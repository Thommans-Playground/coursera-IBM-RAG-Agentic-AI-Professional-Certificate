---
name: transcript-tutorial
description: Turn a course video transcript (pasted, or from a file) into a clean, concept-by-concept follow-along tutorial saved as a markdown file with mermaid diagrams and small typeable code steps. Use this whenever the user pastes a transcript or lecture/video text from the Coursera IBM RAG and Agentic AI course, says "process this transcript", "make a tutorial", "break this into concepts", "I have another set for module N", or wants study material they can type along with and ask questions about, even if they don't say the word "skill" or "tutorial".
---

# Transcript to follow-along tutorial

The reader is a learner using this repo as a study tool. They will **type the code themselves** while reading, then ask you questions. So the tutorial must be easy to follow one small step at a time, and every snippet must actually run. A tutorial with code that fails on the first paste loses the reader's trust.

## Inputs to settle first

- **The transcript**: pasted text, or a file path. Read the whole thing before writing.
- **Target module**: `moduleN/` (ask only if it is not obvious from the conversation).
- **Topic name**: a short slug from the transcript's main idea, for example `lcel-chaining`.

Do not ask more than that. Pick sensible defaults and say what you picked.

## Steps

### 1. Clean the transcript

Transcripts from the course page carry noise and speech-to-text mistakes. Remove UI text (XP lines, "Interactive Transcript", keyboard-shortcut instructions). Fix obvious mishearings by meaning, and keep a short list of the fixes to show the user, because they are learning and may copy the wrong term. Examples seen so far: "View Shot Prompt Template" is "Few-shot Prompt Template"; "Panda DataFrames" is "Pandas DataFrames"; "Examples of Efficient Prompts" is most likely the length-based selector. Only fix when confident. When unsure, keep the term and flag it.

### 2. Break it into concepts

Find the distinct ideas, one per section, ordered so each builds on the previous one (a concept should never use a term not yet explained). Typical size is 3 to 7 concepts. Merge fragments, and drop filler such as "let's recap" and "welcome to this video". The video's own learning objectives are a good checklist for what must be covered.

### 3. Write the tutorial

Save to `moduleN/tutorials/<NN>-<slug>.md`, where NN continues the numbering of existing files in that folder (01 if none). Use this shape:

```
# <Title>
> What you will be able to do after this (the video's objectives, in plain words)
## Before you start        (setup pointer + the one-time llm cell)
## Concept 1: <name>
   - The idea            2 to 4 plain sentences plus an everyday analogy
   - Diagram             one small mermaid diagram
   - Type this           code in small steps, one idea per block
   - Expected output     what they should see, labelled as an example since LLM text varies
   - Try it              one small change to make, so they learn by poking
   - Check yourself      one question; answer in a <details> block
## Concept 2 ...
## Putting it together   a short example combining the concepts
## Common mistakes       errors a beginner will realistically hit, with fixes
## Cheat sheet           a table
## Practice               3 to 5 exercises, no answers shown, so the user can ask you
```

Writing rules, and why:
- **Simple language, short sentences.** The reader wants low friction. Define a term the first time it appears.
- **Small code blocks (under about 15 lines), built up in order.** They type it by hand, so long dumps cause typos and skipped understanding. Start with the smallest working version, then add one thing at a time.
- **Teach what the video taught, in its order.** Anything you add beyond the video (modern API notes, extra examples) goes under a "Beyond the video" label so the reader knows what the course covers and what is extra.
- **Comments in code explain why, not what.**

### 4. Code conventions for this repo

- Use the repo's stack: the shared root `.venv`, OpenAI via `ChatOpenAI(model="gpt-4o-mini")`, and `OPENAI_API_KEY` from the root `.env`. The setup cell is in `module2/README.md` ("Run the examples yourself"); link to it rather than copying it, except for a minimal version in "Before you start".
- The course uses IBM watsonx.ai. Keep the concept identical and show the watsonx model line as a comparison, since the transcript is about watsonx.
- Prefer current LangChain 1.x idioms (LCEL `prompt | llm | parser`). The course sometimes shows removed or deprecated classes such as `LLMChain`, `SequentialChain` and `ChatMessageHistory`. Show the modern equivalent and say why the video differs. Check what is installed first with `uv pip list` and confirm an import exists before using it.
- If a snippet needs a package that is not installed, say `uv add <pkg>` (at the repo root) in the text. Do not edit `pyproject.toml` yourself.

### 5. Mermaid rules

One small diagram per concept, showing the mechanism (data flow, sequence of calls), not decoration. Keep labels short. Wrap labels containing punctuation in double quotes. Do not put `|`, parentheses or braces inside edge labels. Use `flowchart LR` for pipelines and `sequenceDiagram` for conversations.

### 6. Verify before saving

Run the checker, which extracts every python block, swaps `ChatOpenAI` for a fake model, and executes the blocks in order in one namespace:

```
uv run python .claude/skills/transcript-tutorial/scripts/check_snippets.py moduleN/tutorials/<file>.md
```

It checks structure and wiring, not real model output, so say that in your report. A block that needs a missing package or real credentials can opt out by starting with the comment `# needs:` (it will be skipped and listed). Fix every failure before telling the user it is done. Do not call the real API unless the user asks, since it costs money.

### 7. Report

Tell the user: the file path, the list of concepts, any transcript corrections, anything labelled "Beyond the video", and what the check did and did not prove. Offer to link the tutorial from the module README.

## After the tutorial: study mode

The user will type along and ask questions. Answer from the tutorial file, name the concept section the answer lives in, and keep answers short. When they paste an error, ask for the code and traceback, find the cause, and explain it in one or two sentences before showing a fix. When they ask for the answer to a Practice exercise, give a hint first, and the full solution only if they ask again.
