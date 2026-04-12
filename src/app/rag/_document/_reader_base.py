from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseReader(ABC):
    """Base class for document readers."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def extract_text(self) -> str:
        """Extract all text from document."""
        pass

    @abstractmethod
    def extract_images(self) -> List[Dict[str, Any]]:
        """
        Extract images from document.

        Returns:
            List of image dicts with keys:
            - index: int
            - page: int or None
            - width: int
            - height: int
            - format: str (PNG, JPEG, etc)
            - data: str (data URI or base64)
        """
        pass
