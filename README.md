# IBM RAG and Agentic AI Professional Certificate

Study notes and code for the Coursera IBM RAG and Agentic AI Professional Certificate.

| Module | Topic | Start here |
|---|---|---|
| module1 | Prompting, in-context learning, prompt templates | [module1/README.md](module1/README.md) |
| module2 | LangChain core concepts, chains, memory, agents | [module2/README.md](module2/README.md) |

## Setup (once, for all modules)

All modules share one Python environment at the repo root. You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync                      # creates .venv and installs everything
cp .env.example .env         # then add your keys (see below)
```

Create `.env` at the repo root. It is gitignored:

```text
OPENAI_API_KEY=your-key
```

### Running notebooks

1. Open a notebook in VS Code.
2. Select the root `.venv` (`ibm-rag-agentic-ai`) as the kernel.
3. Notebooks run with their own module folder as the working directory, so imports like `from adapters...` resolve.

### Running scripts

```sh
cd module1
uv run python your_script.py
```

### Adding a package or a new module

```sh
uv add <package>             # run at the repo root, shared by all modules
mkdir module3                # new modules need no extra install
```
