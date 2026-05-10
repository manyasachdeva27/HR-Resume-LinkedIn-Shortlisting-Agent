# tools/__init__.py
# Package initializer for document extraction tools.

from .pdf_reader import extract_text_from_file

__all__ = ["extract_text_from_file"]
