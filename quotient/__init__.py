"""
Quotient - AI-Powered Inventory Management System

A three-layer AI system for ingesting, analyzing, and completing inventory information
from various data sources including emails, PDFs, images, and spreadsheets.
"""

__version__ = "0.1.0"
__author__ = "Quotient Team"

from .core.pipeline import QuotientPipeline
from .core.config import QuotientConfig

__all__ = ["QuotientPipeline", "QuotientConfig"] 