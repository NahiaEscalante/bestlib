"""
Jerarquía de excepciones para BESTLIB
"""


class BestlibError(Exception):
    """Excepción base para BESTLIB"""
    pass


class LayoutError(BestlibError):
    """Error en layout"""
    pass


class ChartError(BestlibError):
    """Error en gráfico"""
    pass


class DataError(BestlibError):
    """Error en datos"""
    pass


class RenderError(BestlibError):
    """Error en renderizado"""
    pass


class CommunicationError(BestlibError):
    """Error en comunicación JS ↔ Python"""
    pass

