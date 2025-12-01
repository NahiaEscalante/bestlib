"""
Setup script for BESTLIB
"""
from setuptools import setup, find_packages
from pathlib import Path

# Leer README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Leer versión
version = {}
version_file = Path(__file__).parent / "bestlib" / "version.py"
if version_file.exists():
    exec(version_file.read_text(), version)
else:
    version["__version__"] = "2.0.0"

setup(
    name="bestlib",
    version=version["__version__"],
    author="Nahia Escalante",
    author_email="",
    description="Beautiful & Efficient Visualization Library para Jupyter Notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NahiaEscalante/bestlib",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    package_data={
        "bestlib": [
            "assets/*.js",
            "assets/*.css",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Jupyter",
    ],
    python_requires=">=3.7",
    install_requires=[
        "ipython>=7.0.0",
        "ipywidgets>=7.0.0",
    ],
    extras_require={
        "full": [
            "pandas>=1.3.0",
            "numpy>=1.20.0",
            "scipy>=1.7.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    keywords="visualization jupyter d3 interactive dashboard charts",
    project_urls={
        "Bug Reports": "https://github.com/NahiaEscalante/bestlib/issues",
        "Source": "https://github.com/NahiaEscalante/bestlib",
        "Documentation": "https://github.com/NahiaEscalante/bestlib#readme",
    },
)
