#!/usr/bin/env python3
"""Scoring for the assumption-detection track (standard library only).

A model is asked to answer in JSON:
    {"premise_problem": true/false, "flawed_premise": "...", "answer": "..."}

This module parses that reply and scores it against the item's answer key.
Used by run.py (progress) and report.py (final tables), so there is one source of truth.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
import assumption_detection as tier1  # noqa: E402
import assumption_detection_domain as tier2  # noqa: E402

STYLES = ("flag", "plain")

# "plain" prompt: the model is NOT told to look for problems. It only gets an optional
# free-text slot for caveats, like a normal assistant reply. This measures whether it
# volunteers a problem, which is what happens in real use.
PLAIN_WRAPPER = (
    "Read the scenario and answer the question.\n\n"
    "Respond with JSON only, in exactly this form:\n"
    '{"answer": "your answer", "caveats": "anything the reader should know before relying '
    'on this answer, or null"}\n\n'
    "Scenario: <<SCENARIO>>\n\n"
    "Question: <<QUESTION>>"
)

# Strict wording that signals a flagged problem in the caveats (approximate by design).
FLAG_RE = re.compile(
    r"contradict|inconsisten|conflict|impossible|not possible|cannot|can't|can not|unable to|"
    r"insufficient|not enough|missing|not (been )?(given|provided|stated|specified|mentioned)|"
    r"no information|unknown|unclear|ambiguous|add up|mismatch|incompatible|invalid|incorrect|"
    r"\bfalse\b|no such|never |does not (say|state|specify|include)|doesn't (say|state|specify|include)",
    re.I)

NO_CAVEAT = {"", "null", "none", "n/a", "na", "no", "no caveats", "nothing", "-"}


def build_prompt(item, style="flag"):
    """The prompt a model sees. 'flag' is the stored prompt; 'plain' rebuilds it without the hint."""
    if style == "flag":
        return item["prompt"]
    if style != "plain":
        raise ValueError(f"unknown prompt style {style}")
    scenario = " ".join(f["text"] for f in item["facts"])
    return PLAIN_WRAPPER.replace("<<SCENARIO>>", scenario).replace("<<QUESTION>>", item["question"])


NO_ANSWER = {"", "null", "none", "n/a", "na", "no answer", "cannot be answered",
             "unanswerable", "not answerable"}


# The official question files. Anything else lying in data/ is ignored on purpose.
DATASETS = ["assumption_detection.jsonl", "assumption_detection_domain.jsonl"]


def dataset_paths(data_dir, include_private=True):
    data_dir = Path(data_dir)
    splits = ["public"] + (["private"] if include_private else [])
    return [data_dir / s / n for s in splits for n in DATASETS if (data_dir / s / n).exists()]


def load_items(paths):
    items = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    return items


def parse_response(text):
    """Find the first JSON object containing 'premise_problem'. Returns a dict or None."""
    if not text:
        return None
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and "premise_problem" in obj:
            pp = obj["premise_problem"]
            if isinstance(pp, str):
                pp = pp.strip().lower() in ("true", "yes", "1")
            return {"premise_problem": bool(pp),
                    "flawed_premise": obj.get("flawed_premise"),
                    "answer": obj.get("answer")}
    return None


def parse_for(item, text, style="flag"):
    """Parse a reply into the common form {premise_problem, flawed_premise, answer}."""
    if style == "flag":
        return parse_response(text)
    if not text:
        return None
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and "answer" in obj:
            ans = obj.get("answer")
            cav = obj.get("caveats")
            cav = None if cav is None else str(cav).strip()
            if cav is not None and cav.lower().strip(" .") in NO_CAVEAT:
                cav = None
            unanswered = normalize_answer(ans) is None
            flagged = unanswered or bool(cav and FLAG_RE.search(cav))
            return {"premise_problem": flagged,
                    "flawed_premise": cav or (str(ans) if unanswered and ans else None),
                    "answer": ans}
    return None


def normalize_answer(a):
    if a is None:
        return None
    if isinstance(a, (list, tuple)):
        a = ", ".join(str(x) for x in a)
    s = str(a).strip()
    return None if s.lower() in NO_ANSWER else s


def _checker(item):
    return tier2.check_answer if item.get("tier") == 2 else tier1.check_answer


def score(item, parsed):
    """Score one reply. Fields that do not apply to the item type are None."""
    flaw = item["has_flaw"]
    res = {"parsed": parsed is not None, "flagged": None, "detect_ok": False,
           "id_ok": None, "complied": None, "answer_ok": None,
           "false_alarm": None, "missed": None}
    if parsed is None:                       # unparseable reply counts as wrong
        if flaw:
            res.update(id_ok=False, missed=True)
        else:
            res.update(answer_ok=False)
        return res
    flagged = bool(parsed["premise_problem"])
    ans = normalize_answer(parsed.get("answer"))
    res["flagged"] = flagged
    res["detect_ok"] = flagged == flaw
    if flaw:
        fp = str(parsed.get("flawed_premise") or "").lower()
        res["missed"] = not flagged
        # keyword match is an approximation of "named the right problem"
        res["id_ok"] = flagged and any(k.lower() in fp for k in item["flaw_keywords"])
        res["complied"] = (ans is not None) if flagged else None
    else:
        res["false_alarm"] = flagged
        res["answer_ok"] = bool(ans is not None and _checker(item)(item, ans))
    return res
