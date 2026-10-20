#!/usr/bin/env python3
"""Extra tier-2 scenario templates for the assumption-detection track (batch B).

Each template is grounded in a mistake that is documented as common in real HR, finance,
project-planning and compliance work (see docs/real_world_patterns.md for the source of each
pattern). Same contract as generators/assumption_detection_domain.py: the planted flaw is known
by construction, every flawed item has a repaired twin, and every answer key is recomputed by
a separate route in VERIFIERS.

This module is imported by assumption_detection_domain.py; it is not run on its own.
"""
from __future__ import annotations

from datetime import date, timedelta

from assumption_detection import MONTHS, Spec

N_EXTRA = {"easy": 0, "medium": 2, "hard": 4}


def usd(n):
    return f"${n:,}"


def cap(s):
    return s[0].upper() + s[1:]


def extras_for(texts, diff):
    return [(f"x{i + 1}", t) for i, t in enumerate(texts[: N_EXTRA[diff]])]


def fmt(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def add_months(y, m, k):
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


# ==========================================================================
# HR 1: pro-rata leave for a mid-year joiner  (false_presupposition)
# ==========================================================================
def core_prorata(rng, diff):
    return dict(diff=diff, E=rng.choice([20, 24, 26, 28]), m=rng.randint(4, 9),
                used=rng.randint(2, 6), k=rng.randint(3, 9))


def gen_prorata(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    E, m, used = c["E"], c["m"], c["used"]
    join = f"1 {MONTHS[m - 1]} 2026" if flawed else "1 January 2025"
    facts = [
        ("f1", f"Under {org}'s leave policy, employees who joined before 1 January 2026 receive {E} days "
               f"of annual leave in 2026. Employees who join during 2026 receive {E} days divided by 12 "
               f"for each month of 2026 remaining, counting the month they join."),
        ("f2", f"{p} joined {org} on {join}."),
        ("f3", f"{p} has taken {used} days of annual leave so far in 2026."),
    ]
    extras = [
        f"{q} joined {org} on 1 January 2020.",
        "The leave year runs from 1 January to 31 December.",
        "Public holidays do not count against annual leave.",
        f"{org} has {c['k']} offices.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many of {p}'s {E} annual leave days for 2026 remain?" if v.variant == 0
             else f"{p} has {E} days of annual leave for 2026. How many are left?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["pro rata", "pro-rata", "prorata", "joined", "divided by 12", "months",
                       "not the full", "fewer", "entitle"] if flawed else [],
        correct_answer=None if flawed else E - used,
        answer_check={"type": "number"},
        check_data={"template": "prorata_leave", "E": E, "join_month": m if flawed else None, "used": used},
    )


# ==========================================================================
# HR 2: holiday pay needs a 52-week average, only 12 weeks given  (missing_info)
# ==========================================================================
def core_holiday(rng, diff):
    w = rng.choice([400, 450, 500, 550, 600, 650])
    return dict(diff=diff, w=w, w12=w + rng.choice([-60, -40, 50, 80]), k=rng.randint(3, 9))


def gen_holiday(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    w = c["w"]
    if flawed:
        f2 = f"{p} earned {usd(c['w12'] * 12)} in total over the last 12 weeks."
    else:
        f2 = f"{p} earned {usd(w * 52)} in total over the last 52 weeks."
    facts = [
        ("f1", f"{org}'s policy: holiday pay for one week of leave equals the employee's average weekly "
               f"earnings over the previous 52 weeks."),
        ("f2", f2),
    ]
    extras = [
        f"{q} earned {usd(c['w'] + 100)} per week over the same period.",
        "Holiday pay is paid on the normal pay date.",
        f"{org} pays employees every two weeks.",
        f"{org} has {c['k']} departments.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What is {p}'s holiday pay for one week of leave?" if v.variant == 0
             else f"How much holiday pay does {p} receive for a week of leave?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["52", "12 weeks", "12-week", "twelve", "reference period", "only",
                       "not enough", "missing", "average"] if flawed else [],
        correct_answer=None if flawed else w,
        answer_check={"type": "number"},
        check_data={"template": "holiday_pay", "weeks": 12 if flawed else 52,
                    "total": c["w12"] * 12 if flawed else w * 52, "w": w},
    )


# ==========================================================================
# HR 3: carry-over of leave asked about, but policy forbids it  (false_presupposition)
# ==========================================================================
def core_carry(rng, diff):
    return dict(diff=diff, C=rng.choice([3, 4, 5]), U=rng.randint(2, 8), k=rng.randint(3, 9))


def gen_carry(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    C, U = c["C"], c["U"]
    f1 = (f"{org}'s leave policy: unused annual leave cannot be carried over into the next year." if flawed
          else f"{org}'s leave policy: up to {C} unused annual leave days can be carried over into the next "
               f"year and must be used by 31 March.")
    facts = [
        ("f1", f1),
        ("f2", f"{p} has {U} unused annual leave days at the end of 2026."),
    ]
    extras = [
        f"{q} has {U + 3} unused annual leave days at the end of 2026.",
        "The leave year runs from 1 January to 31 December.",
        "Leave requests are approved by the line manager.",
        f"{org} has {c['k']} offices.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many of {p}'s carried-over days must be used by 31 March 2027?" if v.variant == 0
             else f"By 31 March 2027, how many carried-over days of {p}'s leave need to be used?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1"] if flawed else [],
        flaw_keywords=["cannot be carried", "no carry", "not carried", "carried over", "carry over",
                       "forfeit", "expire", "lost"] if flawed else [],
        correct_answer=None if flawed else min(U, C),
        answer_check={"type": "number"},
        check_data={"template": "carry_over", "allowed": not flawed, "C": C, "U": U},
    )


# ==========================================================================
# HR 4: leave booked before it is earned  (impossible_constraint)
# ==========================================================================
def core_earned(rng, diff):
    r = rng.choice([2, 3])
    M = rng.randint(3, 6)
    return dict(diff=diff, r=r, M=M, n_ok=rng.randint(2, r * M - 1), n_bad=r * M + rng.randint(2, 4),
                k=rng.randint(3, 9))


def gen_earned(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    r, M = c["r"], c["M"]
    n = c["n_bad"] if flawed else c["n_ok"]
    facts = [
        ("f1", f"At {org}, an employee earns {r} days of leave for each completed month of service, "
               f"counted from a start date of 1 January 2026. Leave can only be taken after it has been earned."),
        ("f2", f"{p} plans to take {n} days of leave at the end of {MONTHS[M - 1]} 2026, by which time "
               f"{p} will have completed {M} months of service."),
    ]
    extras = [
        f"{q} started on 1 January 2026 as well.",
        "Leave requests need two weeks' notice.",
        "Leave is booked through the HR portal.",
        f"{org} has {c['k']} offices.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many earned leave days will {p} have left after that leave?" if v.variant == 0
             else f"After taking that leave, how many earned days does {p} still have?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["earned", "accrued", "not enough", "only", "exceed", "more than",
                       "cannot", "insufficient", "short"] if flawed else [],
        correct_answer=None if flawed else r * M - n,
        answer_check={"type": "number"},
        check_data={"template": "leave_earned", "r": r, "M": M, "n": n},
    )


# ==========================================================================
# HR 5: leave accrues on hours worked, percentage not given  (missing_info)
# ==========================================================================
def core_hours(rng, diff):
    return dict(diff=diff, pct=rng.choice([8, 10, 12]), H=rng.choice([400, 500, 600, 800, 1000]),
                k=rng.randint(3, 9))


def gen_hours(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    pct, H = c["pct"], c["H"]
    f2 = (f"The accrual percentage is set out in the company handbook." if flawed
          else f"The accrual percentage is {pct}%.")
    facts = [
        ("f1", f"{p} works variable hours at {org}. Leave accrues as a fixed percentage of the hours worked."),
        ("f2", f2),
        ("f3", f"{p} worked {H} hours in the last quarter."),
    ]
    extras = [
        f"{q} worked {H + 100} hours in the last quarter.",
        "Leave is recorded in hours.",
        f"{org} pays variable-hours staff monthly.",
        f"{org} has {c['k']} offices.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many hours of leave did {p} accrue in the last quarter?" if v.variant == 0
             else f"How much leave, in hours, has {p} accrued from the last quarter's work?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["MISSING:accrual_percentage"] if flawed else [],
        flaw_keywords=["percentage", "percent", "rate", "%", "handbook", "not given",
                       "not specified", "unknown", "missing"] if flawed else [],
        correct_answer=None if flawed else H * pct // 100,
        answer_check={"type": "number"},
        check_data={"template": "hours_accrual", "pct": None if flawed else pct, "H": H},
    )


# ==========================================================================
# Finance 1: cash balance asked, credit sales not collected  (missing_info)
# ==========================================================================
def core_cash(rng, diff):
    return dict(diff=diff, O=rng.choice([40000, 60000, 85000, 120000]),
                P=rng.choice([15000, 22000, 30000, 45000]), k=rng.randint(3, 9))


def gen_cash(c, flawed, v):
    org, q, city = v.orgs[0], v.names[1], v.cities[0]
    O, P = c["O"], c["P"]
    f3 = (f"Some customers were invoiced on credit and have not yet paid." if flawed
          else f"All revenue was collected in cash and all expenses were paid in cash during the quarter.")
    facts = [
        ("f1", f"{org} started the quarter with {usd(O)} in cash."),
        ("f2", f"{org}'s profit for the quarter was {usd(P)}."),
        ("f3", f3),
    ]
    extras = [
        f"{org} has an office in {city}.",
        f"{q} prepared the quarterly accounts.",
        "The quarter ended on 30 September.",
        f"{org} has {c['k']} employees.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How much cash does {org} hold at the end of the quarter?" if v.variant == 0
             else f"What is {org}'s cash balance at quarter end?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f3"] if flawed else [],
        flaw_keywords=["credit", "not yet paid", "unpaid", "receivable", "cash", "profit",
                       "not the same", "collected"] if flawed else [],
        correct_answer=None if flawed else O + P,
        answer_check={"type": "number"},
        check_data={"template": "profit_vs_cash", "O": O, "P": P, "uncollected": flawed},
    )


# ==========================================================================
# Finance 2: distributor discount not given  (missing_info)
# ==========================================================================
def core_margin(rng, diff):
    return dict(diff=diff, N=rng.choice([200, 300, 400, 500, 800]), L=rng.choice([50, 80, 100, 120, 150]),
                k=rng.randint(3, 9))


def gen_margin(c, flawed, v):
    org, q, city = v.orgs[0], v.names[1], v.cities[0]
    N, L = c["N"], c["L"]
    f2 = (f"Distributors buy from {org} at a discount to the list price of {usd(L)} per unit." if flawed
          else f"Distributors buy from {org} at 60% of the list price of {usd(L)} per unit.")
    facts = [
        ("f1", f"{org} expects to sell {N} units this year, all through distributors."),
        ("f2", f2),
    ]
    extras = [
        f"{org} sells in {c['k']} regions.",
        f"{q} manages the distributor relationships.",
        f"The distributors are based in {city}.",
        "Payment from distributors is due within 30 days.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What revenue will {org} receive from the distributors for these units?" if v.variant == 0
             else f"How much will the distributors pay {org} in total for these {N} units?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f2"] if flawed else [],
        flaw_keywords=["discount", "how much", "percentage", "not specified", "not given",
                       "unknown", "missing", "rate"] if flawed else [],
        correct_answer=None if flawed else N * L * 60 // 100,
        answer_check={"type": "number"},
        check_data={"template": "channel_margin", "N": N, "L": L, "pct": None if flawed else 60},
    )


