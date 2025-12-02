from setuptools import setup, find_packages
from pathlib import Path

# Leer el README para long_description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pybestlib",
    version="0.1.0",
    description="BestLib, the best lib for graphics - Interactive dashboards for Jupyter with D3.js",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nahia Escalante, Alejandro Rojas y Max Antúnez",
    author_email="",  # Agregar email si lo deseas
    url="https://github.com/NahiaEscalante/bestlib",  # Actualizar con tu URL real
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Jupyter",
    ],
    keywords="visualization, dashboard, d3.js, jupyter, interactive, charts, data-visualization",
    # Usar find_packages para incluir todos los subpaquetes automáticamente
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    package_data={
        "BESTLIB": ["*.js", "*.css"],
    },
    python_requires=">=3.8",
    install_requires=[
        "ipython>=8.0",
        "ipykernel>=6.0",
        "ipywidgets>=8.0",
        "traitlets>=5.9",
        "pandas>=1.3",
        "numpy>=1.20",
        "scipy>=1.8",
        "jupyterlab>=4.0",
        "notebook>=7.0",
    ],
    extras_require={
        "ml": ["scikit-learn>=1.0"],
    },
    project_urls={
        "Bug Reports": "https://github.com/NahiaEscalante/bestlib/issues",
        "Source": "https://github.com/NahiaEscalante/bestlib",
        "Documentation": "https://github.com/NahiaEscalante/bestlib#readme",
    },
)
