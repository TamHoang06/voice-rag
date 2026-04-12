import io
import base64
from typing import List, Dict, Any
from PIL import Image as PILImage
import pypdf

from ._reader_base import BaseReader


class PDFReader(BaseReader):
    """Extract text and images from PDF files."""

    def extract_text(self) -> str:
        """Extract all text from PDF."""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(self.file_path)
            documents = loader.load()
            return "\n".join(doc.page_content for doc in documents)
        except Exception as e:
            print(f"[PDF READER] Error extracting text: {e}")
            return ""

    def extract_images(self) -> List[Dict[str, Any]]:
        """Extract images from PDF."""
        images = []
        try:
            reader = pypdf.PdfReader(self.file_path)
            idx = 0

            for page_num, page in enumerate(reader.pages):
                xobjects = (page.get("/Resources") or {}).get("/XObject")
                if not xobjects:
                    continue

                if hasattr(xobjects, "get_object"):
                    xobjects = xobjects.get_object()

                for _, obj in xobjects.items():
                    if hasattr(obj, "get_object"):
                        obj = obj.get_object()

                    if obj.get("/Subtype") != "/Image":
                        continue

                    try:
                        w = int(obj.get("/Width", 0))
                        h = int(obj.get("/Height", 0))

                        # Skip small images
                        if w < 50 or h < 50:
                            continue

                        mode = "L" if "/DeviceGray" in str(obj.get("/ColorSpace", "")) else "RGB"
                        img = PILImage.frombytes(mode, (w, h), obj.get_data())

                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        b64 = base64.b64encode(buf.getvalue()).decode()

                        images.append({
                            "index": idx,
                            "page": page_num + 1,
                            "width": w,
                            "height": h,
                            "format": "PNG",
                            "data": f"data:image/png;base64,{b64}",
                        })
                        idx += 1

                    except Exception as e:
                        print(f"[PDF READER] Skip image page {page_num + 1}: {e}")

        except Exception as e:
            print(f"[PDF READER] Error extracting images: {e}")

        return images