# ==========================================================================
# Finance 3: budget category missing from the actuals report  (false_presupposition)
# ==========================================================================
def core_category(rng, diff):
    return dict(diff=diff, a=rng.choice([8000, 10000, 12000]), b=rng.choice([3000, 4000, 5000]),
                c=rng.choice([6000, 8000]), over=rng.choice([1500, 2000, 2500]),
                a2=rng.choice([9000, 11000]), b2=rng.choice([2500, 3500]), f2=rng.choice([4000, 5000]),
                k=rng.randint(3, 9))


def gen_category(c, flawed, v):
    org, q = v.orgs[0], v.names[1]
    bud = c["c"]
    act = bud + c["over"]
    f2 = (f"{org}'s actual-spend report for the quarter lists: Marketing {usd(c['a2'])}, Travel "
          f"{usd(c['b2'])}, Facilities {usd(c['f2'])}." if flawed
          else f"{org}'s actual-spend report for the quarter lists: Marketing {usd(c['a2'])}, Travel "
               f"{usd(c['b2'])}, Software {usd(act)}.")
    facts = [
        ("f1", f"{org}'s budget for the quarter: Marketing {usd(c['a'])}, Travel {usd(c['b'])}, "
               f"Software {usd(bud)}."),
        ("f2", f2),
    ]
    extras = [
        f"{q} prepared the budget.",
        "The quarter ended on 31 March.",
        "Budget lines are reviewed monthly.",
        f"{org} has {c['k']} departments.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = ("By how much did actual Software spending exceed its budget?" if v.variant == 0
             else "How far over budget was the actual Software spend?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["software", "no software", "not listed", "does not list", "missing",
                       "category", "categories", "no actual", "not in"] if flawed else [],
        correct_answer=None if flawed else c["over"],
        answer_check={"type": "number"},
        check_data={"template": "budget_category", "software_in_actuals": not flawed,
                    "budget": bud, "actual": None if flawed else act},
    )


