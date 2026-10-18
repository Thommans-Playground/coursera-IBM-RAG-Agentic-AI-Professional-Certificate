---
name: transcript-tutorial
description: Turn course material (a video transcript, a lab notebook .ipynb, or both) into clean, concept-by-concept follow-along tutorials saved as markdown files with mermaid diagrams and small typeable code steps, verified to run. Use this whenever the user pastes a transcript or lecture text, adds a lab notebook to a module folder, mentions the Coursera IBM RAG and Agentic AI course, says "process this transcript", "make a tutorial", "follow along", "break this into concepts", "I have another set for module N", or wants study material they can type along with and ask questions about, even if they don't say the word "skill" or "tutorial".
---

# Course material to follow-along tutorials

The reader is a learner using this repo as a study tool. They will **type the code themselves** while reading, then ask you questions. So the tutorial must be easy to follow one small step at a time, and every snippet must actually run. A tutorial with code that fails on the first paste loses the reader's trust.

## Inputs to settle first

- **The material**: a pasted transcript, a file path, or a lab notebook in the module folder. Read all of it before writing. For a notebook, dump a compact view first (markdown cells shortened, code cells in full, outputs trimmed) into the scratchpad directory and read that, because raw `.ipynb` JSON is huge. A big lab can be 200+ cells.
- **Target module**: `moduleN/` (ask only if it is not obvious from the conversation).
- **Topic name**: a short slug from the main idea, for example `lcel-chaining`.
- **Which flavour(s)** (see next section). If the user does not say, make both for a lab notebook and the single "adapted" flavour for a short transcript.

Do not ask more than that. Pick sensible defaults and say what you picked.

## Two flavours of tutorial

| Flavour | When | Shape |
|---|---|---|
| **Adapted** (`NN-<slug>-adapted.md`) | The user wants to follow the course itself | Same order and concepts as the transcript or lab, modernised. Lab exercises become practice tasks with no answers. |
| **Project** (`NN-<slug>-build-<app>.md`) | The user wants the best way to understand, or the material is a catalogue of components | One small app grown step by step. Every step opens with **The problem** you just hit, then **The fix** (the concept). Use a corpus the learner already owns (the module README) so there is no download, and so they can ask it things they study. |

