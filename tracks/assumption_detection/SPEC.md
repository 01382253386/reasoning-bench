# Track Spec: Assumption Detection

## 1. Definition
Measures whether a model notices a **hidden, false, or unsupported premise** inside a question, and says so, instead of answering as if the premise were true.

Not measured: general knowledge, whether the model refuses appropriately, or whether it is polite about it.

## 2. Task format
**Input:** a short scenario plus a question. Some items contain a flawed premise; some are clean controls with no flaw.

**Required output (JSON, so it can be parsed):**
```json
{
  "premise_problem": true,
  "flawed_premise": "one sentence naming the problem, or null",
  "answer": "the model's answer, or null if the question cannot be answered"
}
```

## 3. Question subtypes
| Subtype | Example |
|---|---|
| Contradictory facts | "Ravi is 30 and was born in 1990. In 2026, how old is he?" Stated age conflicts with the birth year. |
| False presupposition | "When did the 2019 company merger happen?" The scenario says no merger took place. |
| Missing required info | "A train leaves at 2 pm at 60 km/h. When does it arrive?" Distance is not given. |
| Hidden dependency | "The plan needs the 3 engineers to finish by Friday." Earlier facts say one engineer is on leave. |
| Impossible constraint | "Pick 3 numbers from {2, 4, 6} that sum to an odd number." |
| Clean control | Same format and same surface features, but no flawed premise. A correct answer exists. |

## 4. Ground truth
Every item is produced by a generator that **knows which premise it broke**. The item stores:
- `has_flaw` (true/false)
- `flaw_type` (subtype)
- `flaw_fact_ids` (which stated facts conflict or are missing)
- `correct_answer` (for controls, computed by code)

Answers are checked by code. Detection is a boolean match. Flaw identification is checked by matching the model's `flawed_premise` text against the stored fact IDs, with a rubric fallback (see Scoring). A 10% random sample of items gets independent human review, with the disagreement rule: if two reviewers disagree, the item is removed.

## 5. Difficulty levels
- **Easy:** flaw is explicit, 2-3 facts, one conflict.
- **Medium:** flaw requires combining 4-6 facts or a small calculation to surface.
- **Hard:** flaw is implied across 7+ facts with distractors, or is a missing dependency rather than a direct conflict.

## 6. Perturbations
- **Surface:** rename people/places/units, reorder facts, rephrase. The flaw stays the same.
- **Distractor:** add 2-4 irrelevant but plausible sentences. The flaw stays the same.
- **Control pair:** every flawed item has a repaired twin where the flaw is fixed. This catches models that flag everything.

## 7. Scoring
Reported separately, never blended into one number:
1. **Detection accuracy:** flagged when flawed, did not flag when clean.
2. **False-alarm rate:** flagged on clean controls.
3. **Identification accuracy:** among correctly flagged items, named the right premise.
4. **Complied-anyway rate:** flagged the problem but still gave a confident answer built on the false premise.
5. **Robustness gap:** detection on original minus detection on surface-perturbed and distractor versions.

Identification is scored by code match on key terms from the stored facts; ambiguous cases go to a fixed rubric (0 / 0.5 / 1) applied by a strong-model judge, with 20% of judged items checked by hand.

## 8. Known failure modes to look for
- Answers confidently without noticing the flaw.
- Notices the flaw but answers anyway.
- Flags every question (high false-alarm rate).
- Detects flaws in easy items but loses them when distractors are added.
- Names a different flaw than the one planted.

## 9. Validity threats
- **Template tells:** if flawed items share wording patterns, models can learn the pattern. Mitigation: multiple templates per subtype, shuffled phrasing, and clean controls with the same wording.
- **Flag-everything strategy:** controlled by false-alarm rate.
- **Unintended flaws:** a "clean" control may contain a real flaw. Mitigation: code-solve every control and human-review a sample.
- **Contamination:** private held-out set, never published.

## 10. Size and split
**Tier 1 (controlled puzzles):** 24 base questions (5 flawed subtypes x 4 difficulty levels, plus 4 clean controls). Each flawed base question has 4 versions (original, surface, distractor, repaired control); each clean one has 3. Total 92 items.

**Tier 2 (realistic business scenarios):** 27 base questions across 4 domains (HR operations, finance, project planning, compliance): 9 scenario templates x easy and hard flawed versions, plus one clean control per template. Total 99 items.

In both tiers about 30% of base questions are held out as a private set (`data/private/`, git-ignored, never uploaded) and 70% are published (`data/public/`). All versions of one base question always stay in the same split.

## 11. Item schema
```json
{
  "id": "ad-0001",
  "track": "assumption_detection",
  "version": "original | surface | distractor | control",
  "base_id": "ad-0001",
  "subtype": "contradictory_facts",
  "difficulty": "easy",
  "prompt": "...",
  "has_flaw": true,
  "flaw_fact_ids": ["f2", "f4"],
  "correct_answer": null,
  "split": "public | private",
  "generator": "generators/assumption_detection.py",
  "seed": 1234
}
```

## 12. Tier 2: realistic business scenarios
Tier 2 keeps everything above (same output format, same scoring, same perturbations) but replaces the abstract puzzles with scenarios that read like business documents. It is generated by `generators/assumption_detection_domain.py` and written to `data/*/assumption_detection_domain.jsonl`.

| Domain | Scenario (flaw type) |
|---|---|
| HR operations | Hiring plan exceeds the approved budget (impossible constraint) |
| HR operations | Leave question assumes an entitlement the policy does not give (false presupposition) |
| Finance | Stated loan instalment does not match the loan terms (contradictory facts) |
| Finance | Loan total requested, interest rate missing (missing info) |
| Project planning | Concurrent tasks need more engineers than the team has (impossible constraint) |
| Project planning | Tasks assumed parallel, but one depends on the other (hidden dependency) |
| Compliance | Two policy clauses overlap and conflict (contradictory facts) |
| Compliance | Deletion date requested for an account that is still open (false presupposition) |
| Compliance | Training deadline requested, start date missing (missing info) |

Additional Tier 2 rules:
- **Decoy facts.** Hard versions add plausible but irrelevant facts, such as another employee's closure date or a deposit rate that is not the loan rate, to test whether the model uses the right fact.
- **Answer formats.** Numeric answers allow a small tolerance where rounding is possible (loan interest, 1%); policy-conflict items require one of two exact phrases; date and month answers are matched by month name and day or year.
- **Scope.** Tier 2 tests whether a model catches inconsistencies in business documents and plans. It does not involve judging candidates or people.
- **Verification.** Every answer key and flaw label is recomputed by a separate code path at generation time, and a human reviews a sample for realism and fairness.