# ==========================================================================
# Finance 4: forecast needs last year's revenue, not finalised  (missing_info)
# ==========================================================================
def core_baseline(rng, diff):
    return dict(diff=diff, R=rng.choice([120000, 250000, 400000, 640000]), g=rng.choice([5, 10, 20]),
                k=rng.randint(3, 9))


def gen_baseline(c, flawed, v):
    org, q, city = v.orgs[0], v.names[1], v.cities[0]
    R, g = c["R"], c["g"]
    f2 = (f"This year's revenue figure has not yet been finalised by the accounts team." if flawed
          else f"{org}'s revenue this year was {usd(R)}.")
    facts = [
        ("f1", f"{org}'s forecasting rule: next year's revenue equals this year's revenue increased by {g}%."),
        ("f2", f2),
    ]
    extras = [
        f"{org} has an office in {city}.",
        f"{q} owns the forecast model.",
        "The forecast is updated every quarter.",
        f"{org} has {c['k']} product lines.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What is {org}'s forecast revenue for next year?" if v.variant == 0
             else f"Using the rule, what revenue should {org} forecast for next year?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["MISSING:this_year_revenue"] if flawed else [],
        flaw_keywords=["not finalised", "not finalized", "this year's revenue", "baseline",
                       "not given", "unknown", "missing", "figure"] if flawed else [],
        correct_answer=None if flawed else R * (100 + g) // 100,
        answer_check={"type": "number"},
        check_data={"template": "no_baseline", "R": None if flawed else R, "g": g},
    )


