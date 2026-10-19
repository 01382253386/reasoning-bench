#!/usr/bin/env python3
"""Run models on the assumption-detection questions and log every reply.

Standard library only. API keys are read from environment variables named in the
config file; they are never written to disk or to the logs.

Usage:
    # offline test with fake models, no keys needed
    python runner/run.py --models config/models.mock.json --runs 2 --out results/mock_raw

    # real run (copy config/models.example.json to config/models.json and edit it first)
    python runner/run.py --models config/models.json --runs 5

    # see what would run without calling any API
    python runner/run.py --models config/models.json --runs 5 --dry-run

Useful options:
    --tier 1|2         only one tier
    --limit N          only the first N items (cheap smoke test)
    --only-model ID    only one model from the config
    --include-private  also run data/private (exists only where you ran the generators)
    --workers N        parallel calls (default 4)
    --prompt-style S   flag (default: model is told to look for problems) or plain (no hint)
    --max-calls N      stop after N new calls per model (respects daily limits; run again tomorrow)
    --skip-missing-keys   skip models whose API key is not set instead of stopping
    --stop-after-errors N give up on a model after N failed calls in a row (default 8)

Results are appended to results/raw/<model id>.jsonl (git-ignored). Re-running resumes:
calls that already succeeded are skipped, failed calls are retried.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoring  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class ApiError(Exception):
    def __init__(self, status, detail):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status


def http_post(url, headers, body, timeout=180):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "reasoning-bench/0.1", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read().decode("utf-8", "replace")[:500])


class RateLimiter:
    """Spaces out call starts so a model stays under its requests-per-minute limit."""

    def __init__(self, rpm):
        self.interval = 60.0 / rpm if rpm else 0.0
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self):
        if not self.interval:
            return
        with self.lock:
            now = time.time()
            start = max(now, self.next)
            self.next = start + self.interval
        time.sleep(max(0.0, start - now))


def with_retries(fn, tries=6):
    delay = 2.0
    for _ in range(tries):
        try:
            return fn()
        except ApiError as e:
            if not (e.status in (408, 409, 429) or e.status >= 500):
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(delay + random.random())
        delay = min(delay * 2, 60)
    return fn()


# --------------------------------------------------------------------------
# Providers. Each returns {"text": str, "model": returned model id, "usage": dict|None}
# --------------------------------------------------------------------------
def call_anthropic(cfg, item):
    body = {"model": cfg["model"], "max_tokens": cfg.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": item["prompt"]}]}
    if cfg.get("temperature") is not None:
        body["temperature"] = cfg["temperature"]
    body.update(cfg.get("extra_body") or {})
    headers = {"x-api-key": os.environ[cfg["api_key_env"]], "anthropic-version": "2023-06-01"}
    r = http_post(cfg.get("base_url", "https://api.anthropic.com/v1").rstrip("/") + "/messages", headers, body)
    text = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
    return {"text": text, "model": r.get("model"), "usage": r.get("usage")}


def call_openai(cfg, item):
    """OpenAI and any OpenAI-compatible server (OpenRouter, Together, Groq, Ollama, vLLM...)."""
    body = {"model": cfg["model"], "messages": [{"role": "user", "content": item["prompt"]}],
            cfg.get("token_param", "max_tokens"): cfg.get("max_tokens", 1024)}
    if cfg.get("temperature") is not None:
        body["temperature"] = cfg["temperature"]
    body.update(cfg.get("extra_body") or {})
    headers = {}
    if cfg.get("api_key_env"):
        headers["Authorization"] = "Bearer " + os.environ[cfg["api_key_env"]]
    url = cfg.get("base_url", "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    r = http_post(url, headers, body)
    return {"text": r["choices"][0]["message"].get("content") or "",
            "model": r.get("model"), "usage": r.get("usage")}


def call_gemini(cfg, item):
    gen = {"maxOutputTokens": cfg.get("max_tokens", 1024)}
    if cfg.get("temperature") is not None:
        gen["temperature"] = cfg["temperature"]
    gen.update(cfg.get("extra_body") or {})
    body = {"contents": [{"parts": [{"text": item["prompt"]}]}], "generationConfig": gen}
    base = cfg.get("base_url", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    r = http_post(f"{base}/models/{cfg['model']}:generateContent",
                  {"x-goog-api-key": os.environ[cfg["api_key_env"]]}, body)
    parts = (r.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return {"text": "".join(p.get("text", "") for p in parts),
            "model": r.get("modelVersion") or cfg["model"], "usage": r.get("usageMetadata")}


def call_mock(cfg, item, run, style="flag"):
    """Fake model with a known behaviour, used to test the pipeline offline."""
    b = cfg.get("behavior", "oracle")
    h = int(hashlib.sha256(f"{cfg['id']}|{item['id']}|{run}".encode()).hexdigest(), 16)
    flaw = item["has_flaw"]
    flag = flaw
    if b == "never_flags":
        flag = False
    elif b == "always_flags":
        flag = True
    elif b == "noisy" and (h % 100) < 25:
        flag = not flaw
    right = item["correct_answer"] if not flaw else None
    if b == "complier":                       # flags correctly but answers anyway
        ans = right if right is not None else "42"
    elif flag:
        ans = None
    else:
        ans = right if right is not None else "42"
    fp = None
    if flag:
        fp = item["flaw_keywords"][0] if flaw else "something seems inconsistent"
    if style == "plain":
        cav = f"This is contradictory: {fp}" if flag else None
        return {"text": json.dumps({"answer": ans, "caveats": cav}), "model": "mock", "usage": None}
    return {"text": json.dumps({"premise_problem": flag, "flawed_premise": fp, "answer": ans}),
            "model": "mock", "usage": None}


PROVIDERS = {"anthropic": call_anthropic, "openai": call_openai, "gemini": call_gemini}


def dispatch(cfg, item, run, style="flag"):
    if cfg["provider"] == "mock":
        return call_mock(cfg, item, run, style)
    return with_retries(lambda: PROVIDERS[cfg["provider"]](cfg, item))


# --------------------------------------------------------------------------
def run_one(cfg, limiter, style, item, run):
    limiter.wait()
    t0 = time.time()
    item = dict(item, prompt=scoring.build_prompt(item, style))
    row = {"model_id": cfg["id"], "provider": cfg["provider"], "model_requested": cfg.get("model"),
           "item_id": item["id"], "run": run, "style": style, "temperature": cfg.get("temperature"),
           "prompt_sha256": hashlib.sha256(item["prompt"].encode("utf-8")).hexdigest(),
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        res = dispatch(cfg, item, run, style)
        row.update(text=res["text"], model_returned=res.get("model"), usage=res.get("usage"), error=None)
    except Exception as e:  # keep going; failed calls are retried on the next run
        row.update(text=None, model_returned=None, usage=None, error=f"{type(e).__name__}: {e}"[:500])
    row["seconds"] = round(time.time() - t0, 2)
    return row


def load_done(path):
    done = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("error") is None:
                    done.add((r["item_id"], r["run"]))
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", required=True, help="JSON config listing the models")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "results" / "raw"))
    ap.add_argument("--tier", type=int, choices=[1, 2])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only-model")
    ap.add_argument("--include-private", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--prompt-style", choices=scoring.STYLES, default="flag")
    ap.add_argument("--skip-missing-keys", action="store_true")
    ap.add_argument("--stop-after-errors", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    models = json.load(open(args.models, encoding="utf-8"))["models"]
    if args.only_model:
        models = [m for m in models if m["id"] == args.only_model]
        if not models:
            sys.exit(f"No model with id {args.only_model!r} in {args.models}")

    data = Path(args.data)
    items = scoring.load_items(scoring.dataset_paths(data, args.include_private))
    if args.tier:
        items = [i for i in items if i.get("tier", 1) == args.tier]
    items.sort(key=lambda i: i["id"])
    if args.limit:
        items = items[: args.limit]
    if not items:
        sys.exit("No questions found. Run the generators first (see README).")

    missing = sorted({(m["id"], m["api_key_env"]) for m in models
                      if m["provider"] != "mock" and m.get("api_key_env") and not os.environ.get(m["api_key_env"])})
    if missing and args.skip_missing_keys:
        for i, e in missing:
            print(f"[{i}] skipped: environment variable {e} is not set")
        skip = {i for i, _ in missing}
        models = [m for m in models if m["id"] not in skip]
        missing = []
        if not models:
            sys.exit("No model has its API key set, so there is nothing to run.")
    if missing and not args.dry_run:
        lines = "\n".join(f"  model {i}: set environment variable {e}" for i, e in missing)
        sys.exit("Missing API keys:\n" + lines +
                 "\nSet each one as an environment variable (or a GitHub Actions secret) first. "
                 "Never paste keys into chat or commit them.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(items)} questions x {args.runs} runs x {len(models)} models")

    for cfg in models:
        path = out / f"{cfg['id']}.jsonl"
        done = load_done(path)
        tasks = [(it, r) for it in items for r in range(1, args.runs + 1) if (it["id"], r) not in done]
        if args.max_calls:
            tasks = tasks[: args.max_calls]
        print(f"[{cfg['id']}] {len(tasks)} calls to make ({len(done)} already done)")
        if args.dry_run or not tasks:
            continue
        limiter = RateLimiter(cfg.get("rpm"))
        n_done = n_err = consec = 0
        chunk = max(args.workers * 4, 8)
        with open(path, "a", encoding="utf-8") as f, cf.ThreadPoolExecutor(args.workers) as ex:
            for i in range(0, len(tasks), chunk):
                for row in ex.map(lambda t: run_one(cfg, limiter, args.prompt_style, *t), tasks[i:i + chunk]):
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    n_done += 1
                    if row["error"] is not None:
                        n_err += 1
                        consec += 1
                        if n_err == 1:
                            print(f"[{cfg['id']}] first error: {row['error']}")
                    else:
                        consec = 0
                    if n_done % 25 == 0 or n_done == len(tasks):
                        print(f"[{cfg['id']}] {n_done}/{len(tasks)} done, {n_err} errors")
                if consec >= args.stop_after_errors:
                    print(f"[{cfg['id']}] stopping: {consec} failed calls in a row (daily limit reached, "
                          "or a setting is wrong). Run the same command again later to resume.")
                    break
        if n_err:
            print(f"[{cfg['id']}] {n_err} calls failed. Run the same command again to retry them.")
    print("Finished. Next: python runner/report.py")


if __name__ == "__main__":
    main()
