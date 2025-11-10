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
    # No instalamos dependencias automáticamente para evitar conflictos
    # El código maneja las importaciones de forma opcional (try/except)
    # Los usuarios deben instalar las dependencias manualmente según su entorno
    install_requires=[],
)