# ==========================================================================
# Planning 1: one person over-allocated beyond 100%  (impossible_constraint)
# ==========================================================================
def core_overalloc(rng, diff):
    a, b = rng.choice([20, 30, 40]), rng.choice([20, 30])
    c_ok = rng.choice([x for x in (10, 15, 20, 25) if a + b + x <= 95])
    c_bad = 100 - a - b + rng.choice([10, 20])
    return dict(diff=diff, a=a, b=b, c_ok=c_ok, c_bad=c_bad, k=rng.randint(3, 9))


def gen_overalloc(c, flawed, v):
    p, q, team = v.names[0], v.names[1], v.teams[0]
    t1, t2, t3 = v.tasks
    a, b = c["a"], c["b"]
    cc = c["c_bad"] if flawed else c["c_ok"]
    facts = [
        ("f1", f"{p} is assigned to three tasks: {t1} takes {a}% of {p}'s working time, {t2} takes {b}% "
               f"and {t3} takes {cc}%."),
        ("f2", f"{p} works full-time and does nothing else besides these three tasks."),
    ]
    extras = [
        f"{q} is assigned to {t1} as well.",
        f"{p} is a member of the {team} team.",
        "The team works Monday to Friday.",
        "Task progress is reviewed every Wednesday.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"What percentage of {p}'s working time is left free?" if v.variant == 0
             else f"After these three tasks, how much of {p}'s working time, as a percentage, remains unassigned?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["100", "exceed", "over", "more than", "overallocat", "over-allocat",
                       "impossible", "negative", "total"] if flawed else [],
        correct_answer=None if flawed else 100 - a - b - cc,
        answer_check={"type": "number"},
        check_data={"template": "overallocation", "a": a, "b": b, "c": cc},
    )


