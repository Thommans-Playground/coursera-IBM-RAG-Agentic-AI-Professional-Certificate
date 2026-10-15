# Prompting Examples

Run each prompt in a notebook cell with `llm.generate(prompt, GenerationSettings(...))` and compare the outputs.

## Basic (continuation)

```text
The best thing about learning to code is
```

## Zero-shot (instruction only)

```text
Classify this review as positive or negative: "The battery died after two days."
```

## One-shot (one example)

```text
Convert to a polite request.
Input: "Send me the report."
Output: "Could you please send me the report?"

Input: "Fix the bug."
Output:
```

## Few-shot (several examples)

```text
Sentence: "I loved the food." → Positive
Sentence: "The service was awful." → Negative
Sentence: "It was fine, nothing special." → Neutral

Sentence: "The room was spotless and the staff were lovely." →
```

## Chain-of-thought

```text
A train leaves at 2:15 pm and the trip takes 3 hours 50 minutes.
When does it arrive? Work through it step by step.
```

## Role prompt

```text
You are a patient maths teacher talking to a 10-year-old.
Explain what a fraction is in three sentences.
```

## Format control

```text
List three benefits of exercise as a JSON array of strings. Output only the JSON.
```

## Constraint prompt

```text
Explain what an API is in exactly two sentences, without using the word "interface".
```

## Experiment

Run the same prompt at `temperature=0.0` and again at `temperature=1.0`. Classification prompts change little. Creative prompts change a lot.
