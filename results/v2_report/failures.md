# Failure examples

Concrete cases taken from the logs. Replies are shortened to 400 characters.

## gemini-flash-lite

### Caught the original, missed the perturbed version

**ad-0001** (abstract, contradictory_facts), perturbation: distractor

Original question:

> Arjun was born in 1997. Arjun is 35 years old as of 2026.
> 
> Question: In 2031, how old will Arjun be at the end of the year?

Perturbed question:

> Arjun was born in 1997. Arjun is 35 years old as of 2026. Zoya enjoys cycling on weekends. Isha prefers to take the stairs instead of the lift. The parking area is closed on Sundays.
> 
> Question: In 2031, how old will Arjun be at the end of the year?

Model reply to the perturbed version:

```
```json
{"answer": "39", "caveats": null}
```
```

**ad-0012** (abstract, missing_info), perturbation: surface

Original question:

> A train leaves Ashford at 09:00 and travels non-stop at 90 km/h toward Brenton. A second train leaves Ashford at 10:00 and travels at 75 km/h toward Fairhaven. The rail route from Ashford to Fairhaven is 225 km long. A bus covers the road from Brenton to Fairhaven in 3 hours. Brenton station has 9 platforms.
> 
> Question: At what time does the first train arrive in Brenton?

Perturbed question:

> Glenrock station has 9 platforms. A bus covers the road from Glenrock to Hollis in 3 hours. The rail route from Dunmore to Hollis is 225 km long. A second train leaves Dunmore at 10:00 and travels at 75 km/h toward Hollis. A train leaves Dunmore at 09:00 and travels non-stop at 90 km/h toward Glenrock.
> 
> Question: When will the train from Dunmore reach Glenrock?

Model reply to the perturbed version:

```
```json
{"answer": "11:30", "caveats": null}
```
```

**ad-0014** (abstract, hidden_dependency), perturbation: distractor

Original question:

> The Platform team has 3 engineers: Meera, Isha, Anika. A sprint lasts 5 working days. Meera is on leave for the whole of the sprint.
> 
> Question: All 3 engineers will work on every day of the sprint. How many engineer-days of work will the Platform team deliver in the sprint?

Perturbed question:

> The Platform team has 3 engineers: Meera, Isha, Anika. A sprint lasts 5 working days. A new coffee machine was installed in the lobby. Zoya enjoys cycling on weekends. Meera is on leave for the whole of the sprint. Marco prefers to take the stairs instead of the lift.
> 
> Question: All 3 engineers will work on every day of the sprint. How many engineer-days of work will the Platform team deliver in the sprint?

Model reply to the perturbed version:

```
{"answer": "10 engineer-days", "caveats": "Meera is on leave for the whole 5-day sprint, leaving Isha and Anika to work 5 days each (2 engineers * 5 days = 10 engineer-days)."}
```

### Flaws the model most often missed (original versions)

**ad-0003-original** (abstract, contradictory_facts), caught in 0/1 runs

> Priya was born in 1984. Felix is 7 years older than Priya. Felix is 43 years old as of 2026. Leila is 49 years old as of 2026. Sana is 56 years old as of 2026.
> 
> Question: In 2031, how old will Felix be at the end of the year?

Planted flaw: Priya was born in 1984. / Felix is 7 years older than Priya. / Felix is 43 years old as of 2026.

Reply:

```
```json
{"answer": 48, "caveats": null}
```
```

**ad-0004-original** (abstract, contradictory_facts), caught in 0/1 runs

> Priya was born in 1994. Dev is 5 years older than Priya. Lena is 5 years older than Dev. Lena is 48 years old as of 2026. Sana is 21 years old as of 2026. Anika is 44 years old as of 2026. Ravi is 49 years old as of 2026. Kabir is 38 years old as of 2026.
> 
> Question: In 2030, how old will Lena be at the end of the year?

Planted flaw: Priya was born in 1994. / Dev is 5 years older than Priya. / Lena is 5 years older than Dev. / Lena is 48 years old as of 2026.

Reply:

```
```json
{"answer": "52", "caveats": "Lena is 48 in 2026, so she will be 52 at the end of 2030 (48 + 4)."}
```
```

**ad2-0003-original** (finance, contradictory_facts), caught in 0/1 runs

> Orbitra takes a loan of $500,000 at 9% annual interest, to be repaid in 36 equal monthly instalments (interest is charged monthly on the reducing balance). The monthly instalment on Orbitra's $500,000 loan is $9,540.
> 
> Question: Based on these figures, what is the total interest Orbitra pays over the life of the $500,000 loan?

