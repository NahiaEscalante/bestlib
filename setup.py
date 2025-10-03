from setuptools import setup, find_packages

setup(
    name="bestlib",
    version="0.1.0",
    description="MatrixLayout widget for dashboards",
    author="Nahia, Alejandro, Max",
    packages=find_packages(),
    install_requires=[
        "anywidget",
        "traitlets"
    ],
)
