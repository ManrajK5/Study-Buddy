import tempfile
from pathlib import Path

import pdfplumber
from langchain_community.document_loaders import PyPDFLoader


class PdfTextExtractor:
    async def extract_pages(self, file_bytes: bytes, file_name: str) -> list[dict]:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_path = Path(temp_file.name)

        try:
            loader = PyPDFLoader(str(temp_path))
            docs = loader.load()
            if docs:
                return [
                    {
                        "content": doc.page_content,
                        "page_number": doc.metadata.get("page"),
                        "source": file_name,
                    }
                    for doc in docs
                ]
            return self._extract_with_pdfplumber(temp_path, file_name)
        finally:
            temp_path.unlink(missing_ok=True)

    def _extract_with_pdfplumber(self, path: Path, file_name: str) -> list[dict]:
        pages: list[dict] = []
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                pages.append({"content": page.extract_text() or "", "page_number": index, "source": file_name})
        return pages