Why the project flavour: a catalogue of parts is hard to remember because the learner never feels why a part exists. A problem-first ladder makes each concept earn its place (for example: memory appears because the bot just forgot the user's name). Each project step uses: The problem, The fix, Type this, What you should see, Why it works, Try it, plus a mermaid diagram. End with a whole-app diagram, a common-mistakes table, practice and a cheat sheet.

Cross-link the two tutorials at the top and bottom, and add a short "Hands-on tutorials" section to the module README.

## Web app tutorials (the standard shape)

When the tutorial builds a web app (a frontend plus a backend, for example Next.js with FastAPI), use this shape every time. The reader should always have a working app and always know what to type next.

1. **Start from a hello world.** Stage 0 is one backend endpoint and one page that shows its message. Then a chat or form that echoes. Only then add the real feature. Every stage runs on its own.
2. **One idea per stage, problem first.** Each stage opens with the problem the reader just hit, then the fix. Add each technology (a database, a vector store, Redis, Celery) only at the stage whose problem needs it, and say why it is needed there.
3. **Real services, no fakes.** Use the real database, queue and model API. Do not teach or ship fake models, fake Redis or mocks. Test with a live test against the running stack (`test_live.py`), and make its assertions check facts that must hold, not exact LLM wording.
4. **Finish with Docker, built step by step.** The last stage builds the `Dockerfile` for each service and `docker-compose.yml` piece by piece, explaining each line. Standard practice: pinned dependencies, layer caching (install before copying code), non-root user, health checks, `depends_on` with `service_healthy`, a named volume for data, secrets from `.env` with a fail-fast message, a fixed compose `name:` so apps do not share volumes, and a note that `NEXT_PUBLIC_*` values are baked in at build time.
5. **Ship a finished copy** in an `app/` folder next to the tutorials, with a README that has the Docker one-liner, a no-Docker path, and the live test command.
6. **Verify for real.** Rebuild the app from the tutorial's own code blocks into a scratch folder (mark file blocks `# needs: ... (file: NAME)` or `(file: NAME, append)` so they can be assembled), start the real services, and run the live test against that rebuild. Also compare the tutorial's frontend blocks with the real files. Run the Docker build too and check health and a real request.

Concept-only tutorials (a study guide, or notebook-style code) keep the shapes in the next section. This standard is for tutorials that build an app.

## Steps

### 1. Clean the transcript

Transcripts from the course page carry noise and speech-to-text mistakes. Remove UI text (XP lines, "Interactive Transcript", keyboard-shortcut instructions). Fix obvious mishearings by meaning, and keep a short list of the fixes to show the user, because they are learning and may copy the wrong term. Examples seen so far: "View Shot Prompt Template" is "Few-shot Prompt Template"; "Panda DataFrames" is "Pandas DataFrames"; "Examples of Efficient Prompts" is most likely the length-based selector. Only fix when confident. When unsure, keep the term and flag it.

### 2. Break it into concepts

Find the distinct ideas, one per section, ordered so each builds on the previous one (a concept should never use a term not yet explained). Typical size is 3 to 7 concepts. Merge fragments, and drop filler such as "let's recap" and "welcome to this video". The video's own learning objectives are a good checklist for what must be covered.

### 3. Write the tutorial

Save to `moduleN/tutorials/<NN>-<slug>.md`, where NN continues the numbering of existing files in that folder (01 if none). The shape below is for the adapted flavour; the project flavour replaces each concept section with the problem-first step described above.

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
- **Show where the course and today differ.** When the course code uses a removed or legacy API, keep the course's concept and add a note in the exact form `> **Lab says / today we use:** ...` so the learner can map the original notebook to what they type. Also flag course quirks that would mislead (for example a demo setting that truncates embeddings to 3 tokens) and say why you did not copy them.
- **Teach what the video taught, in its order.** Anything you add beyond the video (modern API notes, extra examples) goes under a "Beyond the video" label so the reader knows what the course covers and what is extra.
- **Comments in code explain why, not what.**

### 4. Code conventions for this repo

- Use the repo's stack: the shared root `.venv`, OpenAI via `ChatOpenAI(model="gpt-4o-mini")`, and `OPENAI_API_KEY` from the root `.env`. The setup cell is in `module2/README.md` ("Run the examples yourself"); link to it rather than copying it, except for a minimal version in "Before you start".
- The course uses IBM watsonx.ai. Keep the concept identical and show the watsonx model line as a comparison, since the transcript is about watsonx.
- Prefer current LangChain 1.x idioms (LCEL `prompt | llm | parser`). The course sometimes shows removed or deprecated classes such as `LLMChain`, `SequentialChain` and `ChatMessageHistory`. Show the modern equivalent and say why the video differs. Check what is installed first with `uv pip list` and confirm an import exists before using it.
- Prefer what is already installed (for example `InMemoryVectorStore` over Chroma, `DeterministicFakeEmbedding` in checks). If a lab truly needs more packages (loaders, splitters, `langchain`), run `uv add` at the repo root, since runnable code is the point, and tell the user exactly what changed in `pyproject.toml`. For a package used only by an optional extra, do not install it. Mark that block `# needs: <pkg>` and put the `uv add` line in the text.
- Prefer a hand-built version over a removed class when the idea is small (for example a parent-document retriever in about 15 lines): the learner sees what it does.
- Probe unfamiliar APIs in a throwaway script first (imports, signatures, a real loader call) before writing them into a tutorial.

### 5. Mermaid rules

One small diagram per concept, showing the mechanism (data flow, sequence of calls), not decoration. Keep labels short. Wrap labels containing punctuation in double quotes. Do not put `|`, parentheses or braces inside edge labels. Use `flowchart LR` for pipelines and `sequenceDiagram` for conversations.

### 6. Verify before saving

Run the checker, which extracts every python block, swaps `ChatOpenAI` for a fake model, and executes the blocks in order in one namespace:

```
uv run python .claude/skills/transcript-tutorial/scripts/check_snippets.py moduleN/tutorials/<file>.md
```

It fakes the chat model (including tool calls, so agents run) and `OpenAIEmbeddings`, while document loaders run for real (free; needs network). It checks structure and wiring, not real model output, so say that in your report. A block that needs a missing package or real credentials can opt out by starting with the comment `# needs:` (it will be skipped and listed). Fix every failure before telling the user it is done. Do not call the real API unless the user asks, since it costs money.

### 7. Report

Tell the user: the file path(s), the list of concepts, any transcript or lab corrections, packages added, anything labelled "Beyond the video", and what the check did and did not prove. Offer to link the tutorial from the module README.

## After the tutorial: study mode

The user will type along and ask questions. Answer from the tutorial file, name the concept section the answer lives in, and keep answers short. When they paste an error, ask for the code and traceback, find the cause, and explain it in one or two sentences before showing a fix. When they ask for the answer to a Practice exercise, give a hint first, and the full solution only if they ask again.
