# Track Spec: <ability name>

## 1. Definition
One paragraph: what ability is being measured, in plain words. What is explicitly NOT being measured?

## 2. Task format
- Input given to the model (exact structure)
- Output expected from the model (exact structure, so it can be parsed)

## 3. Question types / subtypes
List each subtype with a one-line example.

## 4. Ground truth
How is the correct answer defined and checked **by code**? If code cannot check it, say why and how human review works (two independent reviewers, disagreement rule).

## 5. Difficulty levels
What changes between easy / medium / hard? (number of steps, number of distractors, depth of nesting)

## 6. Perturbations
- **Surface:** rename entities, reorder facts, change wording. The answer must not change.
- **Distractor:** add irrelevant but plausible details. The answer must not change.
- **Control (if applicable):** a version where the correct answer is different, to catch models that always give the same response.

## 7. Scoring
- Primary metric
- Secondary metrics
- Partial credit rules

## 8. Known failure modes to look for
What wrong behaviours do you expect, and how will they show up in the logs?

## 9. Validity threats
Ways a model could score well without having the ability (shortcuts, pattern matching, contamination).

## 10. Size and split
Number of items per difficulty, public vs private split.

## 11. Item schema
JSON fields for one item.
