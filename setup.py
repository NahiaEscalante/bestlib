from setuptools import setup, find_packages

setup(
    name="bestlib",
    version="0.1.0",
    description="MatrixLayout widget for dashboards",
    author="Nahia, Alejandro, Max",
    # Usar find_packages para incluir todos los subpaquetes automáticamente
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "BESTLIB": ["*.js", "*.css"],
    },
    # Dependencias requeridas para funcionalidad básica
    install_requires=[
        "ipython>=8.0",      # Requerido para Jupyter Notebook/Lab
        "ipywidgets>=8.0",   # Requerido para widgets interactivos y comunicación bidireccional
        "pandas>=1.3.0",     # Requerido para trabajar con DataFrames
        "numpy>=1.20.0",    # Requerido para histogramas, violines, y operaciones numéricas
    ],
    # Dependencias opcionales (solo para funcionalidades específicas)
    extras_require={
        "confusion_matrix": ["scikit-learn>=1.0.0"],  # Solo necesario para add_confusion_matrix()
    },
)
