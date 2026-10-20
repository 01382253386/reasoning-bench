#!/usr/bin/env python3
"""Second-opinion scoring: a judge model reads each reply and the planted flaw.

Usage:
    python runner/judge.py --raw results/raw/plain/groq-gpt-oss-120b.jsonl

Needs GROQ_API_KEY (default judge: openai/gpt-oss-20b on Groq, a different model from the one
being tested). Output: <raw>.judged.jsonl, resumable, plus a table by group.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run  # noqa: E402
import scoring  # noqa: E402

FLAWED = """A test question contained a hidden problem.
Hidden problem ({subtype}): {planted}

Scenario: {scenario}
Question: {question}

An AI replied:
{reply}

Does the reply explicitly point out THIS specific problem (for example by saying the premise is
wrong, the numbers do not work, or the needed information is missing)? A generic hedge, or a note
about something else, does not count. Answer with JSON only: {{"names_the_flaw": true or false}}"""

CLEAN = """Here is a scenario and question. The scenario is consistent and has everything needed.

Scenario: {scenario}
Question: {question}

An AI replied:
{reply}

Does the reply claim the scenario contains a contradiction, a false assumption, or missing
information that makes the question wrong or unanswerable as posed? Ordinary clarifying notes
(for example 'assuming X') do not count. Answer with JSON only: {{"claims_problem": true or false}}"""


def reply_text(raw):
    try:
        i = raw.index("{")
        obj = json.JSONDecoder().raw_decode(raw[i:])[0]
        return "answer: %s | caveats: %s" % (obj.get("answer"), obj.get("caveats"))
    except Exception:
        return raw[:600]


def ask(cfg, prompt):
    res = run.with_retries(lambda: run.call_openai(cfg, {"prompt": prompt}))
    t = res["text"]
    try:
        obj = json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
        return bool(obj.get("names_the_flaw", obj.get("claims_problem")))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--judge-model", default="openai/gpt-oss-20b")
    ap.add_argument("--data", default="data")
    a = ap.parse_args()
    cfg = {"id": "judge", "model": a.judge_model, "base_url": "https://api.groq.com/openai/v1",
           "api_key_env": "GROQ_API_KEY", "max_tokens": 1500, "temperature": 0,
           "extra_body": {"reasoning_effort": "low"}}
    items = {i["id"]: i for i in scoring.load_items(scoring.dataset_paths(a.data))}
    out = Path(a.raw + ".judged.jsonl")
    done = {}
    if out.exists():
        for line in open(out):
            r = json.loads(line)
            done[(r["item_id"], r["run"])] = r
    limiter = run.RateLimiter(20)
    with open(out, "a") as f:
        for line in open(a.raw):
            r = json.loads(line)
            key = (r["item_id"], r["run"])
            if key in done or not r.get("text"):
                continue
            it = items[r["item_id"]]
            scen = " ".join(x["text"] for x in it["facts"])
            planted = " / ".join(x["text"] for x in it["facts"] if x["id"] in it["flaw_fact_ids"]) \
                or "a fact needed to answer is missing from the scenario"
            tpl = FLAWED if it["has_flaw"] else CLEAN
            p = tpl.format(subtype=it["subtype"], planted=planted, scenario=scen,
                           question=it["question"], reply=reply_text(r["text"]))
            limiter.wait()
            try:
                v = ask(cfg, p)
            except Exception as e:
                print("error:", str(e)[:120])
                continue
            rec = {"item_id": r["item_id"], "run": r["run"], "judge": v}
            done[key] = rec
            f.write(json.dumps(rec) + "\n")
            f.flush()
    tab = collections.defaultdict(lambda: [0, 0, 0])
    for (iid, _), r in done.items():
        it = items[iid]
        g = "clean (false alarms)" if not it["has_flaw"] else (
            "flawed " + it["domain"] if it.get("tier") == 2 else "flawed tier1")
        if r["judge"] is None:
            tab[g][2] += 1
            continue
        tab[g][0] += 1
        tab[g][1] += bool(r["judge"])
    print("%-28s %5s %9s %8s" % ("group", "n", "flagged", "unclear"))
    for g, (n, k, u) in sorted(tab.items()):
        print("%-28s %5d %8.0f%% %8d" % (g, n, 100 * k / max(n, 1), u))


if __name__ == "__main__":
    main()
