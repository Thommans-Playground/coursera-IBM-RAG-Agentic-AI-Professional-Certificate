from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


class MarkdownSplitter:
    def __init__(self) -> None:
        # Markdown-aware: prefers to cut at headings and paragraphs, not mid-sentence.
        self.splitter = RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=1000, chunk_overlap=150)

    def split(self, text: str) -> list[str]:
        return [d.page_content for d in self.splitter.create_documents([text])]
