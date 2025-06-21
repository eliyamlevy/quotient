#!/usr/bin/env python3
"""
Setup script for Quotient - AI-Powered Inventory Management System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="quotient",
    version="0.1.0",
    author="Quotient Team",
    author_email="team@quotient.ai",
    description="AI-Powered Inventory Management System with three-layer architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quotient/quotient",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "web": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "streamlit>=1.28.0",
        ],
        "full": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "streamlit>=1.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quotient=quotient.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "quotient": ["*.json", "*.yaml", "*.yml"],
    },
    keywords=[
        "ai",
        "inventory",
        "management",
        "ocr",
        "nlp",
        "machine-learning",
        "document-processing",
        "automation",
    ],
    project_urls={
        "Bug Reports": "https://github.com/quotient/quotient/issues",
        "Source": "https://github.com/quotient/quotient",
        "Documentation": "https://quotient.readthedocs.io/",
    },
) 