# ==========================================================================
# Planning 2: start depends on a sign-off with no date  (missing_info)
# ==========================================================================
def core_signoff(rng, diff):
    return dict(diff=diff, A=rng.choice([4, 6, 8, 10]), D=rng.randint(6, 15), k=rng.randint(3, 9))


def gen_signoff(c, flawed, v):
    p, team = v.names[0], v.teams[0]
    t1, t2, _ = v.tasks
    A, D = c["A"], c["D"]
    f2 = (f"The security team has not said when it will complete the sign-off." if flawed
          else f"The security team will complete the sign-off at the end of working day {A}.")
    facts = [
        ("f1", f"{cap(t1)} can only start after the security team's sign-off."),
        ("f2", f2),
        ("f3", f"{cap(t1)} starts on the working day after the sign-off and takes {D} working days."),
    ]
    extras = [
        f"{cap(t2)} is not affected by the sign-off.",
        f"{p} is the project manager.",
        f"The {team} team works Monday to Friday.",
        "Progress is reviewed every Wednesday.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"On which working day does {t1} finish?" if v.variant == 0
             else f"{cap(t1)} will be completed on which working day?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f2"] if flawed else [],
        flaw_keywords=["sign-off", "signoff", "not said", "unknown", "when", "date",
                       "not given", "not specified", "missing"] if flawed else [],
        correct_answer=None if flawed else A + D,
        answer_check={"type": "number"},
        check_data={"template": "signoff_wait", "A": None if flawed else A, "D": D},
    )


# ==========================================================================
# Planning 3: sequential tasks do not fit before the deadline  (impossible_constraint)
# ==========================================================================
def core_slack(rng, diff):
    T = rng.choice([20, 24, 30])
    d1, d2 = rng.randint(4, 9), rng.randint(4, 9)
    d3_ok = rng.randint(2, T - d1 - d2 - 2) if T - d1 - d2 - 2 >= 2 else 2
    return dict(diff=diff, T=T, d1=d1, d2=d2, d3_ok=d3_ok,
                d3_bad=T - d1 - d2 + rng.randint(2, 5), k=rng.randint(3, 9))


def gen_slack(c, flawed, v):
    p = v.names[0]
    t1, t2, t3 = v.tasks
    d3 = c["d3_bad"] if flawed else c["d3_ok"]
    facts = [
        ("f1", f"{cap(t1)}, {t2} and {t3} must be done one after another, in that order."),
        ("f2", f"{cap(t1)} takes {c['d1']} working days, {t2} takes {c['d2']} and {t3} takes {d3}."),
        ("f3", f"Everything must be finished by working day {c['T']}."),
    ]
    extras = [
        f"{p} is the project manager.",
        "The team works Monday to Friday.",
        "Progress is reviewed every Wednesday.",
        f"The project has {c['k']} stakeholders.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = ("How many working days of slack remain before the deadline?" if v.variant == 0
             else "By how many working days does the plan finish ahead of the deadline?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f2", "f3"] if flawed else [],
        flaw_keywords=["exceed", "more than", "over", "not enough", "no slack", "negative",
                       "after the deadline", "late", "cannot", "impossible"] if flawed else [],
        correct_answer=None if flawed else c["T"] - c["d1"] - c["d2"] - d3,
        answer_check={"type": "number"},
        check_data={"template": "no_buffer", "T": c["T"], "d": [c["d1"], c["d2"], d3]},
    )


# ==========================================================================
# Planning 4: circular dependency  (contradictory_facts)
# ==========================================================================
def core_cycle(rng, diff):
    return dict(diff=diff, dA=rng.randint(3, 9), dB=rng.randint(3, 9), k=rng.randint(3, 9))


