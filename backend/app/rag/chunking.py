from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int | None
    chunk_index: int
    metadata: dict


class DocumentChunker:
    def split_pages(self, pages: list[dict]) -> list[TextChunk]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks: list[TextChunk] = []
        for page in pages:
            for text in splitter.split_text(page["content"]):
                chunks.append(
                    TextChunk(
                        content=text,
                        page_number=page.get("page_number"),
                        chunk_index=len(chunks),
                        metadata={"source": page.get("source"), "page_number": page.get("page_number")},
                    )
                )
        return chunks
