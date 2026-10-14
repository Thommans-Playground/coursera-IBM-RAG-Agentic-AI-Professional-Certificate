# module1

This project uses a ports-and-adapters boundary for text generation:

- `module1.ports.TextGenerationPort` is the application-facing port.
- `module1.adapters.WatsonxTextGenerationAdapter` is the current IBM
  watsonx.ai connector used by the notebook.
- `module1.adapters.OpenAITextGenerationAdapter` is an alternative OpenAI
  connector.
- `module1.factory.create_text_generator` selects an adapter without changing
  application code.

The default provider is `watsonx`:

```sh
export LLM_PROVIDER=watsonx
export WATSONX_PROJECT_ID=your-project-id
export WATSONX_API_KEY=your-api-key
uv run python -c "from module1.factory import create_text_generator; print(create_text_generator().generate('The wind is'))"
```

To use OpenAI instead:

```sh
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4o-mini
uv run python -c "from module1.factory import create_text_generator; print(create_text_generator().generate('The wind is'))"
```

Application code depends only on the port:

```python
from module1.factory import create_text_generator

generator = create_text_generator()
answer = generator.generate("The wind is ")
```