def gen_cycle(c, flawed, v):
    p = v.names[0]
    t1, t2, t3 = v.tasks
    f2 = (f"{cap(t2)} takes {c['dB']} working days and cannot start until {t1} is finished." if flawed
          else f"{cap(t2)} takes {c['dB']} working days and has no prerequisites.")
    facts = [
        ("f1", f"{cap(t1)} takes {c['dA']} working days and cannot start until {t2} is finished."),
        ("f2", f2),
    ]
    extras = [
        f"{cap(t3)} is not connected to either task.",
        f"{p} is the project manager.",
        "The team works Monday to Friday.",
        "Progress is reviewed every Wednesday.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"If work starts on day 1, on which working day is {t1} finished?" if v.variant == 0
             else f"Work begins on day 1. {cap(t1)} will be done on which working day?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["circular", "deadlock", "each other", "neither", "cannot start",
                       "until", "loop", "dependency", "contradict"] if flawed else [],
        correct_answer=None if flawed else c["dA"] + c["dB"],
        answer_check={"type": "number"},
        check_data={"template": "circular_dependency", "cycle": flawed, "dA": c["dA"], "dB": c["dB"]},
    )


# ==========================================================================
# Compliance 1: deadline counted from the wrong date  (contradictory_facts)
# ==========================================================================
def core_breach(rng, diff):
    occ = date(2026, rng.randint(1, 6), rng.randint(1, 20))
    return dict(diff=diff, N=rng.choice([30, 45, 60]), occ=occ.isoformat(), gap=rng.randint(5, 20),
                k=rng.randint(3, 9))


def gen_breach(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    N = c["N"]
    occ = date.fromisoformat(c["occ"])
    disc = occ + timedelta(days=c["gap"])
    f3 = (f"The compliance calendar lists the reporting deadline as {N} days after the date the breach "
          f"occurred." if flawed else "The compliance calendar notes that the breach has been logged.")
    facts = [
        ("f1", f"{org}'s policy: a data breach must be reported to the regulator within {N} calendar days "
               f"of the date it was discovered."),
        ("f2", f"A breach at {org} occurred on {fmt(occ)} and was discovered on {fmt(disc)}."),
        ("f3", f3),
    ]
    extras = [
        f"{p} is the data protection officer.",
        f"{q} reported the incident internally.",
        "Reports to the regulator are filed online.",
        f"{org} has {c['k']} offices.",
    ]
    facts += extras_for(extras, c["diff"])
    ans = disc + timedelta(days=N)
    q_txt = ("What is the deadline for reporting the breach to the regulator?" if v.variant == 0
             else "By which date must the breach be reported to the regulator?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f3"] if flawed else [],
        flaw_keywords=["calendar", "occurred", "discovered", "conflict", "contradict", "inconsistent",
                       "differ", "policy", "mismatch"] if flawed else [],
        correct_answer=None if flawed else fmt(ans),
        answer_check={"type": "date", "iso": None if flawed else ans.isoformat()},
        check_data={"template": "breach_deadline", "N": N, "occ": c["occ"], "disc": disc.isoformat(),
                    "calendar_uses_occurrence": flawed},
    )


# ==========================================================================
# Compliance 2: two retention rules cover the same records  (contradictory_facts)
# ==========================================================================
def core_conflict(rng, diff):
    a = rng.choice([12, 18, 24])
    return dict(diff=diff, a=a, b=a + rng.choice([12, 24]), cm=rng.randint(1, 12), cy=rng.randint(2022, 2024),
                k=rng.randint(3, 9))


def gen_conflict(c, flawed, v):
    org, p, q = v.orgs[0], v.names[0], v.names[1]
    a, b, cm, cy = c["a"], c["b"], c["cm"], c["cy"]
    f2 = (f"{org}'s Finance Policy: customer records must be kept for {b} months after the account is closed."
          if flawed else
          f"{org}'s Finance Policy: supplier contracts must be kept for {b} months after the contract ends.")
    facts = [
        ("f1", f"{org}'s Privacy Policy: customer records are deleted {a} months after the account is closed."),
        ("f2", f2),
        ("f3", f"{p} closed their account with {org} in {MONTHS[cm - 1]} {cy}."),
    ]
    extras = [
        f"{q} closed their account with {org} in {MONTHS[(cm % 12)]} {cy}.",
        "Deleted records are logged for audit purposes.",
        "Customers are notified by email before deletion.",
        f"{org} has {c['k']} regional offices.",
    ]
    facts += extras_for(extras, c["diff"])
    y, m = add_months(cy, cm, a)
    q_txt = (f"In which month and year must {p}'s customer records be deleted?" if v.variant == 0
             else f"When, by month and year, does {org} have to delete {p}'s customer records?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f1", "f2"] if flawed else [],
        flaw_keywords=["conflict", "contradict", "inconsistent", "finance policy", "privacy policy",
                       "kept", "retain", "both", "overlap"] if flawed else [],
        correct_answer=None if flawed else f"{MONTHS[m - 1]} {y}",
        answer_check={"type": "monthyear"},
        check_data={"template": "retention_conflict", "a": a, "b": b, "cm": cm, "cy": cy,
                    "overlap": flawed},
    )


