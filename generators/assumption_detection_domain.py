#!/usr/bin/env python3
"""Tier-2 generator for the assumption-detection track: realistic business scenarios.

Same machinery as tier 1 (generators/assumption_detection.py): every question is built by
code, the planted flaw is known by construction, every flawed item has a repaired twin, and
every item comes in original / surface / distractor versions. Only the scenarios differ:
instead of abstract puzzles they read like HR, finance, project-planning and compliance
documents.

Standard library only (Python 3.8+). Needs generators/assumption_detection.py next to it.

Usage:
    python generators/assumption_detection_domain.py
    python generators/assumption_detection_domain.py --seed 99 --out data

Output (JSON Lines):
    data/public/assumption_detection_domain.jsonl
    data/private/assumption_detection_domain.jsonl   (git-ignored, never upload)

Same seed -> identical output.

Scope note: these scenarios test whether a model notices inconsistencies in business
documents and plans. They deliberately do NOT involve judging candidates or people.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assumption_detection as base  # noqa: E402
import assumption_detection_domain_b as batch_b  # noqa: E402
from assumption_detection import (  # noqa: E402
    MONTHS, Spec, View, make_item, make_view, pick_distractors,
)

TRACK = base.TRACK
TIER = 2
GEN_PATH = "generators/assumption_detection_domain.py"
PRIVATE_FRACTION = 0.3
N_EXTRA = {"easy": 0, "medium": 2, "hard": 4}
TASKS = ["the API migration", "the data clean-up", "the payment integration",
         "the dashboard rebuild", "the security audit", "the search upgrade",
         "the mobile release", "the reporting overhaul"]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def usd(n):
    return f"${n:,}"


def cap(s):
    return s[0].upper() + s[1:]


def extras_for(texts, diff):
    return [(f"x{i + 1}", t) for i, t in enumerate(texts[: N_EXTRA[diff]])]


def parse_nums(s):
    return [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", s)]


def emi(P, rate, n):
    i = rate / 1200
    f = (1 + i) ** n
    return round(P * i * f / (f - 1))


@dataclass
class DView(View):
    """View plus task names, so the surface version can rename tasks too."""
    tasks: list = field(default_factory=list)


def make_dview(seed, avoid=None):
    v = make_view(seed, avoid)
    used = avoid.tasks if avoid else []
    tasks = random.Random(seed + 99).sample([t for t in TASKS if t not in used], 3)
    return DView(names=v.names, orgs=v.orgs, cities=v.cities, teams=v.teams, tasks=tasks)


# --------------------------------------------------------------------------
# HR operations 1: hiring plan vs approved budget  (impossible_constraint)
# --------------------------------------------------------------------------
def core_hiring(rng, diff):
    n = rng.randint(4, 8)
    r = rng.choice([1, 2])
    months = -(-n // r)
    return dict(
        diff=diff, n=n, r=r, months=months,
        m0=rng.randint(1, 12 - months + 1),
        b_bad=max(1, n - rng.randint(1, 3)),
        b_ok=n + rng.randint(0, 3),
        k=rng.randint(2, 5), w=rng.choice([2, 3, 4]), e=rng.choice([80, 120, 200, 350]),
    )


def gen_hiring(c, flawed, v):
    org, team = v.orgs[0], v.teams[0]
    n, r = c["n"], c["r"]
    b = c["b_bad"] if flawed else c["b_ok"]
    start = MONTHS[c["m0"] - 1]
    end = MONTHS[c["m0"] - 1 + c["months"] - 1]
    facts = [
        ("f1", f"{org}'s {team} team plans to hire {n} engineers."),
        ("f2", f"The recruiter closes {r} {'hire' if r == 1 else 'hires'} per month, starting in "
               f"{start}, and each hire starts work in the month the offer is closed."),
        ("f3", f"The approved hiring budget for the {team} team covers {b} hires."),
    ]
    extras = [
        f"{org} has {c['e']} employees in total.",
        f"{c['k']} engineers sit on each interview panel.",
        f"Each new engineer completes a {c['w']}-week onboarding programme.",
        "Interviews are held on Tuesdays and Thursdays.",
    ]
    facts += extras_for(extras, c["diff"])
    q = (f"In which month will all {n} engineers have started work?" if v.variant == 0
         else f"By which month will the {team} team have all {n} new engineers in place?")
    return Spec(
        facts=facts, question=q, has_flaw=flawed,
        flaw_fact_ids=["f1", "f3"] if flawed else [],
        flaw_keywords=["budget", "fund", "afford", "cover", "only", "cannot", "insufficient",
                       "not enough", "short"] if flawed else [],
        correct_answer=None if flawed else end,
        answer_check={"type": "month"},
        check_data={"template": "hiring_budget", "n": n, "b": b, "r": r, "m0": c["m0"]},
    )


# --------------------------------------------------------------------------
# HR operations 2: leave entitlement  (false_presupposition)
# --------------------------------------------------------------------------
def core_leave(rng, diff):
    thr = rng.choice([2, 3])
    return dict(
        diff=diff, thr=thr,
        high=rng.choice([20, 22, 24]), low=rng.choice([10, 12, 14]),
        used=rng.randint(3, 9),
        y_ok=rng.randint(2026 - thr - 4, 2026 - thr),
        y_bad=rng.randint(2026 - thr + 1, 2025),
        used2=rng.randint(2, 9), y2=rng.randint(2015, 2020),
    )


def gen_leave(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    thr, high, low, used = c["thr"], c["high"], c["low"], c["used"]
    y = c["y_bad"] if flawed else c["y_ok"]
    facts = [
        ("f1", f"Under {org}'s leave policy, employees with at least {thr} completed years of service "
               f"on 1 January 2026 receive {high} days of annual leave in 2026; all other employees "
               f"receive {low} days."),
        ("f2", f"{p} joined {org} on 1 January {y}."),
        ("f3", f"{p} has taken {used} days of annual leave so far in 2026."),
    ]
    extras = [
        f"{q} joined {org} on 1 January {c['y2']} and has taken {c['used2']} days of annual leave so far in 2026.",
        "The leave year runs from 1 January to 31 December.",
        "Public holidays do not count against annual leave.",
        "Unused leave cannot be carried over to 2027.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many of {p}'s {high} annual leave days for 2026 remain?" if v.variant == 0
             else f"{p} is entitled to {high} days of annual leave in 2026. How many are still unused?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["entitle", "eligible", "service", "only", "policy", str(low),
                       "completed years", "not qualify"] if flawed else [],
        correct_answer=None if flawed else high - used,
        answer_check={"type": "number"},
        check_data={"template": "leave_entitlement", "y": y, "thr": thr, "high": high,
                    "low": low, "used": used},
    )


# --------------------------------------------------------------------------
# Finance 1: stated loan instalment does not match the loan terms  (contradictory_facts)
# --------------------------------------------------------------------------
def core_emi(rng, diff):
    return dict(
        diff=diff,
        P=rng.choice([300000, 500000, 800000, 1000000]),
        rate=rng.choice([8, 9, 10, 12]),
        n=rng.choice([24, 36, 48, 60]),
        factor=rng.choice([0.6, 0.7, 1.3, 1.4]),
        P2=rng.choice([150000, 250000, 400000]),
        rate2=rng.choice([7, 11]),
        n2=rng.choice([12, 24, 36]),
    )


def gen_emi(c, flawed, v):
    org, q, city = v.orgs[0], v.names[1], v.cities[0]
    P, rate, n = c["P"], c["rate"], c["n"]
    true = emi(P, rate, n)
    stated = round(true * c["factor"]) if flawed else true
    loan = usd(P)
    facts = [
        ("f1", f"{org} takes a loan of {loan} at {rate}% annual interest, to be repaid in {n} equal "
               f"monthly instalments (interest is charged monthly on the reducing balance)."),
        ("f2", f"The monthly instalment on {org}'s {loan} loan is {usd(stated)}."),
    ]
    extras = [
        f"{org} also has a separate {usd(c['P2'])} loan at {c['rate2']}% annual interest, repaid in "
        f"{c['n2']} equal monthly instalments of {usd(emi(c['P2'], c['rate2'], c['n2']))}.",
        f"The {loan} loan agreement was signed at the {city} branch.",
        f"The first instalment on the {loan} loan is due on the 5th of the month after disbursement.",
        f"{q} is the loan officer for the {loan} loan.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"Based on these figures, what is the total interest {org} pays over the life of the {loan} loan?"
             if v.variant == 0
             else f"What is the total interest that {org} will have paid by the end of the {loan} loan?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["instalment", "installment", "emi", "does not match", "inconsistent",
                       "incorrect", "calculat", "too low", "too high", "monthly payment"] if flawed else [],
        correct_answer=None if flawed else stated * n - P,
        answer_check={"type": "number", "tol_pct": 1},
        check_data={"template": "loan_instalment", "P": P, "rate": rate, "n": n,
                    "stated": stated, "true": true},
    )


# --------------------------------------------------------------------------
# Finance 2: loan with no interest rate given  (missing_info)
# --------------------------------------------------------------------------
def core_rate(rng, diff):
    return dict(
        diff=diff,
        P=rng.choice([100000, 150000, 200000, 250000, 300000, 400000, 500000]),
        t=rng.choice([2, 3, 4, 5]), r=rng.choice([6, 8, 9, 10, 12]),
        D=rng.choice([100000, 200000, 300000]), rd=rng.choice([4, 5, 6]),
        mo=rng.randint(1, 12), yr=rng.randint(2022, 2025), k=rng.randint(3, 12),
    )


def gen_rate(c, flawed, v):
    org, q, city = v.orgs[0], v.names[1], v.cities[0]
    P, t, r = c["P"], c["t"], c["r"]
    loan = usd(P)
    rate_txt = "at the bank's prevailing rate" if flawed else f"at {r}% per year"
    facts = [
        ("f1", f"{org} borrowed {loan} from the bank for {t} years, repayable in a single payment "
               f"at the end of the term."),
        ("f2", f"Interest on {org}'s {loan} loan is charged as simple interest {rate_txt}."),
    ]
    extras = [
        f"{org} also holds a {usd(c['D'])} fixed deposit at the same bank, earning {c['rd']}% simple interest per year.",
        f"The {loan} loan was disbursed in {MONTHS[c['mo'] - 1]} {c['yr']}.",
        f"{q} is the relationship manager for the {loan} loan.",
        f"The bank has {c['k']} branches in {city}.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What total amount must {org} repay at the end of the term of the {loan} loan?"
             if v.variant == 0
             else f"How much will {org} have to pay back in total when the {loan} loan matures?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["MISSING:interest_rate"] if flawed else [],
        flaw_keywords=["rate", "percent", "%", "prevailing", "not given", "not specified",
                       "unknown", "missing"] if flawed else [],
        correct_answer=None if flawed else P + P * r * t // 100,
        answer_check={"type": "number"},
        check_data={"template": "loan_rate", "P": P, "t": t, "r": None if flawed else r,
                    "rate_missing": flawed},
    )


# --------------------------------------------------------------------------
# Project planning 1: two concurrent tasks need more engineers than exist  (impossible_constraint)
# --------------------------------------------------------------------------
def core_resource(rng, diff):
    tot = rng.randint(4, 8)
    a = rng.randint(2, tot - 1)
    return dict(
        diff=diff, tot=tot, a=a,
        b_bad=tot - a + rng.randint(1, 2),
        b_ok=rng.randint(1, tot - a),
        d=rng.randint(3, 12),
    )


def gen_resource(c, flawed, v):
    team = v.teams[0]
    t1, t2, t3 = v.tasks
    tot, a, d = c["tot"], c["a"], c["d"]
    b = c["b_bad"] if flawed else c["b_ok"]
    facts = [
        ("f1", f"The {team} team has {tot} engineers."),
        ("f2", f"{cap(t1)} needs {a} {'engineer' if a == 1 else 'engineers'} and {t2} needs {b} "
               f"{'engineer' if b == 1 else 'engineers'}, each working full-time on that task."),
        ("f3", f"{cap(t1)} and {t2} must run at the same time for {d} working days."),
    ]
    extras = [
        f"{cap(t3)} is scheduled to start after {t1} and {t2} are finished.",
        "The team works Monday to Friday.",
        "A code freeze starts the week after both tasks end.",
        f"All {tot} engineers have completed the security training.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"In total, how many engineer-days do {t1} and {t2} use during that period?"
             if v.variant == 0
             else f"How many engineer-days will {t1} and {t2} consume together over those {d} working days?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["exceed", "more than", "not enough", "only", "insufficient", "cannot",
                       "short", "capacity", "available", "overallocat"] if flawed else [],
        correct_answer=None if flawed else (a + b) * d,
        answer_check={"type": "number"},
        check_data={"template": "team_capacity", "tot": tot, "a": a, "b": b, "d": d},
    )


# --------------------------------------------------------------------------
# Project planning 2: "run in parallel" but one task depends on the other  (hidden_dependency)
# --------------------------------------------------------------------------
def core_parallel(rng, diff):
    return dict(diff=diff, dA=rng.randint(3, 9), dB=rng.randint(3, 9), dC=rng.randint(2, 6))


def gen_parallel(c, flawed, v):
    p = v.names[0]
    t1, t2, t3 = v.tasks
    dA, dB = c["dA"], c["dB"]
    dep = (f"{cap(t1)} cannot start until {t2} has been completed." if flawed
           else f"{cap(t1)} and {t2} do not depend on each other.")
    facts = [
        ("f1", f"{cap(t1)} takes {dA} working days."),
        ("f2", f"{cap(t2)} takes {dB} working days."),
        ("f3", dep),
    ]
    extras = [
        f"{cap(t3)} takes {c['dC']} working days and starts only after {t1} is completed.",
        "The team works Monday to Friday.",
        f"{p} is the project manager.",
        "Progress is reviewed every Wednesday.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = ("Both tasks start on day 1 and run in parallel. On which working day are both of them finished?"
             if v.variant == 0
             else f"If {t1} and {t2} both start on day 1 and run side by side, on which working day are both finished?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f3"] if flawed else [],
        flaw_keywords=["depend", "cannot start", "until", "sequential", "parallel", "after",
                       "before", "one after the other"] if flawed else [],
        correct_answer=None if flawed else max(dA, dB),
        answer_check={"type": "number"},
        check_data={"template": "parallel_tasks", "dA": dA, "dB": dB, "dep": flawed},
    )


# --------------------------------------------------------------------------
# Compliance 1: two policy clauses overlap and conflict  (contradictory_facts)
# --------------------------------------------------------------------------
CLAUSE_OPTS = 'Answer with exactly "manager approval" or "auto-approved".'


def core_clause(rng, diff):
    X = rng.choice([2000, 3000, 5000])
    gap = rng.choice([2000, 3000, 4000])
    return dict(diff=diff, X=X, Y=X + gap, Z=X + gap // 2, repair=rng.choice(["a", "b"]),
                days=rng.choice([14, 30, 60]))


def gen_clause(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    X, Y, Z = c["X"], c["Y"], c["Z"]
    if flawed:
        x_, y_ = X, Y
    elif c["repair"] == "a":
        x_, y_ = X, X
    else:
        x_, y_ = Y, Y
    facts = [
        ("f1", f"Section 4 of {org}'s expense policy: claims above {usd(x_)} require manager approval."),
        ("f2", f"Section 7 of {org}'s expense policy: claims below {usd(y_)} are approved automatically "
               f"with no manager review."),
        ("f3", f"{p} submits an expense claim of {usd(Z)}."),
    ]
    extras = [
        f"{org} requires claims to be submitted within {c['days']} days of the expense.",
        "Receipts are required for every claim.",
        "The finance team processes approved claims on Fridays.",
        f"{q} is {p}'s line manager.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What happens to {p}'s claim? {CLAUSE_OPTS}" if v.variant == 0
             else f"How is {p}'s {usd(Z)} claim handled? {CLAUSE_OPTS}")
    ans = "manager approval" if Z > x_ else "auto-approved"
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["conflict", "contradict", "inconsistent", "overlap", "both", "section 4",
                       "section 7", "ambiguous"] if flawed else [],
        correct_answer=None if flawed else ans,
        answer_check={"type": "choice", "options": ["manager approval", "auto-approved"]},
        check_data={"template": "policy_clauses", "x": x_, "y": y_, "z": Z},
    )


# --------------------------------------------------------------------------
# Compliance 2: deletion date asked for an account that is still open  (false_presupposition)
# --------------------------------------------------------------------------
def core_retention(rng, diff):
    return dict(diff=diff, ret=rng.choice([12, 24, 36]), cm=rng.randint(1, 12), cy=rng.randint(2021, 2024),
                cm2=rng.randint(1, 12), cy2=rng.randint(2021, 2024), k=rng.randint(3, 9))


def gen_retention(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    ret, cm, cy = c["ret"], c["cm"], c["cy"]
    total = cy * 12 + (cm - 1) + ret
    ans = f"{MONTHS[total % 12]} {total // 12}"
    f2 = (f"{p}'s account with {org} is still open." if flawed
          else f"{p} closed their account with {org} in {MONTHS[cm - 1]} {cy}.")
    facts = [
        ("f1", f"{org}'s data policy requires customer records to be deleted {ret} months after the "
               f"account is closed."),
        ("f2", f2),
    ]
    extras = [
        f"{q} closed their account with {org} in {MONTHS[c['cm2'] - 1]} {c['cy2']}.",
        "Customers are notified by email before their records are deleted.",
        "Deleted records are logged for audit purposes.",
        f"{org} has {c['k']} regional offices.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"In which month and year must {p}'s customer records be deleted?" if v.variant == 0
             else f"When, in terms of month and year, must {org} delete {p}'s records?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f2"] if flawed else [],
        flaw_keywords=["still open", "not closed", "active", "has not closed", "no closure",
                       "not yet", "open"] if flawed else [],
        correct_answer=None if flawed else ans,
        answer_check={"type": "monthyear"},
        check_data={"template": "retention", "open": flawed, "cm": cm, "cy": cy, "ret": ret},
    )


# --------------------------------------------------------------------------
# Compliance 3: training deadline asked, start date never given  (missing_info)
# --------------------------------------------------------------------------
def core_training(rng, diff):
    return dict(diff=diff, days=rng.choice([14, 30, 45, 60]), m=rng.randint(1, 9), d=rng.randint(1, 28),
                m2=rng.randint(1, 9), d2=rng.randint(1, 28), h=rng.choice([2, 3, 4]))


def gen_training(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    team, team2 = v.teams[0], v.teams[1]
    days = c["days"]
    start = date(2026, c["m"], c["d"])
    deadline = start + timedelta(days=days)
    f2 = f"{p} is a new employee in the {team} team."
    if not flawed:
        f2 += f" {p} started on {start.day} {MONTHS[start.month - 1]} 2026."
    facts = [
        ("f1", f"{org}'s policy requires every new employee to complete safety training within {days} "
               f"calendar days of their start date."),
        ("f2", f2),
    ]
    extras = [
        f"{q} is a new employee in the {team2} team and started on {c['d2']} {MONTHS[c['m2'] - 1]} 2026.",
        "Data-protection training must be completed within 90 days of the start date.",
        f"The safety training takes {c['h']} hours and is delivered online.",
        "Training completion is recorded in the HR system.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"By which date must {p} complete the safety training?" if v.variant == 0
             else f"What is the deadline for {p}'s safety training?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["MISSING:start_date"] if flawed else [],
        flaw_keywords=["start date", "when", "started", "joined", "not given", "unknown",
                       "not specified", "date"] if flawed else [],
        correct_answer=None if flawed else f"{deadline.day} {MONTHS[deadline.month - 1]} 2026",
        answer_check={"type": "date", "iso": None if flawed else deadline.isoformat()},
        check_data={"template": "training_deadline", "days": days,
                    "start": None if flawed else start.isoformat(),
                    "deadline": None if flawed else deadline.isoformat()},
    )


# (domain, subtype, template name, core fn, gen fn)
TEMPLATES = [
    ("hr_operations", "impossible_constraint", "hiring_budget", core_hiring, gen_hiring),
    ("hr_operations", "false_presupposition", "leave_entitlement", core_leave, gen_leave),
    ("finance", "contradictory_facts", "loan_instalment", core_emi, gen_emi),
    ("finance", "missing_info", "loan_rate", core_rate, gen_rate),
    ("project_planning", "impossible_constraint", "team_capacity", core_resource, gen_resource),
    ("project_planning", "hidden_dependency", "parallel_tasks", core_parallel, gen_parallel),
    ("compliance", "contradictory_facts", "policy_clauses", core_clause, gen_clause),
    ("compliance", "false_presupposition", "retention", core_retention, gen_retention),
    ("compliance", "missing_info", "training_deadline", core_training, gen_training),
]

TEMPLATES = TEMPLATES + batch_b.TEMPLATES_B


# --------------------------------------------------------------------------
# Answer checking
# --------------------------------------------------------------------------
def check_answer(item, answer):
    """True/False for clean items, None for flawed items (they have no correct answer)."""
    ca = item["correct_answer"]
    if ca is None:
        return None
    if answer is None:
        return False
    s = str(answer)
    low = s.lower()
    chk = item["answer_check"]
    t = chk["type"]
    if t == "number":
        tol = int(round(chk.get("tol_pct", 0) / 100 * int(ca)))
        return any(abs(x - int(ca)) <= tol for x in parse_nums(s))
    if t == "month":
        return str(ca).lower() in low
    if t == "monthyear":
        m, y = ca.split()
        return m.lower() in low and y in low
    if t == "date":
        dl = date.fromisoformat(chk["iso"])
        if chk["iso"] in s:
            return True
        return (MONTHS[dl.month - 1].lower() in low
                and re.search(rf"(?<!\d){dl.day}(?!\d)", low) is not None)
    if t == "choice":
        others = [o for o in chk["options"] if o != ca]
        return ca in low and not any(o in low for o in others)
    raise ValueError(f"unknown answer_check type {t}")


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def build_all(seed):
    plan = ([(t, "easy", True) for t in TEMPLATES]
            + [(t, "hard", True) for t in TEMPLATES]
            + [(t, "medium", False) for t in TEMPLATES])

    rng = random.Random(seed)
    private = set()
    for dom in sorted({t[0] for t, _, _ in plan}):
        idxs = [i for i, (t, _, _) in enumerate(plan, 1) if t[0] == dom]
        rng.shuffle(idxs)
        private.update(idxs[: round(PRIVATE_FRACTION * len(idxs))])

    items = []
    for idx, ((domain, subtype, tname, core_fn, gen_fn), diff, flawed) in enumerate(plan, 1):
        base_id = f"ad2-{idx:04d}"
        bseed = seed * 1000 + 500 + idx
        core = core_fn(random.Random(bseed), diff)
        v_orig = make_dview(bseed + 1)
        v_alt = make_dview(bseed + 2, avoid=v_orig)
        split = "private" if idx in private else "public"
        st = subtype if flawed else "clean_control"
        src = None if flawed else subtype

        def add(version, spec, view):
            it = make_item(base_id, version, st, diff, spec, view, split, bseed, src)
            it.update(tier=TIER, domain=domain, template=tname, generator=GEN_PATH)
            items.append(it)

        add("original", gen_fn(core, flawed, v_orig), v_orig)
        v_surf = replace(v_alt, variant=1, shuffle_seed=bseed + 3)
        add("surface", gen_fn(core, flawed, v_surf), v_surf)
        v_dist = replace(v_orig, extras=pick_distractors(bseed + 4, v_orig))
        add("distractor", gen_fn(core, flawed, v_dist), v_dist)
        if flawed:
            add("control", gen_fn(core, False, v_orig), v_orig)
    return items


# --------------------------------------------------------------------------
# Self-check: recompute every answer key and flaw label by a separate route
# --------------------------------------------------------------------------
def verify_template(it):
    cd, flawed, ca = it["check_data"], it["has_flaw"], it["correct_answer"]
    t, iid = cd["template"], it["id"]
    if t == "hiring_budget":
        assert flawed == (cd["b"] < cd["n"]), iid
        if not flawed:
            m, hired = cd["m0"], cd["r"]
            while hired < cd["n"]:
                m += 1
                hired += cd["r"]
            assert MONTHS[m - 1] == ca, iid
    elif t == "leave_entitlement":
        assert flawed == ((2026 - cd["y"]) < cd["thr"]), iid
        if not flawed:
            assert ca == cd["high"] - cd["used"], iid
    elif t == "loan_instalment":
        i, bal = cd["rate"] / 1200, float(cd["P"])
        for _ in range(cd["n"]):
            bal = bal * (1 + i) - cd["true"]
        assert abs(bal) < 2 * cd["n"], f"true instalment does not amortise {iid}"
        assert flawed == (abs(cd["stated"] - cd["true"]) / cd["true"] >= 0.25), iid
        if not flawed:
            assert cd["stated"] == cd["true"] and ca == cd["stated"] * cd["n"] - cd["P"], iid
    elif t == "loan_rate":
        assert flawed == cd["rate_missing"], iid
        if not flawed:
            assert (cd["P"] * cd["r"] * cd["t"]) % 100 == 0, iid
            assert ca == cd["P"] + cd["P"] * cd["r"] * cd["t"] // 100, iid
    elif t == "team_capacity":
        assert flawed == (cd["a"] + cd["b"] > cd["tot"]), iid
        if not flawed:
            assert ca == (cd["a"] + cd["b"]) * cd["d"], iid
    elif t == "parallel_tasks":
        assert flawed == cd["dep"], iid
        if not flawed:
            assert ca == max(cd["dA"], cd["dB"]), iid
    elif t == "policy_clauses":
        manager, auto = cd["z"] > cd["x"], cd["z"] < cd["y"]
        assert flawed == (manager and auto), iid
        if not flawed:
            assert manager != auto, iid
            assert ca == ("manager approval" if manager else "auto-approved"), iid
    elif t == "retention":
        assert flawed == cd["open"], iid
        if not flawed:
            y, m = cd["cy"], cd["cm"]
            for _ in range(cd["ret"]):
                m += 1
                if m > 12:
                    m, y = 1, y + 1
            assert ca == f"{MONTHS[m - 1]} {y}", iid
    elif t == "training_deadline":
        assert flawed == (cd["start"] is None), iid
        if not flawed:
            dl = date.fromisoformat(cd["start"]) + timedelta(days=cd["days"])
            assert dl.isoformat() == cd["deadline"] == it["answer_check"]["iso"], iid
            assert ca == f"{dl.day} {MONTHS[dl.month - 1]} 2026", iid
    elif t in batch_b.VERIFIERS:
        batch_b.VERIFIERS[t](it)
    else:
        raise AssertionError(f"unknown template {t}")


def verify(items):
    ids, prompts, by_base = set(), set(), {}
    for it in items:
        assert it["id"] not in ids, f"duplicate id {it['id']}"
        ids.add(it["id"])
        assert it["prompt"] not in prompts, f"duplicate prompt {it['id']}"
        prompts.add(it["prompt"])
        by_base.setdefault(it["base_id"], []).append(it)
        flawed = it["has_flaw"]
        fact_ids = {f["id"] for f in it["facts"]}
        if flawed:
            assert it["correct_answer"] is None and it["flaw_keywords"] and it["flaw_fact_ids"], it["id"]
            for fid in it["flaw_fact_ids"]:
                assert fid.startswith("MISSING:") or fid in fact_ids, (it["id"], fid)
        else:
            assert it["correct_answer"] is not None, it["id"]
            assert check_answer(it, it["correct_answer"]) is True, it["id"]
            ac = it["answer_check"]
            if ac["type"] == "number":
                assert check_answer(it, str(int(it["correct_answer"]) * 2 + 13)) is False, it["id"]
            if ac["type"] == "choice":
                other = [o for o in ac["options"] if o != it["correct_answer"]][0]
                assert check_answer(it, other) is False, it["id"]
        verify_template(it)
    for base_id, group in by_base.items():
        assert len({g["split"] for g in group}) == 1, f"split differs inside {base_id}"
        versions = {g["version"] for g in group}
        assert {"original", "surface", "distractor"} <= versions, base_id
        orig = next(g for g in group if g["version"] == "original")
        if orig["has_flaw"]:
            assert "control" in versions, f"flawed item {base_id} has no repaired twin"
        for g in group:
            if g["version"] != "control":
                assert g["has_flaw"] == orig["has_flaw"], base_id
            else:
                assert not g["has_flaw"], base_id


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--out", default=None, help="output folder (default: <repo>/data)")
    args = ap.parse_args()

    out = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data"
    items = build_all(args.seed)
    verify(items)

    name = f"{TRACK}_domain.jsonl"
    for split in ("public", "private"):
        folder = out / split
        folder.mkdir(parents=True, exist_ok=True)
        rows = [it for it in items if it["split"] == split]
        with open(folder / name, "w", encoding="utf-8") as f:
            for it in rows:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        doms = {}
        for it in rows:
            doms.setdefault(it["domain"], set()).add(it["base_id"])
        per = ", ".join(f"{d}={len(b)}" for d, b in sorted(doms.items()))
        print(f"{split:8s} {len(rows):3d} items from {len({it['base_id'] for it in rows}):2d} "
              f"base questions ({per}) -> {folder / name}")
    print(f"total {len(items)} items; all self-checks passed")


if __name__ == "__main__":
    main()
