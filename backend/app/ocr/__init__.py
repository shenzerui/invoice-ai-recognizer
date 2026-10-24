"""
ocr/__init__.py
"""
from .adapter import OCRAdapter, get_adapter
from .parser import parse_ocr_result

__all__ = ["OCRAdapter", "get_adapter", "parse_ocr_result"]
