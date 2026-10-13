#!/usr/bin/env python3
"""Generator for the assumption-detection track of reasoning-bench.

Every question is built by code, so the answer key is known by construction.
Standard library only (Python 3.8+).

Usage:
    python generators/assumption_detection.py                 # default seed 1234
    python generators/assumption_detection.py --seed 99 --out data

Output (JSON Lines):
    data/public/assumption_detection.jsonl    published dev set
    data/private/assumption_detection.jsonl   held-out set (git-ignored, never upload)

Same seed -> identical output, so the private set can always be regenerated locally.

Versions produced per base item:
    original    the question as generated
    surface     renamed entities, reordered facts, reworded question (same flaw, same answer)
    distractor  original plus 3 irrelevant but plausible sentences
    control     (flawed items only) the repaired twin: same scenario, flaw removed
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

TRACK = "assumption_detection"
YEAR = 2026
DIFFICULTIES = ["easy", "easy", "medium", "hard"]
FLAWED_SUBTYPES = [
    "contradictory_facts",
    "false_presupposition",
    "missing_info",
    "hidden_dependency",
    "impossible_constraint",
]
# (subtype generator, difficulty) pairs used for standalone clean controls
CLEAN_PLAN = [
    ("contradictory_facts", "easy"),
    ("false_presupposition", "medium"),
    ("missing_info", "hard"),
    ("hidden_dependency", "medium"),
]
PRIVATE_FRACTION = 0.3

NAMES = ["Ravi", "Meera", "Arjun", "Sana", "Kabir", "Isha", "Dev", "Nina", "Omar", "Lena",
         "Tara", "Yash", "Priya", "Hugo", "Zoya", "Felix", "Anika", "Samir", "Leila", "Marco"]
ORGS = ["Zentra", "Brightloop", "Kavira", "Nordvale", "Helix Works", "Orbitra", "Pantora",
        "Quillon", "Veltrix", "Marlow Labs", "Sunvane", "Tessaro"]
CITIES = ["Ashford", "Brenton", "Calder", "Dunmore", "Eastvale", "Fairhaven", "Glenrock", "Hollis"]
TEAMS = ["Platform", "Mobile", "Data", "Payments", "Search", "Security"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

DISTRACTORS = [
    "{x} usually has tea with breakfast.",
    "{x} enjoys cycling on weekends.",
    "The office kitchen was repainted last spring.",
    "A new coffee machine was installed in the lobby.",
    "{x}'s desk is next to the window.",
    "The building has a small rooftop garden.",
    "{x} prefers to take the stairs instead of the lift.",
    "The parking area is closed on Sundays.",
]

WRAPPER = (
    "Read the scenario and answer the question.\n\n"
    "Respond with JSON only, in exactly this form:\n"
    '{"premise_problem": true or false, "flawed_premise": "one sentence naming the problem, '
    'or null", "answer": "your answer, or null if the question cannot be answered"}\n\n'
    "Set premise_problem to true if the scenario or the question rests on something false, "
    "contradictory, or missing.\n\n"
    "Scenario: <<SCENARIO>>\n\n"
    "Question: <<QUESTION>>"
)


@dataclass
class View:
    """Surface presentation of a scenario: names, wording, order, extra sentences."""
    names: list
    orgs: list
    cities: list
    teams: list
    variant: int = 0
    shuffle_seed: object = None
    extras: list = field(default_factory=list)


@dataclass
class Spec:
    facts: list              # [(fact_id, text)]
    question: str
    has_flaw: bool
    flaw_fact_ids: list
    flaw_keywords: list
    correct_answer: object   # None when has_flaw
    answer_check: dict
    check_data: dict


def make_view(seed, avoid=None):
    r = random.Random(seed)

    def pick(pool, n, used):
        return r.sample([p for p in pool if p not in used], n)

    a = avoid
    return View(
        names=pick(NAMES, 8, a.names if a else []),
        orgs=pick(ORGS, 5, a.orgs if a else []),
        cities=pick(CITIES, 3, a.cities if a else []),
        teams=pick(TEAMS, 2, a.teams if a else []),
    )


# --------------------------------------------------------------------------
# Subtype 1: contradictory facts (stated age vs birth year, possibly via chain)
# --------------------------------------------------------------------------
def core_age(rng, diff):
    n_chain = {"easy": 0, "medium": 1, "hard": 2}[diff]
    n_extra = {"easy": 0, "medium": 2, "hard": 4}[diff]
    return dict(
        n_chain=n_chain,
        n_extra=n_extra,
        birth0=rng.randint(1982, 2002),
        gaps=[rng.randint(2, 8) for _ in range(n_chain)],
        err=rng.choice([-6, -5, -4, 4, 5, 6, 7]),
        target_year=rng.choice([2030, 2031, 2032, 2035]),
        extra_ages=[rng.randint(21, 58) for _ in range(n_extra)],
    )


def gen_age(c, flawed, v):
    people = v.names[: c["n_chain"] + 1]
    facts = [("f1", f"{people[0]} was born in {c['birth0']}.")]
    ids = ["f1"]
    for i, g in enumerate(c["gaps"]):
        fid = f"f{i + 2}"
        facts.append((fid, f"{people[i + 1]} is {g} years older than {people[i]}."))
        ids.append(fid)
    subject = people[-1]
    birth = c["birth0"] - sum(c["gaps"])
    true_age = YEAR - birth
    stated = true_age + c["err"] if flawed else true_age
    sid = f"f{c['n_chain'] + 2}"
    facts.append((sid, f"{subject} is {stated} years old as of {YEAR}."))
    ids.append(sid)
    others = v.names[c["n_chain"] + 1:]
    for j in range(c["n_extra"]):
        facts.append((f"x{j + 1}", f"{others[j]} is {c['extra_ages'][j]} years old as of {YEAR}."))
    ty = c["target_year"]
    if v.variant == 0:
        q = f"In {ty}, how old will {subject} be at the end of the year?"
    else:
        q = f"What age will {subject} reach by the end of {ty}?"
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=ids if flawed else [],
        flaw_keywords=["age", "born", "birth", "years old", "older", "inconsistent"] if flawed else [],
        correct_answer=None if flawed else ty - birth,
        answer_check={"type": "number"},
        check_data={"year": YEAR, "birth": birth, "stated_age": stated, "target_year": ty},
    )


# --------------------------------------------------------------------------
# Subtype 2: false presupposition (asks about an acquisition that never happened)
# --------------------------------------------------------------------------
def core_acq(rng, diff):
    n_other = {"easy": 0, "medium": 2, "hard": 3}[diff]
    return dict(
        diff=diff,
        n_other=n_other,
        year=rng.randint(2012, 2022),
        month=rng.choice(MONTHS),
        others=[(rng.choice(MONTHS), rng.randint(2010, 2024)) for _ in range(n_other)],
    )


def gen_acq(c, flawed, v):
    org, target = v.orgs[0], v.orgs[1]
    oth = v.orgs[2: 2 + c["n_other"]]
    year, month = c["year"], c["month"]
    facts, ids = [], []
    if c["diff"] == "hard":
        if flawed:
            facts.append(("f1", f"{target} filed its annual report as an independent company in {year + 1}."))
            facts.append(("f2", f"{org}'s completed acquisitions to date are {', '.join(oth)}."))
        else:
            facts.append(("f1", f"{org} acquired {target} in {month} {year}."))
            facts.append(("f2", f"{org}'s completed acquisitions to date are {target}, {', '.join(oth)}."))
        ids = ["f1", "f2"]
    else:
        if flawed:
            facts.append(("f1", f"{org} and {target} held acquisition talks in {year}, but the talks "
                                f"ended without a deal and {target} remains an independent company."))
        else:
            facts.append(("f1", f"{org} acquired {target} in {month} {year}."))
        ids = ["f1"]
    for j, o in enumerate(oth):
        m, y = c["others"][j]
        facts.append((f"x{j + 1}", f"{org} acquired {o} in {m} {y}."))
    if v.variant == 0:
        q = f"In which month did {org} acquire {target}?"
    else:
        q = f"{org} bought {target} in which month?"
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=ids if flawed else [],
        flaw_keywords=["acqui", "independent", "no deal", "talks", "never", "bought", target.lower()] if flawed else [],
        correct_answer=None if flawed else month,
        answer_check={"type": "month"}, check_data={},
    )


# --------------------------------------------------------------------------
# Subtype 3: missing info (train arrival time without the route distance)
# --------------------------------------------------------------------------
def core_missing(rng, diff):
    s2 = rng.choice([50, 60, 75, 100])
    h3 = rng.choice([2, 3, 4])
    return dict(
        diff=diff,
        speed=rng.choice([40, 45, 50, 60, 72, 80, 90]),
        hours=rng.choice([2, 3, 4, 5, 6]),
        start=rng.randint(6, 14),
        s2=s2, d3=s2 * h3, start2=rng.randint(6, 14),
        bus_h=rng.choice([1, 2, 3]), platforms=rng.randint(3, 9),
    )


def gen_missing(c, flawed, v):
    c1, c2, c3 = v.cities
    dist = c["speed"] * c["hours"]
    arrive = c["start"] + c["hours"]
    facts = [("f1", f"A train leaves {c1} at {c['start']:02d}:00 and travels non-stop at "
                    f"{c['speed']} km/h toward {c2}.")]
    if not flawed:
        facts.append(("f2", f"The rail route from {c1} to {c2} is {dist} km long."))
    if c["diff"] in ("medium", "hard"):
        facts.append(("x1", f"A second train leaves {c1} at {c['start2']:02d}:00 and travels at "
                            f"{c['s2']} km/h toward {c3}."))
        facts.append(("x2", f"The rail route from {c1} to {c3} is {c['d3']} km long."))
    if c["diff"] == "hard":
        facts.append(("x3", f"A bus covers the road from {c2} to {c3} in {c['bus_h']} hours."))
        facts.append(("x4", f"{c2} station has {c['platforms']} platforms."))
    if v.variant == 0:
        q = f"At what time does the first train arrive in {c2}?"
    else:
        q = f"When will the train from {c1} reach {c2}?"
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=["MISSING:distance"] if flawed else [],
        flaw_keywords=["distance", "far", "route", "length", "how long", "km"] if flawed else [],
        correct_answer=None if flawed else f"{arrive:02d}:00",
        answer_check={"type": "time"}, check_data={},
    )


# --------------------------------------------------------------------------
# Subtype 4: hidden dependency (question assumes everyone works; a fact says not)
# --------------------------------------------------------------------------
def core_staff(rng, diff):
    k = {"easy": 3, "medium": 4, "hard": 5}[diff]
    n_extra = {"easy": 0, "medium": 2, "hard": 3}[diff]
    return dict(
        diff=diff, k=k, n_extra=n_extra,
        days=rng.choice([5, 10]),
        leave_idx=rng.randrange(k),
        other_size=rng.randint(3, 9),
        hours=rng.choice([6, 7, 8]),
    )


def gen_staff(c, flawed, v):
    team, other = v.teams
    k, d = c["k"], c["days"]
    eng = v.names[:k]
    p = eng[c["leave_idx"]]
    facts = [
        ("f1", f"The {team} team has {k} engineers: {', '.join(eng)}."),
        ("f2", f"A sprint lasts {d} working days."),
    ]
    if c["diff"] == "hard":
        leave = (f"{p} leaves on a trip the day before the sprint starts and returns the day after it ends."
                 if flawed else f"{p} returns from a long trip the day before the sprint starts.")
    else:
        leave = (f"{p} is on leave for the whole of the sprint."
                 if flawed else f"{p} is on leave only in the week after the sprint ends.")
    facts.append(("leave", leave))
    extras = [
        ("x1", f"The {other} team has {c['other_size']} engineers."),
        ("x2", f"Each engineer works {c['hours']} hours a day."),
        ("x3", "The sprint review is held on the last day of the sprint."),
    ]
    facts += extras[: c["n_extra"]]
    if v.variant == 0:
        q = (f"All {k} engineers will work on every day of the sprint. How many engineer-days "
             f"of work will the {team} team deliver in the sprint?")
    else:
        q = (f"Assuming every one of the {k} engineers works on all {d} days, how many "
             f"engineer-days will the {team} team deliver?")
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=["f1", "leave"] if flawed else [],
        flaw_keywords=["leave", "away", "absent", "trip", "unavailable", "vacation", "holiday"] if flawed else [],
        correct_answer=None if flawed else k * d,
        answer_check={"type": "number"}, check_data={},
    )


# --------------------------------------------------------------------------
# Subtype 5: impossible constraint (pick numbers that sum to an unreachable target)
# --------------------------------------------------------------------------
def achievable_sums(numbers, k, repeat):
    combos = (itertools.combinations_with_replacement(numbers, k) if repeat
              else itertools.combinations(numbers, k))
    return {sum(cb) for cb in combos}


def core_constraint(rng, diff):
    if diff == "easy":
        nums = sorted(rng.sample(range(2, 16, 2), 3)); k = 3; repeat = True
    elif diff == "medium":
        nums = sorted(rng.sample(range(1, 10), 4)); k = 3; repeat = True
    else:
        nums = sorted(rng.sample(range(1, 16), 6)); k = 4; repeat = False
    sums = achievable_sums(nums, k, repeat)
    combos = list(itertools.combinations_with_replacement(nums, k) if repeat
                  else itertools.combinations(nums, k))
    solution = list(rng.choice(combos))
    ok_target = sum(solution)
    if diff == "easy":
        bad = rng.choice([t for t in range(k * min(nums), k * max(nums) + 1) if t % 2 == 1])
    elif diff == "medium":
        bad = k * max(nums) + rng.randint(1, 3)
    else:
        top = sum(sorted(nums)[-k:])
        bottom = sum(sorted(nums)[:k])
        bad = top + rng.randint(1, 3) if rng.random() < 0.5 else max(1, bottom - rng.randint(1, 3))
    assert bad not in sums, "flawed target must be unreachable"
    return dict(nums=nums, k=k, repeat=repeat, solution=solution, ok_target=ok_target, bad_target=bad)


def gen_constraint(c, flawed, v):
    target = c["bad_target"] if flawed else c["ok_target"]
    rule = ("the same number may be chosen more than once" if c["repeat"]
            else "each number may be chosen at most once")
    facts = [
        ("f1", f"You are given the numbers {', '.join(map(str, c['nums']))}."),
        ("f2", f"You must choose exactly {c['k']} numbers, and {rule}."),
        ("f3", f"The chosen numbers must add up to exactly {target}."),
    ]
    q = "Which numbers do you choose?" if v.variant == 0 else f"List the {c['k']} numbers you would pick."
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2", "f3"] if flawed else [],
        flaw_keywords=["impossible", "cannot", "can't", "not possible", "no way", "odd", "even",
                       "parity", "exceed", "too large", "too small", "maximum", "minimum",
                       "unreachable"] if flawed else [],
        correct_answer=None if flawed else ", ".join(map(str, c["solution"])),
        answer_check={"type": "sum_pick", "numbers": c["nums"], "k": c["k"],
                      "target": target, "repeat": c["repeat"]},
        check_data={},
    )


GENS = {
    "contradictory_facts": (core_age, gen_age),
    "false_presupposition": (core_acq, gen_acq),
    "missing_info": (core_missing, gen_missing),
    "hidden_dependency": (core_staff, gen_staff),
    "impossible_constraint": (core_constraint, gen_constraint),
}


# --------------------------------------------------------------------------
# Rendering, answer checking, item building
# --------------------------------------------------------------------------
def render(spec, view):
    facts = list(spec.facts)
    if view.shuffle_seed is not None:
        random.Random(view.shuffle_seed).shuffle(facts)
    if view.extras:
        r = random.Random((view.shuffle_seed or 0) + 17)
        for i, text in enumerate(view.extras):
            facts.insert(r.randint(0, len(facts)), (f"d{i + 1}", text))
    scenario = " ".join(t for _, t in facts)
    prompt = WRAPPER.replace("<<SCENARIO>>", scenario).replace("<<QUESTION>>", spec.question)
    return prompt, facts


def pick_distractors(seed, view):
    r = random.Random(seed)
    pool = [n for n in NAMES if n not in view.names]
    sentences = r.sample(DISTRACTORS, 3)
    return [s.replace("{x}", r.choice(pool)) for s in sentences]


def valid_pick(picked, chk):
    if len(picked) != chk["k"] or sum(picked) != chk["target"]:
        return False
    if any(p not in chk["numbers"] for p in picked):
        return False
    return chk["repeat"] or len(set(picked)) == len(picked)


def check_answer(item, answer):
    """Return True/False if the item has a correct answer, None for flawed items.

    Deliberately lenient for 'number' (any number in the text may match); the runner
    asks models for a bare answer in the JSON 'answer' field, which keeps this safe.
    """
    ca = item["correct_answer"]
    if ca is None:
        return None
    if answer is None:
        return False
    s = str(answer)
    t = item["answer_check"]["type"]
    if t == "number":
        return int(ca) in [int(x) for x in re.findall(r"\d+", s)]
    if t == "month":
        return ca.lower() in s.lower()
    if t == "time":
        eh, em = [int(x) for x in ca.split(":")]
        return any((int(h), int(m)) == (eh, em) for h, m in re.findall(r"(\d{1,2}):(\d{2})", s))
    if t == "sum_pick":
        return valid_pick([int(x) for x in re.findall(r"\d+", s)], item["answer_check"])
    raise ValueError(f"unknown answer_check type {t}")


def make_item(base_id, version, subtype, diff, spec, view, split, seed, source=None):
    prompt, facts = render(spec, view)
    item = {
        "id": f"{base_id}-{version}",
        "track": TRACK,
        "base_id": base_id,
        "version": version,
        "subtype": subtype,
        "difficulty": diff,
        "prompt": prompt,
        "question": spec.question,
        "facts": [{"id": i, "text": t} for i, t in facts],
        "has_flaw": spec.has_flaw,
        "flaw_fact_ids": spec.flaw_fact_ids,
        "flaw_keywords": spec.flaw_keywords,
        "correct_answer": spec.correct_answer,
        "answer_check": spec.answer_check,
        "check_data": spec.check_data,
        "split": split,
        "generator": "generators/assumption_detection.py",
        "seed": seed,
    }
    if source:
        item["source_subtype"] = source
    return item


def build_all(seed):
    plan = [(st, d, True) for st in FLAWED_SUBTYPES for d in DIFFICULTIES]
    plan += [(st, d, False) for st, d in CLEAN_PLAN]
    order = list(range(1, len(plan) + 1))
    random.Random(seed).shuffle(order)
    private_ids = set(order[: round(PRIVATE_FRACTION * len(plan))])

    items = []
    for idx, (st, diff, flawed) in enumerate(plan, 1):
        base_id = f"ad-{idx:04d}"
        bseed = seed * 1000 + idx
        core_fn, gen_fn = GENS[st]
        core = core_fn(random.Random(bseed), diff)
        v_orig = make_view(bseed + 1)
        v_alt = make_view(bseed + 2, avoid=v_orig)
        split = "private" if idx in private_ids else "public"
        subtype = st if flawed else "clean_control"
        source = None if flawed else st

        def add(version, spec, view):
            items.append(make_item(base_id, version, subtype, diff, spec, view, split, bseed, source))

        add("original", gen_fn(core, flawed, v_orig), v_orig)
        v_surf = replace(v_alt, variant=1, shuffle_seed=bseed + 3)
        add("surface", gen_fn(core, flawed, v_surf), v_surf)
        v_dist = replace(v_orig, extras=pick_distractors(bseed + 4, v_orig))
        add("distractor", gen_fn(core, flawed, v_dist), v_dist)
        if flawed:
            add("control", gen_fn(core, False, v_orig), v_orig)
    return items


# --------------------------------------------------------------------------
# Self-check: independent re-verification where code can do it
# --------------------------------------------------------------------------
def verify(items):
    ids, prompts, by_base = set(), set(), {}
    for it in items:
        assert it["id"] not in ids, f"duplicate id {it['id']}"
        ids.add(it["id"])
        assert it["prompt"] not in prompts, f"duplicate prompt {it['id']}"
        prompts.add(it["prompt"])
        by_base.setdefault(it["base_id"], []).append(it)
        if it["has_flaw"]:
            assert it["correct_answer"] is None and it["flaw_keywords"] and it["flaw_fact_ids"], it["id"]
        else:
            assert it["correct_answer"] is not None, it["id"]
        chk, cd = it["answer_check"], it["check_data"]
        if chk["type"] == "sum_pick":
            reachable = chk["target"] in achievable_sums(chk["numbers"], chk["k"], chk["repeat"])
            assert reachable == (not it["has_flaw"]), f"constraint mismatch {it['id']}"
            if not it["has_flaw"]:
                assert check_answer(it, it["correct_answer"]) is True, it["id"]
        if "stated_age" in cd:
            consistent = cd["stated_age"] == cd["year"] - cd["birth"]
            assert consistent == (not it["has_flaw"]), f"age mismatch {it['id']}"
            if not it["has_flaw"]:
                assert it["correct_answer"] == cd["target_year"] - cd["birth"], it["id"]
    for base_id, group in by_base.items():
        assert len({g["split"] for g in group}) == 1, f"split differs inside {base_id}"
        versions = {g["version"] for g in group}
        assert {"original", "surface", "distractor"} <= versions, base_id
        orig = next(g for g in group if g["version"] == "original")
        if orig["has_flaw"]:
            assert "control" in versions, f"flawed item {base_id} has no repaired twin"
        for g in group:
            if g["version"] in ("original", "surface", "distractor"):
                assert g["has_flaw"] == orig["has_flaw"], base_id
            if g["version"] == "control":
                assert not g["has_flaw"], base_id


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--out", default=None, help="output folder (default: <repo>/data)")
    args = ap.parse_args()

    out = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data"
    items = build_all(args.seed)
    verify(items)

    for split in ("public", "private"):
        folder = out / split
        folder.mkdir(parents=True, exist_ok=True)
        rows = [it for it in items if it["split"] == split]
        path = folder / f"{TRACK}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for it in rows:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        bases = len({it["base_id"] for it in rows})
        print(f"{split:8s} {len(rows):3d} items from {bases:2d} base questions -> {path}")
    print(f"total {len(items)} items; all self-checks passed")


if __name__ == "__main__":
    main()
