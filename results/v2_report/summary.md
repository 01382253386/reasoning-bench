# Results summary

Generated 2026-10-20 11:01 UTC. Proportions show a 95% Wilson interval in brackets; question counts are small, so intervals are wide.

Definitions: **sensitivity** = flagged a problem when there was one. **specificity** = did not flag when there was none. **balanced** = mean of the two. **gap** = balanced score on original questions minus balanced score on the perturbed version. **repaired twin** = same scenario with the flaw fixed. **complied anyway** = flagged the problem but still gave a confident answer. **named it** = the flagged problem matches the planted one (keyword match, approximate).

**Prompt style "plain"** (rows from runs with `--prompt-style plain`): the model is NOT told to look for problems. "Flagged" means it volunteered one. When a `.judged.jsonl` file from `runner/judge.py` sits next to the raw log, a judge model decided this (for flawed questions: did the reply name the planted flaw; for clean ones: did it wrongly claim a problem). Without it, a word-matching fallback is used, which undercounts. Judge verdicts are approximate; read the examples in failures.md.

Prompt style in this report: plain.

## Headline

| model | calls | failed calls | valid replies | sensitivity (original) | specificity (original) | balanced original | balanced surface | balanced distractor | gap surface | gap distractor | repaired twins correct | tokens per call | seconds per call | runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| groq-gpt-oss-120b | 265 | 0 | 100% | 90% [79-96] | 100% [83-100] | 95% | 85% | 94% | +10 pts | +1 pts | 100% [93-100] | 459 | 0.9 | 1 |

## How the models fail (all versions)

| model | missed the flaw | complied anyway | named it | false alarms on clean | clean answers correct |
|---|---|---|---|---|---|
| groq-gpt-oss-120b | 15% [11-22] | 98% [94-99] | 100% [97-100] | 1% [0-5] | 97% [92-99] |

## Run-to-run consistency

| model | runs | accuracy per run (mean ± std) | questions answered the same way in every run |
|---|---|---|---|
| groq-gpt-oss-120b | 1 | 90.6% ± 0.0 | n/a |

## By tier

| model | tier | sensitivity | specificity |
|---|---|---|---|
| groq-gpt-oss-120b | tier 1 | 90% [78-96] | 100% [86-100] |
| groq-gpt-oss-120b | tier 2 | 82% [74-88] | 99% [94-100] |

## By domain

| model | domain | sensitivity | specificity |
|---|---|---|---|
| groq-gpt-oss-120b | abstract | 90% [78-96] | 100% [86-100] |
| groq-gpt-oss-120b | compliance | 88% [69-96] | 96% [79-99] |
| groq-gpt-oss-120b | finance | 100% [88-100] | 100% [85-100] |
| groq-gpt-oss-120b | hr_operations | 61% [45-75] | 100% [85-100] |
| groq-gpt-oss-120b | project_planning | 89% [72-96] | 100% [85-100] |

## By flaw type (flawed items only counted for sensitivity)

| model | flaw type | sensitivity | specificity |
|---|---|---|---|
| groq-gpt-oss-120b | clean_control | n/a | 98% [91-100] |
| groq-gpt-oss-120b | contradictory_facts | 85% [69-93] | 100% [74-100] |
| groq-gpt-oss-120b | false_presupposition | 75% [59-86] | 100% [76-100] |
| groq-gpt-oss-120b | hidden_dependency | 73% [48-89] | 100% [57-100] |
| groq-gpt-oss-120b | impossible_constraint | 79% [60-91] | 100% [68-100] |
| groq-gpt-oss-120b | missing_info | 98% [89-100] | 100% [81-100] |

## Notes and limitations

- Sensitivity and specificity use code-checked labels, so they do not depend on opinion.
- "Named it" is a keyword match and only approximates whether the model identified the right problem.
- Question counts per cell are small; treat differences inside the intervals as noise.
- Scores depend on the prompt format. The exact prompts and replies are in the raw logs (kept local) and the question files.