# ==========================================================================
# Compliance 3: vendor audit that never happened  (false_presupposition)
# ==========================================================================
def core_vendor(rng, diff):
    return dict(diff=diff, k1=rng.randint(1, 6), k2=rng.randint(1, 6), k3=rng.randint(1, 6),
                k=rng.randint(3, 9))


def gen_vendor(c, flawed, v):
    org, p = v.orgs[0], v.names[0]
    v1, v2, v3 = v.orgs[1], v.orgs[2], v.orgs[3]
    f3 = (f"{org}'s contract with {v3} contains no audit rights, so {v3} was not audited." if flawed
          else f"The audit of {v3} reported {c['k3']} findings.")
    facts = [
        ("f1", f"{org} audited its vendors in 2026."),
        ("f2", f"The audit of {v1} reported {c['k1']} findings and the audit of {v2} reported {c['k2']} findings."),
        ("f3", f3),
    ]
    extras = [
        f"{p} leads the vendor compliance programme.",
        "Audit reports are shared with the board.",
        "Vendors have 30 days to respond to findings.",
        f"{org} has {c['k']} vendors in total.",
    ]
    facts += extras_for(extras, c["diff"])
    q_txt = (f"How many findings did the 2026 audit of {v3} report?" if v.variant == 0
             else f"The audit of {v3} in 2026 reported how many findings?")
    return Spec(
        facts=facts, question=q_txt, has_flaw=flawed,
        flaw_fact_ids=["f3"] if flawed else [],
        flaw_keywords=["not audited", "no audit", "was not", "no audit rights", "never audited",
                       "no findings", "did not audit"] if flawed else [],
        correct_answer=None if flawed else c["k3"],
        answer_check={"type": "number"},
        check_data={"template": "vendor_audit", "audited": not flawed, "k3": c["k3"]},
    )


# (domain, subtype, template name, core fn, gen fn)
TEMPLATES_B = [
    ("hr_operations", "false_presupposition", "prorata_leave", core_prorata, gen_prorata),
    ("hr_operations", "missing_info", "holiday_pay", core_holiday, gen_holiday),
    ("hr_operations", "false_presupposition", "carry_over", core_carry, gen_carry),
    ("hr_operations", "impossible_constraint", "leave_earned", core_earned, gen_earned),
    ("hr_operations", "missing_info", "hours_accrual", core_hours, gen_hours),
    ("finance", "missing_info", "profit_vs_cash", core_cash, gen_cash),
    ("finance", "missing_info", "channel_margin", core_margin, gen_margin),
    ("finance", "false_presupposition", "budget_category", core_category, gen_category),
    ("finance", "missing_info", "no_baseline", core_baseline, gen_baseline),
    ("project_planning", "impossible_constraint", "overallocation", core_overalloc, gen_overalloc),
    ("project_planning", "missing_info", "signoff_wait", core_signoff, gen_signoff),
    ("project_planning", "impossible_constraint", "no_buffer", core_slack, gen_slack),
    ("project_planning", "contradictory_facts", "circular_dependency", core_cycle, gen_cycle),
    ("compliance", "contradictory_facts", "breach_deadline", core_breach, gen_breach),
    ("compliance", "contradictory_facts", "retention_conflict", core_conflict, gen_conflict),
    ("compliance", "false_presupposition", "vendor_audit", core_vendor, gen_vendor),
]


# ==========================================================================
# Independent re-checks of every answer key and flaw label
# ==========================================================================
def _v_prorata(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["join_month"] is not None), it["id"]
    if not f:
        assert it["correct_answer"] == cd["E"] - cd["used"], it["id"]


def _v_holiday(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["weeks"] != 52), it["id"]
    if not f:
        assert cd["total"] % 52 == 0 and it["correct_answer"] == cd["total"] // 52, it["id"]


