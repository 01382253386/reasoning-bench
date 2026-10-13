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
Target v0.1: **24 base items** x 3 versions (original, surface, distractor) = 72 items, plus 24 repaired controls. Split 70% public (`data/public/`), 30% private (`data/private/`, git-ignored).

Per base item: 6 subtypes x 4 items (easy, easy, medium, hard).

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
