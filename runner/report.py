#!/usr/bin/env python3
"""Turn raw run logs into summary tables (standard library only).

Usage:
    python runner/report.py                      # reads results/raw, writes results/
    python runner/report.py --raw results/mock_raw --out results/mock_report

Writes:
    summary.md    headline tables (commit this)
    failures.md   concrete failure examples for the README / LinkedIn (commit this)
    scores.csv    one row per call, for your own analysis

All proportions come with 95% Wilson confidence intervals. Question counts are small,
so the intervals are wide; read them before reading the point estimates.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoring  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VERSIONS = ["original", "surface", "distractor"]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def fmt(k, n):
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.0f}% [{100 * lo:.0f}-{100 * hi:.0f}]"


def count(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    return sum(1 for v in vals if v), len(vals)


def balanced(rows):
    fl = [r for r in rows if r["has_flaw"]]
    cl = [r for r in rows if not r["has_flaw"]]
    parts = [sum(r["detect_ok"] for r in g) / len(g) for g in (fl, cl) if g]
    return sum(parts) / len(parts) if parts else None


def tokens_of(u):
    if not isinstance(u, dict):
        return None
    for k in ("total_tokens", "totalTokenCount"):
        if isinstance(u.get(k), (int, float)):
            return u[k]
    a, b = u.get("input_tokens"), u.get("output_tokens")
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b
    return None


def avg(vals, digits=0):
    vals = [v for v in vals if v is not None]
    return "n/a" if not vals else f"{sum(vals) / len(vals):.{digits}f}"


def pct(x):
    return "n/a" if x is None else f"{100 * x:.0f}%"


def gap(a, b):
    return "n/a" if a is None or b is None else f"{100 * (a - b):+.0f} pts"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def scenario(item):
    return item["prompt"].split("Scenario: ", 1)[1].replace("\n\nQuestion:", "\n\nQuestion:")


def load(raw_dir, data_dir):
    items = {i["id"]: i for i in scoring.load_items(scoring.dataset_paths(data_dir))}
    rows, errors, unknown = [], defaultdict(int), 0
    for f in sorted(Path(raw_dir).glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("error") is not None:
                    errors[r["model_id"]] += 1
                    continue
                it = items.get(r["item_id"])
                if it is None:
                    unknown += 1
                    continue
                s = scoring.score(it, scoring.parse_response(r["text"]))
                rows.append({"model": r["model_id"], "model_returned": r.get("model_returned"),
                             "item_id": it["id"], "base_id": it["base_id"], "run": r["run"],
                             "tier": it.get("tier", 1), "domain": it.get("domain", "abstract"),
                             "subtype": it["subtype"], "difficulty": it["difficulty"],
                             "version": it["version"], "has_flaw": it["has_flaw"],
                             "text": r["text"], "usage": r.get("usage"), "seconds": r.get("seconds"),
                             "item": it, **s})
    return rows, errors, unknown


def build_summary(rows, errors):
    models = sorted({r["model"] for r in rows})
    L = ["# Results summary\n",
         f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
         "Proportions show a 95% Wilson interval in brackets; question counts are small, so intervals are wide.\n",
         "Definitions: **sensitivity** = flagged a problem when there was one. **specificity** = did not "
         "flag when there was none. **balanced** = mean of the two. **gap** = balanced score on original "
         "questions minus balanced score on the perturbed version. **repaired twin** = same scenario with "
         "the flaw fixed. **complied anyway** = flagged the problem but still gave a confident answer. "
         "**named it** = the flagged problem matches the planted one (keyword match, approximate).\n"]

    # 1 headline
    head = []
    for m in models:
        R = [r for r in rows if r["model"] == m]
        by_v = {v: [r for r in R if r["version"] == v] for v in VERSIONS + ["control"]}
        bal = {v: balanced(by_v[v]) for v in VERSIONS}
        runs = sorted({r["run"] for r in R})
        head.append([m, len(R), errors.get(m, 0), pct(sum(r["parsed"] for r in R) / len(R)),
                     fmt(*count([r for r in by_v["original"] if r["has_flaw"]], "detect_ok")),
                     fmt(*count([r for r in by_v["original"] if not r["has_flaw"]], "detect_ok")),
                     pct(bal["original"]), pct(bal["surface"]), pct(bal["distractor"]),
                     gap(bal["original"], bal["surface"]), gap(bal["original"], bal["distractor"]),
                     fmt(*count(by_v["control"], "detect_ok")),
                     avg([tokens_of(r["usage"]) for r in R]), avg([r["seconds"] for r in R], 1),
                     len(runs)])
    L += ["## Headline\n",
          md_table(["model", "calls", "failed calls", "valid replies", "sensitivity (original)",
                    "specificity (original)", "balanced original", "balanced surface", "balanced distractor",
                    "gap surface", "gap distractor", "repaired twins correct", "tokens per call", "seconds per call", "runs"], head), ""]

    # 2 how the model fails
    fails = []
    for m in models:
        F = [r for r in rows if r["model"] == m and r["has_flaw"]]
        flagged = [r for r in F if r["flagged"]]
        C = [r for r in rows if r["model"] == m and not r["has_flaw"]]
        fails.append([m, fmt(len(F) - len(flagged), len(F)),
                      fmt(sum(1 for r in flagged if r["complied"]), len(flagged)),
                      fmt(sum(1 for r in flagged if r["id_ok"]), len(flagged)),
                      fmt(sum(1 for r in C if r["false_alarm"]), len(C)),
                      fmt(*count(C, "answer_ok"))])
    L += ["## How the models fail (all versions)\n",
          md_table(["model", "missed the flaw", "complied anyway", "named it", "false alarms on clean",
                    "clean answers correct"], fails), ""]

    # 3 consistency
    cons = []
    for m in models:
        R = [r for r in rows if r["model"] == m]
        per_item = defaultdict(list)
        per_run = defaultdict(list)
        for r in R:
            per_item[r["item_id"]].append(r["detect_ok"])
            per_run[r["run"]].append(r["detect_ok"])
        multi = [v for v in per_item.values() if len(v) > 1]
        accs = [sum(v) / len(v) for v in per_run.values()]
        cons.append([m, len(accs),
                     f"{100 * statistics.mean(accs):.1f}% ± {100 * (statistics.pstdev(accs) if len(accs) > 1 else 0):.1f}",
                     fmt(sum(1 for v in multi if len(set(v)) == 1), len(multi))])
    L += ["## Run-to-run consistency\n",
          md_table(["model", "runs", "accuracy per run (mean ± std)", "questions answered the same way in every run"], cons), ""]

    # 4 by tier / domain / subtype (sensitivity, specificity)
    def slice_table(title, keyfn, label):
        keys = sorted({keyfn(r) for r in rows})
        out = []
        for m in models:
            for k in keys:
                S = [r for r in rows if r["model"] == m and keyfn(r) == k]
                if not S:
                    continue
                fl = [r for r in S if r["has_flaw"]]
                cl = [r for r in S if not r["has_flaw"]]
                out.append([m, k, fmt(*count(fl, "detect_ok")) if fl else "n/a",
                            fmt(*count(cl, "detect_ok")) if cl else "n/a"])
        return [f"## {title}\n", md_table(["model", label, "sensitivity", "specificity"], out), ""]

    L += slice_table("By tier", lambda r: f"tier {r['tier']}", "tier")
    L += slice_table("By domain", lambda r: r["domain"], "domain")
    L += slice_table("By flaw type (flawed items only counted for sensitivity)",
                     lambda r: r["subtype"], "flaw type")
    L += ["## Notes and limitations\n",
          "- Sensitivity and specificity use code-checked labels, so they do not depend on opinion.",
          "- \"Named it\" is a keyword match and only approximates whether the model identified the right problem.",
          "- Question counts per cell are small; treat differences inside the intervals as noise.",
          "- Scores depend on the prompt format. The exact prompts and replies are in the raw logs "
          "(kept local) and the question files.", ""]
    return "\n".join(L)


def build_failures(rows):
    models = sorted({r["model"] for r in rows})
    L = ["# Failure examples\n",
         "Concrete cases taken from the logs. Replies are shortened to 400 characters.\n"]
    for m in models:
        R = [r for r in rows if r["model"] == m]
        L.append(f"## {m}\n")

        # robustness flips: caught in the original, missed once perturbed
        rate = defaultdict(list)
        for r in R:
            if r["has_flaw"] and r["version"] in VERSIONS:
                rate[(r["base_id"], r["version"])].append(r["detect_ok"])
        flips = []
        for b in sorted({k[0] for k in rate}):
            o = rate.get((b, "original"))
            if not o:
                continue
            for v in ("surface", "distractor"):
                p = rate.get((b, v))
                if p:
                    d = sum(o) / len(o) - sum(p) / len(p)
                    if d >= 0.6:
                        flips.append((d, b, v))
        flips.sort(key=lambda t: (-t[0], t[1], t[2]))
        L.append("### Caught the original, missed the perturbed version\n")
        if not flips:
            L.append("None found.\n")
        for d, b, v in flips[:3]:
            orig = next(r for r in R if r["base_id"] == b and r["version"] == "original")
            pert = next((r for r in R if r["base_id"] == b and r["version"] == v and not r["detect_ok"]), None)
            if pert is None:
                continue
            L.append(f"**{b}** ({orig['domain']}, {orig['subtype']}), perturbation: {v}\n")
            L.append("Original question:\n\n> " + scenario(orig["item"]).replace("\n", "\n> ") + "\n")
            L.append("Perturbed question:\n\n> " + scenario(pert["item"]).replace("\n", "\n> ") + "\n")
            L.append(f"Model reply to the perturbed version:\n\n```\n{(pert['text'] or '')[:400]}\n```\n")

        # misses on original versions, worst first
        miss = defaultdict(list)
        for r in R:
            if r["has_flaw"] and r["version"] == "original":
                miss[r["item_id"]].append(r)
        worst = sorted(miss.values(), key=lambda g: (sum(x["detect_ok"] for x in g) / len(g), g[0]["item_id"]))
        L.append("### Flaws the model most often missed (original versions)\n")
        shown = 0
        for g in worst:
            if sum(x["detect_ok"] for x in g) == len(g):
                break
            ex = next(x for x in g if not x["detect_ok"])
            planted = [f["text"] for f in ex["item"]["facts"] if f["id"] in ex["item"]["flaw_fact_ids"]]
            L.append(f"**{ex['item_id']}** ({ex['domain']}, {ex['subtype']}), caught in "
                     f"{sum(x['detect_ok'] for x in g)}/{len(g)} runs\n")
            L.append("> " + scenario(ex["item"]).replace("\n", "\n> ") + "\n")
            L.append("Planted flaw: " + (" / ".join(planted) if planted else "a required fact is missing") + "\n")
            L.append(f"Reply:\n\n```\n{(ex['text'] or '')[:400]}\n```\n")
            shown += 1
            if shown == 5:
                break
        if shown == 0:
            L.append("None: every flaw was caught in every run.\n")

        # false alarms
        fa = sorted((r for r in R if r["false_alarm"]), key=lambda r: r["item_id"])
        L.append("### False alarms on clean questions\n")
        if not fa:
            L.append("None.\n")
        for ex in fa[:3]:
            L.append(f"**{ex['item_id']}** ({ex['domain']}, {ex['version']})\n")
            L.append("> " + scenario(ex["item"]).replace("\n", "\n> ") + "\n")
            L.append(f"Reply:\n\n```\n{(ex['text'] or '')[:400]}\n```\n")
    return "\n".join(L)


def write_csv(rows, path):
    cols = ["model", "item_id", "base_id", "run", "tier", "domain", "subtype", "difficulty", "version",
            "has_flaw", "parsed", "flagged", "detect_ok", "id_ok", "complied", "answer_ok"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(ROOT / "results" / "raw"))
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    rows, errors, unknown = load(args.raw, Path(args.data))
    if not rows:
        sys.exit(f"No scored replies found in {args.raw}. Run runner/run.py first.")
    if unknown:
        print(f"Warning: {unknown} log rows reference questions not found in {args.data} "
              "(private questions are only available where you ran the generators).")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(build_summary(rows, errors), encoding="utf-8")
    (out / "failures.md").write_text(build_failures(rows), encoding="utf-8")
    write_csv(rows, out / "scores.csv")
    print(f"Wrote {out / 'summary.md'}, {out / 'failures.md'}, {out / 'scores.csv'} "
          f"({len(rows)} scored replies, {len({r['model'] for r in rows})} models)")


if __name__ == "__main__":
    main()
