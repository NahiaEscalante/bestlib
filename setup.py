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
    # Dependencias opcionales: el código maneja las importaciones de forma opcional (try/except)
    # Los usuarios deben instalar las dependencias manualmente según su entorno
    # Dependencias recomendadas:
    # - ipython>=8.0 (requerido para Jupyter)
    # - ipywidgets>=8.0 (requerido para widgets interactivos)
    # - pandas>=1.3.0 (recomendado para trabajar con DataFrames)
    # - numpy>=1.20.0 (recomendado para histogramas, violines, etc.)
    # - scikit-learn>=1.0.0 (opcional, solo para add_confusion_matrix)
    install_requires=[],
)
