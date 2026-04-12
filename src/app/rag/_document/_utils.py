from typing import Dict, List, Any
import os


def get_reader(file_path: str):
    """
    Get appropriate reader based on file extension.

    Args:
        file_path: Path to document

    Returns:
        Reader instance (PDFReader, WordReader, etc)
    """
    from ._pdf_reader import PDFReader
    from ._word_reader import WordReader

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PDFReader(file_path)
    elif ext == ".docx":
        return WordReader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def is_supported_format(file_path: str) -> bool:
    """Check if file format is supported."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in [".pdf", ".docx", ".txt"]


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get basic file information."""
    return {
        "path": file_path,
        "name": os.path.basename(file_path),
        "ext": os.path.splitext(file_path)[1].lower(),
        "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
    }
