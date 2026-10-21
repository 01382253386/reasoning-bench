# Methodology and design principles

This page explains why the benchmark is built the way it is, where its scenarios come from, and where it falls short.

## What it measures

Whether a model notices a hidden, false or missing premise in a business-style scenario, or answers as if nothing were wrong. It does not measure general reasoning.

## Where the scenarios come from

Tier 2 scenarios are based on mistakes that trade and practitioner sources describe as common. Each template turns one such pattern into a small scenario with a planted flaw, a repaired twin and an answer key that code can verify. The numbers and names are invented; the error patterns are not.

| Area | Real-world pattern | Template |
|---|---|---|
| HR | Hiring plan larger than the approved budget | hiring_budget |
| HR | Entitlement assumed that the policy does not give | leave_entitlement |
| HR | New starter given a full year's leave, no pro-rata | prorata_leave |
| HR | Holiday pay needs a longer reference period than the data given | holiday_pay |
| HR | Carry-over assumed where the policy has none | carry_over |
| HR | Leave paid out before it is earned | leave_earned |
| HR | Variable-hours staff with no accrual rate | hours_accrual |
| Finance | Stated instalment does not match the loan terms | loan_instalment |
| Finance | Loan total asked for with no interest rate | loan_rate |
| Finance | Profit confused with cash (unpaid credit sales) | profit_vs_cash |
| Finance | Channel margin ignored in a revenue forecast | channel_margin |
| Finance | Budget and actuals use different categories | budget_category |
| Finance | Forecast asked for with no baseline | no_baseline |
| Planning | Two tasks need more people than the team has | team_capacity |
| Planning | Tasks assumed parallel but one depends on the other | parallel_tasks |
| Planning | One person booked above 100% of their time | overallocation |
| Planning | End date depends on an approval not in the plan | signoff_wait |
| Planning | Deadline with zero slack | no_buffer |
| Planning | Tasks that each wait for the other | circular_dependency |
| Compliance | Two policy clauses conflict | policy_clauses |
| Compliance | Deletion date asked for an account still open | retention |
| Compliance | Training deadline with the start date missing | training_deadline |
| Compliance | Reporting deadline counted from the wrong date | breach_deadline |
| Compliance | Two retention rules that contradict | retention_conflict |
| Compliance | Vendor assumed to be audited, contract gives no audit rights | vendor_audit |

Sources read for this: [leave and payroll errors](https://www.leavebalance.com/blog/leave-payroll-errors/), [budget and forecast mistakes (SBA)](https://www.sba.gov/blog/5-classic-fails-budgets-forecasts), [project scheduling mistakes](https://www.planradar.com/au/5-common-project-scheduling-mistakes/), [compliance mistakes](https://aaronhall.com/compliance-mistakes-leading-to-regulator-scrutiny). These are general trade articles, not audits, so they show that the patterns are common, not how often they occur.

## Design principles

These follow common advice on keeping benchmarks reliable (fresh questions, checkable answers, held-out data, watching for saturation), applied at small scale.

| Principle | How this benchmark applies it | Honest status |
|---|---|---|
| Answers checked by code, not opinion | Every key is recomputed by a separate verifier; builds fail if any check fails | Done |
| Control for "flag everything" | Every flawed question has a repaired twin; false alarms are reported | Done |
| Robustness | Each question comes in original, surface-changed and distractor versions | Done |
| Held-out data | 30% of scenarios are generated separately with a secret seed and never published; only a SHA-256 fingerprint is public so the set can be verified when revealed | Done; not yet used for published results |
| Uncertainty shown | 95% Wilson intervals on every proportion | Done |
| Reproducible | Fixed seed, logged prompts, one command per step, standard library only | Done |
| Scoring of the reply | Flag-style uses the model's own boolean; plain-style uses a judge model that sees the planted flaw (`runner/judge.py`) | Judge checked by hand on a sample only |
| Size | 99 base scenarios, 367 items including variants | Small |
| Variety | 25 business templates, 3 scenarios each | Limited, templated wording |
| Human review | Not yet done | Needed |
| Human baseline | A short form with 12 of the public scenarios is planned | Not yet done |
| Saturation watch | Easy templates may be caught by strong models; results by template will show which | Pending more models |

## Prompt styles

- **flag**: the model is told to check for problems. Strong models score near the ceiling, so this mainly shows the benchmark runs.
- **plain**: the model just answers, with an optional caveats field. This tests whether it volunteers the problem unprompted, which is closer to real use.

## Scoring plain-style replies

An early version matched words like "contradiction" in the caveats. A check against real replies showed that this undercounted: a reply saying "technically he is entitled to 14 days (not 22)" had caught the flaw but was marked as a miss. The current method asks a separate judge model whether the reply points out the specific planted flaw. On clean questions it asks whether the reply wrongly claims a problem. The judge is also an AI model, so its verdicts are spot-checked by hand and should be treated as approximate.

## Known limitations

See the README. In short: small, templated, one prompt format per style, scored partly by an AI judge, not peer reviewed.
