from setuptools import setup, find_packages

setup(
    name="bestlib",
    version="0.1.0",
    description="MatrixLayout widget for dashboards",
    author="Nahia, Alejandro, Max",
    # Asegura que ambos alias se empaqueten
    packages=["BESTLIB", "bestlib"],
    include_package_data=True,
    package_data={
        "BESTLIB": ["*.js", "*.css"],
        "bestlib": ["*.js", "*.css"]
    },
    install_requires=[],
)
