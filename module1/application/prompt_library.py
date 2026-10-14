from langchain_core.prompts import PromptTemplate

SUMMARIZE = PromptTemplate.from_template("Summarize the {content} in one sentence.")

ANSWER = PromptTemplate.from_template(
    "Answer the {question} based on the {content}.\n"
    'Respond "Unsure about answer" if not sure about the answer.\n\n'
    "Answer:"
)

CLASSIFY = PromptTemplate.from_template(
    "Classify the {text} into one of the {categories}.\n\nCategory:"
)

REVIEW = PromptTemplate.from_template(
    'Analyze the following product review:\n"{review}"\n\n'
    "Provide your analysis in the following format:\n"
    "- Sentiment: (positive, negative, or neutral)\n"
    "- Key Features Mentioned: (list the product features mentioned)\n"
    "- Summary: (one-sentence summary)"
)