Planted flaw: Orbitra takes a loan of $500,000 at 9% annual interest, to be repaid in 36 equal monthly instalments (interest is charged monthly on the reducing balance). / The monthly instalment on Orbitra's $500,000 loan is $9,540.

Reply:

```
```json
{"answer": "$334,440", "caveats": "Calculated as (36 monthly instalments * $9,540) - $500,000 principal."}
```
```

**ad2-0005-original** (project_planning, impossible_constraint), caught in 0/1 runs

> The Search team has 4 engineers. The search upgrade needs 2 engineers and the mobile release needs 3 engineers, each working full-time on that task. The search upgrade and the mobile release must run at the same time for 4 working days.
> 
> Question: In total, how many engineer-days do the search upgrade and the mobile release use during that period?

Planted flaw: The Search team has 4 engineers. / The search upgrade needs 2 engineers and the mobile release needs 3 engineers, each working full-time on that task.

Reply:

```
```json
{"answer": "20 engineer-days", "caveats": "This calculation is based solely on the resource requirements (2 for search, 3 for mobile) and the duration (4 days), resulting in (2 + 3) * 4 = 20 engineer-days, despite the team only having 4 engineers available."}
```
```

**ad2-0023-original** (compliance, contradictory_facts), caught in 0/1 runs

> Nordvale's policy: a data breach must be reported to the regulator within 60 calendar days of the date it was discovered. A breach at Nordvale occurred on 9 February 2026 and was discovered on 22 February 2026. The compliance calendar lists the reporting deadline as 60 days after the date the breach occurred.
> 
> Question: What is the deadline for reporting the breach to the regulator?

Planted flaw: Nordvale's policy: a data breach must be reported to the regulator within 60 calendar days of the date it was discovered. / The compliance calendar lists the reporting deadline as 60 days after the date the breach occurred.

Reply:

