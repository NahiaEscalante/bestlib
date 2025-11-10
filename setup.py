from setuptools import setup, find_packages

setup(
    name="bestlib",
    version="0.1.0",
    description="MatrixLayout widget for dashboards",
    author="Nahia, Alejandro, Max",
    packages=["BESTLIB"],
    include_package_data=True,
    package_data={
        "BESTLIB": ["*.js", "*.css"],
    },
    install_requires=[
        "ipython>=8",
        "jupyterlab>=4",
        "ipywidgets>=8",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
    ],
)
