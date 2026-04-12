import io
import base64
from typing import List, Dict, Any
from PIL import Image as PILImage
from docx import Document as DocxDoc

from ._reader_base import BaseReader


class WordReader(BaseReader):
    """Extract text and images from DOCX files."""

    def extract_text(self) -> str:
        """Extract all text from DOCX."""
        try:
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(self.file_path)
            documents = loader.load()
            return "\n".join(doc.page_content for doc in documents)
        except Exception as e:
            print(f"[WORD READER] Error extracting text: {e}")
            return ""

    def extract_images(self) -> List[Dict[str, Any]]:
        """Extract images from DOCX."""
        images = []
        try:
            doc = DocxDoc(self.file_path)

            for idx, rel in enumerate(doc.part.rels.values()):
                if "image" not in rel.reltype:
                    continue

                try:
                    img = PILImage.open(io.BytesIO(rel.target_part.blob))

                    # Skip small images
                    if img.width < 50 or img.height < 50:
                        continue

                    buf = io.BytesIO()
                    fmt = img.format or "PNG"
                    img.save(buf, format=fmt)
                    b64 = base64.b64encode(buf.getvalue()).decode()

                    images.append({
                        "index": idx,
                        "page": None,
                        "width": img.width,
                        "height": img.height,
                        "format": fmt,
                        "data": f"data:image/{fmt.lower()};base64,{b64}",
                    })

                except Exception as e:
                    print(f"[WORD READER] Skip image {idx}: {e}")

        except Exception as e:
            print(f"[WORD READER] Error extracting images: {e}")

        return images