```
```json
{"answer": "April 10, 2026", "caveats": "Nordvale's official policy sets the deadline 60 calendar days from the date of discovery (22 February 2026), which would be April 23, 2026. However, the compliance calendar referenced in the scenario specifies the deadline as 60 days after the date the breach occurred (9 February 2026). Counting 60 calendar days from 9 February 2026 results in April
```

### False alarms on clean questions

**ad2-0075-surface** (compliance, surface)

> The audit of Kavira reported 1 findings. Zentra audited its vendors in 2026. Audit reports are shared with the board. Zoya leads the vendor compliance programme. The audit of Nordvale reported 4 findings and the audit of Marlow Labs reported 4 findings.
> 
> Question: The audit of Kavira in 2026 reported how many findings?

Reply:

```
```json
{"answer": "1", "caveats": "The scenario mentions that Zentra audited its vendors in 2026 and that the audit of Kavira reported 1 finding, but does not explicitly state the audit of Kavira occurred in 2026."}
```
```

## groq-gpt-oss-120b

### Caught the original, missed the perturbed version

**ad-0003** (abstract, contradictory_facts), perturbation: surface

Original question:

> Priya was born in 1984. Felix is 7 years older than Priya. Felix is 43 years old as of 2026. Leila is 49 years old as of 2026. Sana is 56 years old as of 2026.
> 
> Question: In 2031, how old will Felix be at the end of the year?

Perturbed question:

> Omar is 7 years older than Yash. Lena is 49 years old as of 2026. Yash was born in 1984. Arjun is 56 years old as of 2026. Omar is 43 years old as of 2026.
> 
> Question: What age will Omar reach by the end of 2031?

Model reply to the perturbed version:

```
{"answer": "48", "caveats": "Assumes Omar's age of 43 is measured at the end of 2026 and that each subsequent year adds exactly one year, ignoring exact birth dates within the years."}
```

**ad-0014** (abstract, hidden_dependency), perturbation: surface

Original question:

> The Platform team has 3 engineers: Meera, Isha, Anika. A sprint lasts 5 working days. Meera is on leave for the whole of the sprint.
> 
> Question: All 3 engineers will work on every day of the sprint. How many engineer-days of work will the Platform team deliver in the sprint?

Perturbed question:

> Kabir is on leave for the whole of the sprint. A sprint lasts 5 working days. The Search team has 3 engineers: Kabir, Ravi, Dev.
> 
> Question: Assuming every one of the 3 engineers works on all 5 days, how many engineer-days will the Search team deliver?

Model reply to the perturbed version:

```
{"answer": "10", "caveats": null}
```

**ad-0015** (abstract, hidden_dependency), perturbation: surface

Original question:

> The Security team has 4 engineers: Isha, Ravi, Nina, Leila. A sprint lasts 5 working days. Ravi is on leave for the whole of the sprint. The Search team has 7 engineers. Each engineer works 8 hours a day.
> 
> Question: All 4 engineers will work on every day of the sprint. How many engineer-days of work will the Security team deliver in the sprint?

Perturbed question:

> Hugo is on leave for the whole of the sprint. The Mobile team has 4 engineers: Kabir, Hugo, Arjun, Felix. Each engineer works 8 hours a day. A sprint lasts 5 working days. The Platform team has 7 engineers.
> 
> Question: Assuming every one of the 4 engineers works on all 5 days, how many engineer-days will the Mobile team deliver?

Model reply to the perturbed version:

```
{"answer": "20", "caveats": "The scenario mentions Hugo is on leave, which would normally reduce the total to 15 engineer-days. However, the question explicitly asks to assume all four engineers work all five days, so the calculation uses 4 engineers × 5 days = 20 engineer-days."}
```

### Flaws the model most often missed (original versions)

**ad-0004-original** (abstract, contradictory_facts), caught in 0/1 runs

> Priya was born in 1994. Dev is 5 years older than Priya. Lena is 5 years older than Dev. Lena is 48 years old as of 2026. Sana is 21 years old as of 2026. Anika is 44 years old as of 2026. Ravi is 49 years old as of 2026. Kabir is 38 years old as of 2026.
> 
> Question: In 2030, how old will Lena be at the end of the year?

Planted flaw: Priya was born in 1994. / Dev is 5 years older than Priya. / Lena is 5 years older than Dev. / Lena is 48 years old as of 2026.

Reply:

```
{"answer": "52", "caveats": "This answer assumes the statement 'Lena is 48 years old as of 2026' is correct and that her birthday occurs before the end of each year. The scenario contains inconsistent ages for some individuals, but the calculation follows the given age for Lena."}
```

**ad2-0010-original** (hr_operations, false_presupposition), caught in 0/1 runs

> Under Sunvane's leave policy, employees who joined before 1 January 2026 receive 20 days of annual leave in 2026. Employees who join during 2026 receive 20 days divided by 12 for each month of 2026 remaining, counting the month they join. Samir joined Sunvane on 1 August 2026. Samir has taken 4 days of annual leave so far in 2026.
> 
> Question: How many of Samir's 20 annual leave days for 2026 remain?

Planted flaw: Under Sunvane's leave policy, employees who joined before 1 January 2026 receive 20 days of annual leave in 2026. Employees who join during 2026 receive 20 days divided by 12 for each month of 2026 remaining, counting the month they join. / Samir joined Sunvane on 1 August 2026.

Reply:

```
{"answer": "Approximately 4.33 days of leave remain (8.33 days total entitlement minus the 4 days already taken).", "caveats": "This calculation assumes leave can be taken in fractional days and does not apply any rounding rules. If your company rounds leave to the nearest half‑day or whole day, the remaining balance may differ (e.g., 4.5 days if rounded to the nearest half‑day)."}
```

**ad2-0012-original** (hr_operations, false_presupposition), caught in 0/1 runs

> Sunvane's leave policy: unused annual leave cannot be carried over into the next year. Dev has 2 unused annual leave days at the end of 2026.
> 
> Question: How many of Dev's carried-over days must be used by 31 March 2027?

Planted flaw: Sunvane's leave policy: unused annual leave cannot be carried over into the next year.

Reply:

```
{"answer": "0", "caveats": "This assumes Sunvane's policy strictly prohibits any carry‑over of unused annual leave beyond the calendar year, with no grace period or special exceptions."}
```

**ad2-0035-original** (hr_operations, false_presupposition), caught in 0/1 runs

> Under Quillon's leave policy, employees who joined before 1 January 2026 receive 28 days of annual leave in 2026. Employees who join during 2026 receive 28 days divided by 12 for each month of 2026 remaining, counting the month they join. Omar joined Quillon on 1 April 2026. Omar has taken 2 days of annual leave so far in 2026. Leila joined Quillon on 1 January 2020. The leave year runs from 1 January to 31 December. Public holidays do not count against annual leave. Quillon has 7 offices.
> 
> Question: How many of Omar's 28 annual leave days for 2026 remain?

Planted flaw: Under Quillon's leave policy, employees who joined before 1 January 2026 receive 28 days of annual leave in 2026. Employees who join during 2026 receive 28 days divided by 12 for each month of 2026 remaining, counting the month they join. / Omar joined Quillon on 1 April 2026.

Reply:

```
{"answer": "19", "caveats": null}
```

**ad2-0049-original** (compliance, contradictory_facts), caught in 0/1 runs

> Pantora's Privacy Policy: customer records are deleted 24 months after the account is closed. Pantora's Finance Policy: customer records must be kept for 36 months after the account is closed. Yash closed their account with Pantora in July 2022. Hugo closed their account with Pantora in August 2022. Deleted records are logged for audit purposes. Customers are notified by email before deletion. Pantora has 5 regional offices.
> 
> Question: In which month and year must Yash's customer records be deleted?

Planted flaw: Pantora's Privacy Policy: customer records are deleted 24 months after the account is closed. / Pantora's Finance Policy: customer records must be kept for 36 months after the account is closed.

Reply:

```
{"answer": "July 2025", "caveats": "Assumes the Finance Policy's 36‑month retention requirement overrides the Privacy Policy's 24‑month rule, so records are kept for the longer period. If the organization interprets the policies differently (e.g., deletes after the shorter period and archives for finance), the date could change."}
```

### False alarms on clean questions

**ad2-0075-surface** (compliance, surface)

> The audit of Kavira reported 1 findings. Zentra audited its vendors in 2026. Audit reports are shared with the board. Zoya leads the vendor compliance programme. The audit of Nordvale reported 4 findings and the audit of Marlow Labs reported 4 findings.
> 
> Question: The audit of Kavira in 2026 reported how many findings?

Reply:

```
{"answer": "unknown", "caveats": "The scenario states the audit of Kavira reported 1 finding, but it does not specify the year of that audit. Therefore we cannot determine how many findings were reported in 2026."}
```

## groq-qwen3.8-27b

### Caught the original, missed the perturbed version

**ad-0003** (abstract, contradictory_facts), perturbation: distractor

Original question:

> Priya was born in 1984. Felix is 7 years older than Priya. Felix is 43 years old as of 2026. Leila is 49 years old as of 2026. Sana is 56 years old as of 2026.
> 
> Question: In 2031, how old will Felix be at the end of the year?

Perturbed question:

> Priya was born in 1984. Felix is 7 years older than Priya. Felix is 43 years old as of 2026. The building has a small rooftop garden. A new coffee machine was installed in the lobby. Leila is 49 years old as of 2026. The office kitchen was repainted last spring. Sana is 56 years old as of 2026.
> 
> Question: In 2031, how old will Felix be at the end of the year?

Model reply to the perturbed version:

```
{"answer": "48", "caveats": null}
```

**ad-0003** (abstract, contradictory_facts), perturbation: surface

Original question:

> Priya was born in 1984. Felix is 7 years older than Priya. Felix is 43 years old as of 2026. Leila is 49 years old as of 2026. Sana is 56 years old as of 2026.
> 
> Question: In 2031, how old will Felix be at the end of the year?

Perturbed question:

> Omar is 7 years older than Yash. Lena is 49 years old as of 2026. Yash was born in 1984. Arjun is 56 years old as of 2026. Omar is 43 years old as of 2026.
> 
> Question: What age will Omar reach by the end of 2031?

Model reply to the perturbed version:

```
{
"answer": "48",
"cave": "No caveats."
```

**ad-0014** (abstract, hidden_dependency), perturbation: surface

Original question:

> The Platform team has 3 engineers: Meera, Isha, Anika. A sprint lasts 5 working days. Meera is on leave for the whole of the sprint.
> 
> Question: All 3 engineers will work on every day of the sprint. How many engineer-days of work will the Platform team deliver in the sprint?

Perturbed question:

> Kabir is on leave for the whole of the sprint. A sprint lasts 5 working days. The Search team has 3 engineers: Kabir, Ravi, Dev.
> 
> Question: Assuming every one of the 3 engineers works on all 5 days, how many engineer-days will the Search team deliver?

Model reply to the perturbed version:

```
{"answer": "15", "caveats": null}
```

### Flaws the model most often missed (original versions)

**ad-0002-original** (abstract, contradictory_facts), caught in 0/1 runs

> Arjun was born in 1984. Arjun is 49 years old as of 2026.
> 
> Question: In 2032, how old will Arjun be at the end of the year?

Planted flaw: Arjun was born in 1984. / Arjun is 49 years old as of 2026.

Reply:

```
{"answer": "48", "caveats": null}
```

**ad-0004-original** (abstract, contradictory_facts), caught in 0/1 runs

> Priya was born in 1994. Dev is 5 years older than Priya. Lena is 5 years older than Dev. Lena is 48 years old as of 2026. Sana is 21 years old as of 2026. Anika is 44 years old as of 2026. Ravi is 49 years old as of 2026. Kabir is 38 years old as of 2026.
> 
> Question: In 2030, how old will Lena be at the end of the year?

Planted flaw: Priya was born in 1994. / Dev is 5 years older than Priya. / Lena is 5 years older than Dev. / Lena is 48 years old as of 2026.

Reply:

```
{"answer": "52", "caveats": "The calculation assumes 'as of 2026' implies the age is current within that year, so adding the difference in years (2030 - 2026) to the stated age yields the age at the end of 2030."}
```

**ad-0013-original** (abstract, hidden_dependency), caught in 0/1 runs

> The Mobile team has 3 engineers: Marco, Kabir, Ravi. A sprint lasts 10 working days. Ravi is on leave for the whole of the sprint.
> 
> Question: All 3 engineers will work on every day of the sprint. How many engineer-days of work will the Mobile team deliver in the sprint?

Planted flaw: The Mobile team has 3 engineers: Marco, Kabir, Ravi. / Ravi is on leave for the whole of the sprint.

Reply:

```
{"answer": "30", "caveats": null}
```

**ad-0015-original** (abstract, hidden_dependency), caught in 0/1 runs

> The Security team has 4 engineers: Isha, Ravi, Nina, Leila. A sprint lasts 5 working days. Ravi is on leave for the whole of the sprint. The Search team has 7 engineers. Each engineer works 8 hours a day.
> 
> Question: All 4 engineers will work on every day of the sprint. How many engineer-days of work will the Security team deliver in the sprint?

Planted flaw: The Security team has 4 engineers: Isha, Ravi, Nina, Leila. / Ravi is on leave for the whole of the sprint.

Reply:

```
{
"answer": "10",
"caveat": "The scenario text contains a contradiction: it states 'Ravi is on leave for the whole of the sprint' but the question prompt assumes 'All 4 engineers will work on every day of the sprint'. Based on the explicit instruction in the question prompt ('All 4 engineers...'), the calculation is 4 engineers × 5 days = 20? No, wait. The question asks how many engineer-days the 
```

**ad2-0001-original** (hr_operations, impossible_constraint), caught in 0/1 runs

> Nordvale's Payments team plans to hire 5 engineers. The recruiter closes 2 hires per month, starting in August, and each hire starts work in the month the offer is closed. The approved hiring budget for the Payments team covers 2 hires.
> 
> Question: In which month will all 5 engineers have started work?

Planted flaw: Nordvale's Payments team plans to hire 5 engineers. / The approved hiring budget for the Payments team covers 2 hires.

Reply:

```
{"answer": "December", "caveats": null}
```

### False alarms on clean questions

**ad2-0003-control** (finance, control)

> Orbitra takes a loan of $500,000 at 9% annual interest, to be repaid in 36 equal monthly instalments (interest is charged monthly on the reducing balance). The monthly instalment on Orbitra's $500,000 loan is $15,900.
> 
> Question: Based on these figures, what is the total interest Orbitra pays over the life of the $500,000 loan?

Reply:

```
{"answer": "70400", "caveats": "The total interest is calculated as the difference between the total amount paid (36 installments * $15,900 = $572,400) and the principal ($500,000). Note that there is a mathematical inconsistency in the provided scenario: a $500,000 loan at 9% annual interest (0.75% monthly) over 36 months would typically have a monthly payment closer to $15,700, not $15,900. Howe
```

**ad2-0019-control** (project_planning, control)

> Lena is assigned to three tasks: the reporting overhaul takes 20% of Lena's working time, the mobile release takes 20% and the security audit takes 25%. Lena works full-time and does nothing else besides these three tasks.
> 
> Question: What percentage of Lena's working time is left free?

Reply:

```
{"answer": "35", "caveats": "The text contains a logical contradiction stating that Lena does nothing else besides the three tasks which sum to 65% of her time, implying the remaining 35% is unaccounted for or she is not working at 100% capacity despite being described as full-time. The answer calculates the arithmetic difference between 100% and the sum of the specified task percentages (20% + 20
```

**ad2-0069-original** (project_planning, original)

> Zoya is assigned to three tasks: the mobile release takes 30% of Zoya's working time, the security audit takes 30% and the dashboard rebuild takes 15%. Zoya works full-time and does nothing else besides these three tasks. Tara is assigned to the mobile release as well. Zoya is a member of the Payments team.
> 
> Question: What percentage of Zoya's working time is left free?

Reply:

```
{
"caveats": "The scenario states that Zoya 'does nothing else besides these three tasks,' which contradicts the premise of having working time 'left free' unless 'left free' is interpreted as the unaccounted portion of time not explicitly assigned to the named tasks. Based on the arithmetic sum of the provided percentages, 25% is the residual amount.",
"answer": "25%"
}
```
