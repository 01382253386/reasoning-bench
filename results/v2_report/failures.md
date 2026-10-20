# Failure examples

Concrete cases taken from the logs. Replies are shortened to 400 characters.

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