def _v_carry(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (not cd["allowed"]), it["id"]
    if not f:
        assert it["correct_answer"] == min(cd["U"], cd["C"]), it["id"]


def _v_earned(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["n"] > cd["r"] * cd["M"]), it["id"]
    if not f:
        assert it["correct_answer"] == cd["r"] * cd["M"] - cd["n"], it["id"]


def _v_hours(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["pct"] is None), it["id"]
    if not f:
        assert (cd["H"] * cd["pct"]) % 100 == 0 and it["correct_answer"] == cd["H"] * cd["pct"] // 100, it["id"]


def _v_cash(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == cd["uncollected"], it["id"]
    if not f:
        assert it["correct_answer"] == cd["O"] + cd["P"], it["id"]


def _v_margin(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["pct"] is None), it["id"]
    if not f:
        assert (cd["N"] * cd["L"] * cd["pct"]) % 100 == 0, it["id"]
        assert it["correct_answer"] == cd["N"] * cd["L"] * cd["pct"] // 100, it["id"]


def _v_category(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (not cd["software_in_actuals"]), it["id"]
    joined = " ".join(x["text"] for x in it["facts"] if x["id"] == "f2")
    assert ("Software" in joined) == (not f), it["id"]
    if not f:
        assert cd["actual"] > cd["budget"] and it["correct_answer"] == cd["actual"] - cd["budget"], it["id"]


def _v_baseline(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["R"] is None), it["id"]
    if not f:
        assert (cd["R"] * (100 + cd["g"])) % 100 == 0, it["id"]
        assert it["correct_answer"] == cd["R"] * (100 + cd["g"]) // 100, it["id"]


def _v_overalloc(it):
    cd, f = it["check_data"], it["has_flaw"]
    tot = cd["a"] + cd["b"] + cd["c"]
    assert f == (tot > 100), it["id"]
    if not f:
        assert tot < 100 and it["correct_answer"] == 100 - tot, it["id"]


def _v_signoff(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (cd["A"] is None), it["id"]
    if not f:
        day = cd["A"]
        for _ in range(cd["D"]):
            day += 1
        assert it["correct_answer"] == day, it["id"]


def _v_slack(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (sum(cd["d"]) > cd["T"]), it["id"]
    if not f:
        assert sum(cd["d"]) < cd["T"] and it["correct_answer"] == cd["T"] - sum(cd["d"]), it["id"]


def _v_cycle(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == cd["cycle"], it["id"]
    if not f:
        assert it["correct_answer"] == cd["dA"] + cd["dB"], it["id"]


def _v_breach(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == cd["calendar_uses_occurrence"], it["id"]
    disc = date.fromisoformat(cd["disc"])
    assert disc > date.fromisoformat(cd["occ"]), it["id"]
    if not f:
        dl = disc + timedelta(days=cd["N"])
        assert it["correct_answer"] == fmt(dl) and it["answer_check"]["iso"] == dl.isoformat(), it["id"]


def _v_conflict(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == cd["overlap"] and cd["b"] > cd["a"], it["id"]
    if not f:
        y, m = cd["cy"], cd["cm"]
        for _ in range(cd["a"]):
            m += 1
            if m > 12:
                m, y = 1, y + 1
        assert it["correct_answer"] == f"{MONTHS[m - 1]} {y}", it["id"]


def _v_vendor(it):
    cd, f = it["check_data"], it["has_flaw"]
    assert f == (not cd["audited"]), it["id"]
    if not f:
        assert it["correct_answer"] == cd["k3"], it["id"]


VERIFIERS = {
    "prorata_leave": _v_prorata, "holiday_pay": _v_holiday, "carry_over": _v_carry,
    "leave_earned": _v_earned, "hours_accrual": _v_hours, "profit_vs_cash": _v_cash,
    "channel_margin": _v_margin, "budget_category": _v_category, "no_baseline": _v_baseline,
    "overallocation": _v_overalloc, "signoff_wait": _v_signoff, "no_buffer": _v_slack,
    "circular_dependency": _v_cycle, "breach_deadline": _v_breach, "retention_conflict": _v_conflict,
    "vendor_audit": _v_vendor,
}
