"""
Legacy compatibility wrapper for MatrixLayout.
"""
from warnings import warn
from .layouts.matrix import MatrixLayout as _MatrixLayout

warn(
    "Importar MatrixLayout desde BESTLIB.matrix está deprecado. "
    "Usa BESTLIB.layouts.matrix.MatrixLayout.",
    DeprecationWarning,
    stacklevel=2,
)


class MatrixLayout(_MatrixLayout):
    """Mantiene compatibilidad con el import legacy."""
    
    def __init__(self, *args, **kwargs):
        warn(
            "MatrixLayout desde BESTLIB.matrix es legacy; migra a BESTLIB.layouts.matrix.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["MatrixLayout"]
import uuid
import json
import os
import weakref

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

# Import de pandas de forma defensiva para evitar errores de importación circular
HAS_PANDAS = False
pd = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    import sys
    if 'pandas' in sys.modules:
        # Si pandas ya está en sys.modules pero corrupto, intentar limpiarlo
        try:
            pd_test = sys.modules['pandas']
            # Intentar acceder a un atributo básico para verificar si está corrupto
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            # Pandas está corrupto, limpiarlo
            del sys.modules['pandas']
            # También limpiar submódulos relacionados
            modules_to_remove = [k for k in sys.modules.keys() if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    
    # Ahora intentar importar pandas
    import pandas as pd
    # Verificar que pandas esté completamente inicializado
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    # Si pandas no está disponible o está corrupto, continuar sin él
    HAS_PANDAS = False
    pd = None

# Cache para archivos JS y CSS (cargados una sola vez)
_cached_js = None
_cached_css = None

class MatrixLayout:
    _map = {}
    _safe_html = True
    
    # Sistema de comunicación bidireccional (JS → Python)
    _instances = {}  # dict[str, weakref.ReferenceType[MatrixLayout]]
    _global_handlers = {}  # dict[str, callable]
    _comm_registered = False
    _debug = False  # Modo debug para ver mensajes detallados
    
    @staticmethod
    def _figsize_to_pixels(figsize):
        """
        Convierte figsize de pulgadas a píxeles (asumiendo 96 DPI).
        
        Args:
            figsize: Tupla (width, height) en pulgadas o píxeles, o None
            
        Returns:
            Tupla (width, height) en píxeles, o None
        """
        if figsize is None:
            return None
        if isinstance(figsize, (tuple, list)) and len(figsize) == 2:
            # Si los valores son > 50, asumimos que ya están en píxeles
            # Si son <= 50, asumimos que están en pulgadas
            width, height = figsize
            if width > 50 and height > 50:
                return (int(width), int(height))
            else:
                # Convertir de pulgadas a píxeles (96 DPI)
                return (int(width * 96), int(height * 96))
        return None
    
    @classmethod
    def _process_figsize_in_kwargs(cls, kwargs):
        """
        Procesa figsize en kwargs, convirtiéndolo a píxeles si existe.
        
        Args:
            kwargs: Diccionario de argumentos que puede contener 'figsize'
        """
        if 'figsize' in kwargs:
            figsize_px = cls._figsize_to_pixels(kwargs['figsize'])
            if figsize_px:
                kwargs['figsize'] = figsize_px
            else:
                del kwargs['figsize']
    
    @staticmethod
    def _prepare_data(data, x_col=None, y_col=None, category_col=None, value_col=None):
        """
        Prepara datos para visualización, aceptando DataFrames de pandas o listas de diccionarios.
        OPTIMIZADO: Usa operaciones vectorizadas en lugar de iterrows() para mejor rendimiento.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X (scatter plots)
            y_col: Nombre de columna para eje Y (scatter plots)
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (bar charts)
        
        Returns:
            tuple: (datos_procesados, datos_originales)
            - datos_procesados: Lista de diccionarios con formato estándar
            - datos_originales: Lista de diccionarios con todas las columnas originales
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # OPTIMIZACIÓN: Convertir DataFrame a lista de diccionarios una sola vez
            original_data = data.to_dict('records')
            
            # OPTIMIZACIÓN: Usar operaciones vectorizadas en lugar de iterrows()
            # Crear DataFrame con solo las columnas necesarias
            df_work = pd.DataFrame(index=data.index)
            
            # Mapear columnas según especificación (vectorizado)
            if x_col and x_col in data.columns:
                df_work['x'] = data[x_col]
            elif 'x' in data.columns:
                df_work['x'] = data['x']
            
            if y_col and y_col in data.columns:
                df_work['y'] = data[y_col]
            elif 'y' in data.columns:
                df_work['y'] = data['y']
            
            if category_col and category_col in data.columns:
                df_work['category'] = data[category_col]
            elif 'category' in data.columns:
                df_work['category'] = data['category']
            
            if value_col and value_col in data.columns:
                df_work['value'] = data[value_col]
            elif 'value' in data.columns:
                df_work['value'] = data['value']
            
            # OPTIMIZACIÓN: Convertir a lista de diccionarios y agregar referencias
            # Esto es mucho más rápido que iterrows()
            processed_data = df_work.to_dict('records')
            
            # Agregar referencias a filas originales e índices
            for idx, item in enumerate(processed_data):
                item['_original_row'] = original_data[idx]
                item['_original_index'] = int(data.index[idx])
            
            return processed_data, original_data
        else:
            # Si ya es lista de diccionarios, solo agregar referencias
            if isinstance(data, list):
                processed_data = []
                for idx, item in enumerate(data):
                    processed_item = item.copy()
                    # Asegurar que existe _original_row
                    if '_original_row' not in processed_item:
                        processed_item['_original_row'] = item
                    if '_original_index' not in processed_item:
                        processed_item['_original_index'] = idx
                    processed_data.append(processed_item)
                return processed_data, data
            else:
                raise ValueError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")
    
    @classmethod
    def _validate_data(cls, data, required_cols=None, required_type=None):
        """
        Valida que los datos tengan el formato correcto y las columnas/keys requeridas.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
            required_cols: Lista de columnas/keys requeridas (opcional)
            required_type: Tipo esperado ('DataFrame' o 'list')
        
        Raises:
            ValueError: Si los datos no tienen el formato correcto o faltan columnas/keys
        """
        if required_type == 'DataFrame':
            if not HAS_PANDAS:
                raise ValueError("pandas no está instalado. Instala con: pip install pandas")
            if not isinstance(data, pd.DataFrame):
                raise ValueError(f"Se esperaba un DataFrame de pandas, pero se recibió: {type(data).__name__}")
            if data.empty:
                raise ValueError("El DataFrame está vacío")
            if required_cols:
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    raise ValueError(f"Faltan las siguientes columnas en el DataFrame: {missing_cols}")
        elif required_type == 'list':
            if not isinstance(data, list):
                raise ValueError(f"Se esperaba una lista de diccionarios, pero se recibió: {type(data).__name__}")
            if len(data) == 0:
                raise ValueError("La lista de datos está vacía")
            if required_cols:
                # Verificar que todos los elementos tengan las keys requeridas
                first_item = data[0]
                if not isinstance(first_item, dict):
                    raise ValueError("Los elementos de la lista deben ser diccionarios")
                missing_keys = [key for key in required_cols if key not in first_item]
                if missing_keys:
                    raise ValueError(f"Faltan las siguientes keys en los diccionarios: {missing_keys}")
        elif required_type is not None:
            raise ValueError(f"Tipo de validación no reconocido: {required_type}")
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug.
        
        Args:
            enabled (bool): Si True, activa mensajes detallados de debug.
                           Si False, solo muestra errores críticos.
        
        Ejemplo:
            MatrixLayout.set_debug(True)  # Activar debug
            layout = MatrixLayout("S")
            # ... código ...
            MatrixLayout.set_debug(False)  # Desactivar debug
        """
        cls._debug = bool(enabled)
    
    @classmethod
    def on_global(cls, event, func):
        """
        Registra un callback global para un tipo de evento.
        
        Los callbacks globales se ejecutan para TODOS los layouts, no solo uno específico.
        Útil para logging o procesamiento centralizado de eventos.
        
        Args:
            event (str): Tipo de evento ('select', 'click', 'brush', etc.)
            func (callable): Función callback que recibe el payload del evento
        
        Ejemplo:
            def log_selection(payload):
                print(f"Selección global: {payload['count']} elementos")
            
            MatrixLayout.on_global('select', log_selection)
        """
        cls._global_handlers[event] = func
    
    @classmethod
    def register_comm(cls, force=False):
        """
        Registra manualmente el comm target de Jupyter.
        Útil para forzar el re-registro o verificar que funciona.
        
        ✅ CORRECCIÓN: Ahora delega a CommManager si está disponible para evitar conflictos.
        
        Args:
            force (bool): Si True, fuerza el re-registro incluso si ya está registrado
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        # ✅ CORRECCIÓN CRÍTICA: Si CommManager ya está registrado, no registrar el sistema legacy
        # Esto evita que el sistema legacy sobrescriba al modular
        try:
            from .core.comm import CommManager
            if CommManager._comm_registered:
                if cls._debug:
                    print("ℹ️ [MatrixLayout Legacy] CommManager ya está registrado, usando sistema modular")
                cls._comm_registered = True  # Marcar como registrado para evitar re-registro
                return True
        except (ImportError, AttributeError):
            pass
        
        if cls._comm_registered and not force:
            if cls._debug:
                print("ℹ️ [MatrixLayout] Comm ya estaba registrado")
            return True
        
        if force:
            cls._comm_registered = False
        
        return cls._ensure_comm_target()
    
    @classmethod
    def _ensure_comm_target(cls):
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        Solo se ejecuta una vez por sesión.
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        if cls._comm_registered:
            return True
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                if cls._debug:
                    print("⚠️ [MatrixLayout] No hay kernel de IPython disponible")
                return False
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                """Handler del comm target que procesa mensajes desde JS"""
                div_id = open_msg['content']['data'].get('div_id', 'unknown')
                
                if cls._debug:
                    print(f"🔗 [MatrixLayout] Comm abierto para div_id: {div_id}")
                
                @comm.on_msg
                def _recv(msg):
                    try:
                        data = msg["content"]["data"]
                        div_id = data.get("div_id")
                        event_type = data.get("type")
                        payload = data.get("payload")
                        
                        if cls._debug:
                            print(f"📩 [MatrixLayout] Evento recibido:")
                            print(f"   - Tipo: {event_type}")
                            print(f"   - Div ID: {div_id}")
                            print(f"   - Payload: {payload}")
                        
                        # Buscar instancia por div_id
                        inst_ref = cls._instances.get(div_id)
                        inst = inst_ref() if inst_ref else None
                        
                        if cls._debug:
                            print(f"   🔍 [Legacy] Buscando instancia para div_id '{div_id}'")
                            print(f"   🔍 [Legacy] Instancia en _instances: {'encontrada' if inst else 'no encontrada'}")
                        
                        # ✅ CORRECCIÓN CRÍTICA: Si no se encuentra en sistema legacy, buscar en CommManager (sistema modular)
                        if inst is None:
                            try:
                                # Intentar múltiples formas de importar CommManager
                                CommManager = None
                                try:
                                    # Desde BESTLIB/matrix.py, core está en el mismo nivel
                                    from .core.comm import CommManager
                                except (ImportError, ValueError, AttributeError):
                                    try:
                                        from BESTLIB.core.comm import CommManager
                                    except (ImportError, ValueError, AttributeError):
                                        try:
                                            import sys
                                            if 'BESTLIB.core.comm' in sys.modules:
                                                CommManager = sys.modules['BESTLIB.core.comm'].CommManager
                                        except:
                                            pass
                                
                                if CommManager is not None:
                                    inst = CommManager.get_instance(div_id)
                                    if inst:
                                        if cls._debug:
                                            print(f"   ✅ Instancia encontrada en CommManager (sistema modular)")
                                    elif cls._debug:
                                        print(f"   ⚠️ Instancia no encontrada en CommManager")
                                        print(f"   🔍 CommManager._instances keys: {list(CommManager._instances.keys())[:5]}")
                            except Exception as e:
                                if cls._debug:
                                    print(f"   ⚠️ Error buscando en CommManager: {e}")
                                    import traceback
                                    traceback.print_exc()
                        
                        # ✅ CORRECCIÓN CRÍTICA: Si la instancia tiene _event_manager (sistema modular), usarlo
                        if inst:
                            if hasattr(inst, "_event_manager"):
                                # Sistema modular: usar EventManager
                                if cls._debug:
                                    print(f"   ✅ Usando EventManager (sistema modular)")
                                    print(f"   🔍 Tipo de instancia: {type(inst).__name__}")
                                inst._event_manager.emit(event_type, payload)
                                return  # ✅ IMPORTANTE: Salir después de emitir al EventManager
                            elif cls._debug:
                                print(f"   ⚠️ Instancia encontrada pero no tiene _event_manager")
                                print(f"   🔍 Tipo de instancia: {type(inst).__name__}")
                                print(f"   🔍 Atributos: {[a for a in dir(inst) if not a.startswith('__')][:10]}")
                        elif cls._debug:
                            print(f"   ⚠️ No se encontró instancia en ningún sistema")
                        
                        # Sistema legacy: buscar handlers en _handlers
                        handlers = []
                        handler_names = []  # Para debug: nombres de handlers
                        
                        # Obtener todos los handlers de la instancia (puede haber múltiples para LinkedViews)
                        if inst and hasattr(inst, "_handlers"):
                            handler = inst._handlers.get(event_type)
                            if handler:
                                # Handler puede ser una función o lista de funciones
                                if isinstance(handler, list):
                                    handlers.extend(handler)
                                    handler_names.extend([f"inst_handler_{i}" for i in range(len(handler))])
                                else:
                                    handlers.append(handler)
                                    handler_names.append("inst_handler_0")
                                if cls._debug:
                                    print(f"   ✓ {len(handlers)} handler(s) de instancia encontrado(s)")
                        
                        # Agregar handler global si existe
                        global_handler = cls._global_handlers.get(event_type)
                        if global_handler:
                            handlers.append(global_handler)
                            handler_names.append("global_handler")
                            if cls._debug:
                                print(f"   ✓ Handler global encontrado")
                        
                        # Ejecutar todos los callbacks (múltiples para soportar múltiples scatter plots)
                        if handlers:
                            for idx, handler in enumerate(handlers):
                                try:
                                    handler_name = handler_names[idx] if idx < len(handler_names) else f"handler_{idx}"
                                    if cls._debug:
                                        print(f"   🔄 Ejecutando {handler_name} (#{idx+1}/{len(handlers)})")
                                    handler(payload)
                                    if cls._debug:
                                        print(f"   ✅ {handler_name} completado")
                                except Exception as e:
                                    handler_name = handler_names[idx] if idx < len(handler_names) else f"handler_{idx}"
                                    error_msg = f"   ❌ Error en {handler_name} (#{idx+1}) para evento '{event_type}': {e}"
                                    if cls._debug:
                                        print(error_msg)
                                        import traceback
                                        traceback.print_exc()
                                    else:
                                        # En modo no-debug, solo mostrar error crítico
                                        print(f"⚠️ [MatrixLayout] {error_msg}")
                        else:
                            if cls._debug:
                                print(f"   ⚠️ No hay handler registrado para '{event_type}'")
                    
                    except Exception as e:
                        error_msg = f"❌ [MatrixLayout] Error procesando evento '{event_type}' para div_id '{div_id}': {e}"
                        print(error_msg)
                        if cls._debug:
                            import traceback
                            print("Traceback completo:")
                            traceback.print_exc()
                        # No re-lanzar la excepción para evitar que rompa otros handlers
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
            
            if cls._debug:
                print("✅ [MatrixLayout] Comm target 'bestlib_matrix' registrado exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ [MatrixLayout] No se pudo registrar comm: {e}")
            if cls._debug:
                import traceback
                traceback.print_exc()
            return False
    
    def on(self, event, func):
        """
        Registra un callback específico para esta instancia.
        
        Nota: Si se registran múltiples handlers para el mismo evento,
        todos se ejecutarán (útil para LinkedViews con múltiples scatter plots).
        """
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        
        # Permitir múltiples handlers para el mismo evento
        if event not in self._handlers:
            self._handlers[event] = []
        elif not isinstance(self._handlers[event], list):
            # Convertir handler único a lista
            self._handlers[event] = [self._handlers[event]]
        
        self._handlers[event].append(func)
        # Si se registra un handler personalizado para 'select', marcar que hay uno personalizado
        if event == 'select':
            self._has_custom_select_handler = True
        return self
    
    def _register_default_select_handler(self):
        """Registra un handler por defecto para eventos 'select' que muestre los datos seleccionados"""
        def default_select_handler(payload):
            """Handler por defecto que muestra los datos seleccionados (solo si no hay handlers personalizados)"""
            # Solo ejecutar si no hay handlers personalizados
            if hasattr(self, '_has_custom_select_handler') and self._has_custom_select_handler:
                return
            
            # 🔒 CORRECCIÓN: No ejecutar si el evento tiene __view_letter__ (probablemente hay handler específico)
            # Esto evita que se muestre información duplicada o incorrecta
            if payload.get('__view_letter__') is not None:
                return
            
            items = payload.get('items', [])
            count = payload.get('count', len(items))
            
            if count == 0:
                print("📊 No hay elementos seleccionados")
                return
            
            print(f"\n📊 Elementos seleccionados: {count}")
            print("=" * 60)
            
            # Mostrar los primeros elementos (máximo 10 para no saturar)
            display_count = min(count, 10)
            for i, item in enumerate(items[:display_count]):
                print(f"\n[{i+1}]")
                # 🔒 CORRECCIÓN: Filtrar campos para mostrar solo datos relevantes
                # Excluir campos internos, índices, y valores que parecen escalas/rangos
                excluded_keys = {'index', '_original_row', '_original_rows', '__scatter_letter__', 
                                 '__is_primary_view__', '__view_letter__', 'type'}
                for key, value in item.items():
                    # Excluir campos internos
                    if key in excluded_keys:
                        continue
                    # Excluir valores que son listas/arrays (probablemente escalas o rangos)
                    if isinstance(value, (list, tuple, set)):
                        continue
                    # Excluir valores que son diccionarios (datos anidados)
                    if isinstance(value, dict):
                        continue
                    # Mostrar solo valores simples (números, strings, booleanos)
                    print(f"   {key}: {value}")
            
            if count > display_count:
                print(f"\n... y {count - display_count} elemento(s) más")
            print("=" * 60)
            print(f"\n💡 Tip: Usa layout.on('select', tu_funcion) para personalizar el manejo de selecciones")
        
        # Registrar el handler por defecto (pero no marcar como personalizado)
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        if 'select' not in self._handlers:
            self._handlers['select'] = []
        self._handlers['select'].append(default_select_handler)
    
    def get_selected_data(self, as_dataframe=True):
        """
        ✅ NUEVO: Obtiene los datos seleccionados como DataFrame o lista.
        
        Args:
            as_dataframe (bool): Si True, retorna DataFrame de pandas. Si False, retorna lista.
        
        Returns:
            DataFrame de pandas o lista de diccionarios con los datos seleccionados.
        
        Ejemplo:
            layout = MatrixLayout("S")
            layout.map_scatter('S', df, interactive=True)
            layout.display()
            
            # Después de hacer brush selection...
            selected_df = layout.get_selected_data()  # DataFrame
            selected_list = layout.get_selected_data(as_dataframe=False)  # Lista
        """
        if as_dataframe:
            if self._selected_dataframe is not None:
                return self._selected_dataframe
            # Intentar convertir si hay datos pero no DataFrame
            if self._selected_data:
                try:
                    from .reactive.selection import _items_to_dataframe
                    self._selected_dataframe = _items_to_dataframe(self._selected_data)
                    return self._selected_dataframe
                except Exception as e:
                    if MatrixLayout._debug:
                        print(f"⚠️ [MatrixLayout] No se pudo convertir a DataFrame: {e}")
                    return self._selected_data
            try:
                import pandas as pd
                return pd.DataFrame()
            except ImportError:
                return []
        else:
            return self._selected_data
    
    @property
    def selected_data(self):
        """
        ✅ NUEVO: Propiedad que retorna los datos seleccionados como DataFrame.
        
        Ejemplo:
            layout = MatrixLayout("S")
            layout.map_scatter('S', df, interactive=True)
            layout.display()
            
            # Después de hacer brush selection...
            selected = layout.selected_data  # DataFrame automáticamente
        """
        return self.get_selected_data(as_dataframe=True)
    
    def get_selected_data(self, as_dataframe=True):
        """
        ✅ NUEVO: Obtiene los datos seleccionados como DataFrame o lista.
        
        Args:
            as_dataframe (bool): Si True, retorna DataFrame de pandas. Si False, retorna lista.
        
        Returns:
            DataFrame de pandas o lista de diccionarios con los datos seleccionados.
        
        Ejemplo:
            layout = MatrixLayout("S")
            layout.map_scatter('S', df, interactive=True)
            layout.display()
            
            # Después de hacer brush selection...
            selected_df = layout.get_selected_data()  # DataFrame
            selected_list = layout.get_selected_data(as_dataframe=False)  # Lista
        """
        if as_dataframe:
            if self._selected_dataframe is not None:
                return self._selected_dataframe
            # Intentar convertir si hay datos pero no DataFrame
            if self._selected_data:
                try:
                    from ..reactive.selection import _items_to_dataframe
                    self._selected_dataframe = _items_to_dataframe(self._selected_data)
                    return self._selected_dataframe
                except Exception as e:
                    if self._debug:
                        print(f"⚠️ [MatrixLayout] No se pudo convertir a DataFrame: {e}")
                    return self._selected_data
            return pd.DataFrame() if HAS_PANDAS else []
        else:
            return self._selected_data
    
    @property
    def selected_data(self):
        """
        ✅ NUEVO: Propiedad que retorna los datos seleccionados como DataFrame.
        
        Ejemplo:
            layout = MatrixLayout("S")
            layout.map_scatter('S', df, interactive=True)
            layout.display()
            
            # Después de hacer brush selection...
            selected = layout.selected_data  # DataFrame automáticamente
        """
        return self.get_selected_data(as_dataframe=True)

    @classmethod
    def map(cls, mapping):
        cls._map = mapping
    
    @classmethod
    def map_scatter(cls, letter, data, x_col=None, y_col=None, category_col=None, size_col=None, color_col=None, **kwargs):
        """
        Método helper para crear scatter plot desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            **kwargs: Argumentos adicionales (colorMap, pointRadius, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del scatter plot para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'edad': [20, 30, 40], 'salario': [5000, 8000, 12000], 'dept': ['A', 'B', 'A']})
            
            MatrixLayout.map_scatter('S', df, x_col='edad', y_col='salario', category_col='dept', interactive=True)
            layout = MatrixLayout("S")
        """
        # Validar datos con mensajes de error más descriptivos
        try:
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                required_cols = []
                if x_col:
                    required_cols.append(x_col)
                if y_col:
                    required_cols.append(y_col)
                if required_cols:
                    cls._validate_data(data, required_cols=required_cols, required_type='DataFrame')
            else:
                cls._validate_data(data, required_type='list')
                if x_col or y_col:
                    # Verificar que los diccionarios tengan las keys necesarias
                    if isinstance(data, list) and len(data) > 0:
                        required_keys = []
                        if x_col:
                            required_keys.append(x_col)
                        if y_col:
                            required_keys.append(y_col)
                        if required_keys:
                            cls._validate_data(data, required_cols=required_keys, required_type='list')
        except ValueError as e:
            raise ValueError(f"Error validando datos para scatter plot '{letter}': {e}")
        except Exception as e:
            raise ValueError(f"Error inesperado validando datos para scatter plot '{letter}': {e}")
        
        processed_data, original_data = cls._prepare_data(data, x_col=x_col, y_col=y_col, category_col=category_col, value_col=size_col)

        # OPTIMIZACIÓN: Enriquecer con tamaño y color usando operaciones vectorizadas
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if size_col and size_col in data.columns:
                # Vectorizado: asignar directamente desde la columna
                size_values = data[size_col].astype(float, errors='ignore')
                for idx in range(min(len(processed_data), len(size_values))):
                    try:
                        processed_data[idx]['size'] = float(size_values.iloc[idx])
                    except (ValueError, TypeError):
                        pass
            if color_col and color_col in data.columns:
                # Vectorizado: asignar directamente desde la columna
                color_values = data[color_col]
                for idx in range(min(len(processed_data), len(color_values))):
                    processed_data[idx]['color'] = color_values.iloc[idx]
        else:
            # Lista de dicts
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if idx < len(processed_data):
                        if size_col and size_col in item:
                            try:
                                processed_data[idx]['size'] = float(item.get(size_col))
                            except Exception:
                                pass
                        if color_col and color_col in item:
                            processed_data[idx]['color'] = item.get(color_col)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        # OPTIMIZACIÓN: Aplicar sampling si se especifica maxPoints y hay muchos datos
        max_points = kwargs.get('maxPoints', None)
        if max_points and isinstance(max_points, int) and max_points > 0 and len(processed_data) > max_points:
            # Sampling uniforme para mantener distribución (más rápido que aleatorio)
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                # Usar pandas para sampling más eficiente (uniforme)
                step = len(data) / max_points
                sample_indices = [int(i * step) for i in range(max_points)]
                processed_data = [processed_data[i] for i in sample_indices if i < len(processed_data)]
            else:
                # Sampling uniforme para listas
                step = len(processed_data) / max_points
                processed_data = [processed_data[int(i * step)] for i in range(max_points) if int(i * step) < len(processed_data)]
        
        spec = {
            'type': 'scatter',
            'data': processed_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec
    
    @classmethod
    def map_barchart(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Método helper para crear bar chart desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            **kwargs: Argumentos adicionales (color, colorMap, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del bar chart para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'dept': ['A', 'B', 'C'], 'ventas': [100, 200, 150]})
            
            MatrixLayout.map_barchart('B', df, category_col='dept', value_col='ventas', interactive=True)
            layout = MatrixLayout("B")
        """
        from collections import Counter
        
        # Validar datos
        try:
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                if category_col and category_col not in data.columns:
                    raise ValueError(f"Columna '{category_col}' no existe en el DataFrame. Columnas disponibles: {list(data.columns)}")
                if value_col and value_col not in data.columns:
                    raise ValueError(f"Columna '{value_col}' no existe en el DataFrame. Columnas disponibles: {list(data.columns)}")
            else:
                cls._validate_data(data, required_type='list')
        except ValueError as e:
            raise ValueError(f"Error validando datos para bar chart '{letter}': {e}")
        except Exception as e:
            raise ValueError(f"Error inesperado validando datos para bar chart '{letter}': {e}")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Si hay value_col, agrupar y sumar
            if value_col and value_col in data.columns:
                bar_data = data.groupby(category_col)[value_col].sum().reset_index()
                bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
                bar_data = bar_data.to_dict('records')
            elif category_col and category_col in data.columns:
                # Contar por categoría
                counts = data[category_col].value_counts()
                bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
            else:
                raise ValueError("Debe especificar category_col")
            
            # Agregar datos originales para referencia
            original_data = data.to_dict('records')
            for i, bar_item in enumerate(bar_data):
                # Encontrar todas las filas con esta categoría
                matching_rows = [row for row in original_data if row.get(category_col) == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        else:
            # Lista de diccionarios
            if category_col:
                categories = Counter([item.get(category_col, 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            else:
                categories = Counter([item.get('category', 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            
            # Agregar datos originales
            original_data = data if isinstance(data, list) else []
            for bar_item in bar_data:
                matching_rows = [row for row in original_data if row.get(category_col or 'category') == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = value_col if value_col else 'Count'
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'bar',
            'data': bar_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec

    @classmethod
    def map_grouped_barchart(cls, letter, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        """
        Crea barplot anidado: categorías principales (main_col) con subcategorías (sub_col).
        Estructura: {
          type: 'bar', grouped: True,
          groups: [mainCat1, mainCat2, ...],
          series: [sub1, sub2, ...],
          data: [{ group: mainCat, series: sub, value: v }, ...]
        }
        """
        if main_col is None or sub_col is None:
            raise ValueError("Se requieren main_col y sub_col para grouped barplot")
        rows = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col and value_col in data.columns:
                agg = data.groupby([main_col, sub_col])[value_col].sum().reset_index()
                for _, r in agg.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r[value_col])})
            else:
                # contar ocurrencias por combinación
                counts = data.groupby([main_col, sub_col]).size().reset_index(name='value')
                for _, r in counts.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r['value'])})
            groups = agg[main_col].unique().tolist() if 'agg' in locals() else counts[main_col].unique().tolist()
            series = agg[sub_col].unique().tolist() if 'agg' in locals() else counts[sub_col].unique().tolist()
        else:
            # lista de dicts
            from collections import defaultdict
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para grouped barplot")
            if value_col:
                sums = defaultdict(lambda: defaultdict(float))
                for it in data:
                    g = it.get(main_col, 'unknown')
                    s = it.get(sub_col, 'unknown')
                    sums[g][s] += float(it.get(value_col, 0))
                for g, submap in sums.items():
                    for s, v in submap.items():
                        rows.append({'group': g, 'series': s, 'value': float(v)})
            else:
                counts = defaultdict(lambda: defaultdict(int))
                for it in data:
                    g = it.get(main_col, 'unknown')
                    s = it.get(sub_col, 'unknown')
                    counts[g][s] += 1
                for g, submap in counts.items():
                    for s, v in submap.items():
                        rows.append({'group': g, 'series': s, 'value': int(v)})
            groups = sorted(list({r['group'] for r in rows}))
            series = sorted(list({r['series'] for r in rows}))
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'bar',
            'grouped': True,
            'groups': groups,
            'series': series,
            'data': rows,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_histogram(cls, letter, data, value_col=None, bins=10, **kwargs):
        """
        Método helper para crear histograma desde DataFrame o lista de dicts.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            value_col: Columna numérica a binnear (requerida si data es DataFrame)
            bins: Número de bins (int) o secuencia de bordes
            **kwargs: color, axes, etc.
        """
        import math
        import itertools
        values = []
        
        # ✅ DEBUG: Verificar estado de pandas
        debug_mode = hasattr(cls, '_debug') and cls._debug
        
        # ✅ CORRECCIÓN CRÍTICA: Verificar pandas de forma más robusta
        # A veces HAS_PANDAS puede ser True pero pd no está disponible en el scope
        pd_available = HAS_PANDAS
        pd_module = pd
        if pd_available and pd_module is None:
            # Intentar importar pandas si no está disponible
            try:
                import pandas as pd_module
                pd_available = True
            except ImportError:
                pd_available = False
        
        # ✅ DEBUG SIEMPRE: Para diagnóstico del problema
        print(f"🔍 [map_histogram] Procesando histogram '{letter}'")
        print(f"   - HAS_PANDAS: {HAS_PANDAS}")
        print(f"   - pd_available: {pd_available}")
        print(f"   - pd_module is None: {pd_module is None}")
        print(f"   - data type: {type(data)}")
        is_dataframe = pd_module is not None and isinstance(data, pd_module.DataFrame) if pd_module else False
        print(f"   - isinstance(data, pd.DataFrame): {is_dataframe}")
        print(f"   - value_col: {value_col}")
        
        if pd_module is not None and isinstance(data, pd_module.DataFrame):
            print(f"   - DataFrame shape: {data.shape}")
            print(f"   - Column exists: {value_col in data.columns if value_col else False}")
            if value_col and value_col in data.columns:
                print(f"   - Column dtype: {data[value_col].dtype}")
        
        if pd_available and pd_module is not None and isinstance(data, pd_module.DataFrame):
            if not value_col or value_col not in data.columns:
                raise ValueError("Debe especificar value_col para histograma con DataFrame")
            
            if debug_mode:
                print(f"🔍 [map_histogram] Procesando DataFrame para histogram '{letter}'")
                print(f"   - DataFrame shape: {data.shape}")
                print(f"   - value_col: {value_col}")
                print(f"   - Column dtype: {data[value_col].dtype}")
            
            # Extraer valores numéricos limpiando NaN
            try:
                print(f"   - Attempting to extract series from column '{value_col}'")
                series = data[value_col].dropna()
                
                print(f"   - Series length after dropna: {len(series)}")
                if len(series) > 0:
                    print(f"   - Sample values: {series.head(5).tolist()}")
                    print(f"   - Series dtype: {series.dtype}")
                else:
                    print(f"   - ⚠️ WARNING: Series is empty after dropna!")
                
                if len(series) > 0:
                    try:
                        values = series.astype(float).tolist()
                        print(f"   - Values extracted via astype: {len(values)}")
                    except Exception as e:
                        print(f"   - Error in astype(float): {e}, trying manual conversion")
                        values = [float(v) for v in series.tolist()]
                        print(f"   - Values after manual conversion: {len(values)}")
                else:
                    print(f"   - ⚠️ WARNING: No values to extract, series is empty")
                    values = []
            except Exception as e:
                print(f"   - ❌ ERROR extracting series: {e}")
                import traceback
                traceback.print_exc()
                values = []
        else:
            # Lista de diccionarios
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para histograma: se requiere DataFrame o lista de dicts")
            col = value_col or 'value'
            for item in data:
                v = item.get(col)
                if v is not None:
                    try:
                        values.append(float(v))
                    except Exception:
                        continue
        print(f"   - Final values count: {len(values)}")
        if values:
            print(f"   - Values range: [{min(values)}, {max(values)}]")
        
        if not values:
            print(f"   - ⚠️ WARNING: No values extracted, returning empty histogram data")
            hist_data = []
        else:
            vmin = min(values)
            vmax = max(values)
            if isinstance(bins, int):
                if bins <= 0:
                    bins = 10
                step = (vmax - vmin) / bins if vmax > vmin else 1.0
                edges = [vmin + i * step for i in range(bins + 1)]
            else:
                edges = list(bins)
                edges.sort()
            
            # IMPORTANTE: Almacenar filas originales para cada bin
            # Esto permite que las vistas enlazadas reciban los datos correctos
            bin_rows = [[] for _ in range(len(edges) - 1)]  # Lista de listas para cada bin
            
            if debug_mode:
                print(f"   - Created {len(bin_rows)} bins with edges: [{edges[0]:.2f}, ..., {edges[-1]:.2f}]")
            
            if pd_available and pd_module is not None and isinstance(data, pd_module.DataFrame):
                # Para DataFrame: almacenar todas las filas originales que caen en cada bin
                original_data = data.to_dict('records')
                for row in original_data:
                    v = row.get(value_col)
                    if v is not None:
                        try:
                            v_float = float(v)
                            # Asignar bin
                            idx = None
                            for i in range(len(edges) - 1):
                                left, right = edges[i], edges[i + 1]
                                if (v_float >= left and v_float < right) or (i == len(edges) - 2 and v_float == right):
                                    idx = i
                                    break
                            if idx is not None:
                                bin_rows[idx].append(row)
                        except Exception:
                            continue
            else:
                # Para lista de dicts: almacenar items originales
                items = data if isinstance(data, list) else []
                for item in items:
                    v = item.get(value_col or 'value')
                    if v is not None:
                        try:
                            v_float = float(v)
                            # Asignar bin
                            idx = None
                            for i in range(len(edges) - 1):
                                left, right = edges[i], edges[i + 1]
                                if (v_float >= left and v_float < right) or (i == len(edges) - 2 and v_float == right):
                                    idx = i
                                    break
                            if idx is not None:
                                bin_rows[idx].append(item)
                        except Exception:
                            continue
            
            # Centro del bin para etiqueta; D3 usa 'bin' y 'count'
            # IMPORTANTE: Incluir _original_rows para cada bin
            hist_data = [
                {
                    'bin': float((edges[i] + edges[i + 1]) / 2.0),
                    'count': int(len(bin_rows[i])),
                    '_original_rows': bin_rows[i]  # Almacenar todas las filas originales de este bin
                }
                for i in range(len(bin_rows))
            ]
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and value_col:
            kwargs['xLabel'] = value_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Frequency'
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'histogram',
            'data': hist_data,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_boxplot(cls, letter, data, category_col=None, value_col=None, column=None, **kwargs):
        """
        Método helper para crear boxplot por categoría.
        
        Args:
            letter: Letra del layout ASCII
            data: DataFrame o lista de diccionarios
            category_col: Columna categórica (opcional; si None, usa una sola categoría)
            value_col: Columna numérica para calcular cuantiles (requerida con DataFrame)
            column: Alias de value_col (para compatibilidad)
            **kwargs: color, axes, etc.
        """
        # Permitir 'column' como alias de 'value_col' para compatibilidad
        if value_col is None and column is not None:
            value_col = column
        
        import statistics
        def five_num_summary(values_list):
            vals = sorted([float(v) for v in values_list if v is not None])
            if not vals:
                return None
            n = len(vals)
            median = statistics.median(vals)
            # Cuartiles usando método mediana-excluida
            if n < 4:
                q1 = vals[max(0, (n//4) - 1)] if n > 1 else vals[0]
                q3 = vals[min(n-1, (3*n)//4)] if n > 1 else vals[-1]
            else:
                mid = n // 2
                lower = vals[:mid]
                upper = vals[mid+1:] if n % 2 == 1 else vals[mid:]
                q1 = statistics.median(lower) if lower else vals[0]
                q3 = statistics.median(upper) if upper else vals[-1]
            iqr = q3 - q1
            lower_whisker = max(min(vals), q1 - 1.5 * iqr)
            upper_whisker = min(max(vals), q3 + 1.5 * iqr)
            return {
                'lower': float(lower_whisker),
                'q1': float(q1),
                'median': float(median),
                'q3': float(q3),
                'upper': float(upper_whisker)
            }
        box_data = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col is None or value_col not in data.columns:
                raise ValueError("Debe especificar value_col para boxplot con DataFrame")
            if category_col and category_col in data.columns:
                grouped = data.groupby(category_col)
                for cat, subdf in grouped:
                    summary = five_num_summary(subdf[value_col].dropna().tolist())
                    if summary:
                        box_data.append({'category': cat, **summary})
            else:
                summary = five_num_summary(data[value_col].dropna().tolist())
                if summary:
                    box_data.append({'category': 'All', **summary})
        else:
            # Lista de diccionarios
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para boxplot: se requiere DataFrame o lista de dicts")
            val_key = value_col or 'value'
            if category_col:
                from collections import defaultdict
                groups = defaultdict(list)
                for item in data:
                    groups[item.get(category_col, 'unknown')].append(item.get(val_key))
                for cat, vals in groups.items():
                    summary = five_num_summary(vals)
                    if summary:
                        box_data.append({'category': cat, **summary})
            else:
                summary = five_num_summary([item.get(val_key) for item in data])
                if summary:
                    box_data.append({'category': 'All', **summary})
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs and value_col:
            kwargs['yLabel'] = value_col
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'boxplot',
            'data': box_data,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_heatmap(cls, letter, data, x_col=None, y_col=None, value_col=None, **kwargs):
        """
        Crea heatmap a partir de DataFrame/lista: devuelve celdas {x,y,value}.
        
        Si se pasa un DataFrame sin especificar columnas, asume que es una matriz
        y usa índices/columnas automáticamente.
        """
        cells = []
        x_labels, y_labels = [], []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col and x_col and y_col:
                # Tabla larga → celdas directas
                df = data[[x_col, y_col, value_col]].dropna()
                x_labels = df[x_col].astype(str).unique().tolist()
                y_labels = df[y_col].astype(str).unique().tolist()
                cells = [
                    {'x': str(r[x_col]), 'y': str(r[y_col]), 'value': float(r[value_col])}
                    for _, r in df.iterrows()
                ]
            elif x_col is None and y_col is None and value_col is None:
                # Matriz: usar índices y columnas automáticamente
                # Verificar si es una matriz cuadrada (mismo número de filas y columnas, y mismos nombres)
                index_list = data.index.tolist()
                cols_list = data.columns.tolist()
                
                if len(index_list) == len(cols_list) and set(index_list) == set(cols_list):
                    # Matriz cuadrada (como matriz de correlación)
                    # Ordenar para consistencia
                    cols = sorted(cols_list)
                    x_labels = cols
                    y_labels = cols
                    for i, xi in enumerate(cols):
                        for j, yj in enumerate(cols):
                            val = data.loc[yj, xi]  # Usar loc para acceso por etiqueta
                            if pd.notna(val):
                                cells.append({'x': str(xi), 'y': str(yj), 'value': float(val)})
                else:
                    # Matriz rectangular: usar índices como y, columnas como x
                    x_labels = cols_list
                    y_labels = index_list
                    for i, y_val in enumerate(data.index):
                        for j, x_val in enumerate(data.columns):
                            val = data.iloc[i, j]
                            if pd.notna(val):
                                cells.append({'x': str(x_val), 'y': str(y_val), 'value': float(val)})
            else:
                raise ValueError("Especifique x_col, y_col y value_col para heatmap, o pase una matriz sin especificar columnas")
        else:
            # Lista de dicts
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para heatmap")
            for item in data:
                if x_col in item and y_col in item and value_col in item:
                    cells.append({'x': str(item[x_col]), 'y': str(item[y_col]), 'value': float(item[value_col])})
                    x_labels.append(str(item[x_col]))
                    y_labels.append(str(item[y_col]))
            x_labels = sorted(list(set(x_labels)))
            y_labels = sorted(list(set(y_labels)))
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'heatmap',
            'data': cells,
            'xLabels': x_labels,
            'yLabels': y_labels,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_correlation_heatmap(cls, letter, data, **kwargs):
        """
        Calcula matriz de correlación (pearson) para columnas numéricas del DataFrame.
        Las etiquetas X e Y están ordenadas de la misma manera para mantener consistencia.
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_correlation_heatmap requiere DataFrame de pandas")
        num_df = data.select_dtypes(include=['number'])
        if num_df.shape[1] == 0:
            raise ValueError("No hay columnas numéricas para correlación")
        corr = num_df.corr().fillna(0.0)
        # Ordenar columnas alfabéticamente para consistencia
        cols = sorted(corr.columns.tolist())
        corr = corr.loc[cols, cols]  # Reordenar matriz de correlación
        cells = []
        # Crear celdas asegurando que x e y estén en el mismo orden
        for i, xi in enumerate(cols):
            for j, yj in enumerate(cols):
                # Usar iloc correctamente: fila j, columna i (o usar loc con nombres)
                cells.append({'x': str(xi), 'y': str(yj), 'value': float(corr.loc[yj, xi])})
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        # Opción para mostrar valores numéricos (por defecto False)
        showValues = kwargs.get('showValues', False)
        
        spec = {
            'type': 'heatmap',
            'data': cells,
            'xLabels': cols,  # Mismo orden que yLabels
            'yLabels': cols,  # Mismo orden que xLabels
            'isCorrelation': True,
            'showValues': showValues,  # Opción para mostrar valores
            'colorScale': 'diverging',  # Usar escala divergente para correlación
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_line(cls, letter, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """
        Crea line chart. Si series_col está definido, múltiples series.
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if x_col is None or y_col is None:
                raise ValueError("x_col e y_col son requeridos para line plot")
            df = data[[x_col, y_col] + ([series_col] if series_col else [])].dropna()
            if series_col:
                series_names = df[series_col].unique().tolist()
                series = {}
                for name in series_names:
                    sdf = df[df[series_col] == name].sort_values(by=x_col)
                    series[name] = [{ 'x': float(x), 'y': float(y), 'series': str(name) } for x, y in zip(sdf[x_col], sdf[y_col])]
                payload = {'series': series}
            else:
                sdf = df.sort_values(by=x_col)
                payload = {'series': { 'default': [{ 'x': float(x), 'y': float(y) } for x, y in zip(sdf[x_col], sdf[y_col])] }}
        else:
            # Lista de dicts
            items = [d for d in (data or []) if x_col in d and y_col in d]
            if series_col:
                series = {}
                for item in items:
                    key = str(item.get(series_col))
                    series.setdefault(key, []).append({'x': float(item[x_col]), 'y': float(item[y_col]), 'series': key})
                # ordenar por x
                for k in series:
                    series[k] = sorted(series[k], key=lambda p: p['x'])
                payload = {'series': series}
            else:
                pts = sorted([{'x': float(i[x_col]), 'y': float(i[y_col])} for i in items], key=lambda p: p['x'])
                payload = {'series': { 'default': pts }}
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = { 'type': 'line', **payload, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_pie(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Crea pie/donut chart.
        """
        from collections import Counter, defaultdict
        slices = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if category_col is None:
                raise ValueError("category_col requerido para pie")
            
            # IMPORTANTE: Almacenar filas originales para cada categoría
            # Esto permite que las vistas enlazadas reciban los datos correctos
            original_data = data.to_dict('records')
            category_rows = defaultdict(list)  # Diccionario: categoría -> lista de filas
            
            # Agrupar filas por categoría
            for row in original_data:
                cat = row.get(category_col)
                if cat is not None:
                    category_rows[str(cat)].append(row)
            
            if value_col and value_col in data.columns:
                # Calcular suma por categoría
                agg = data.groupby(category_col)[value_col].sum().reset_index()
                slices = [
                    {
                        'category': str(r[category_col]),
                        'value': float(r[value_col]),
                        '_original_rows': category_rows.get(str(r[category_col]), [])  # Almacenar todas las filas originales de esta categoría
                    }
                    for _, r in agg.iterrows()
                ]
            else:
                # Contar por categoría
                counts = data[category_col].value_counts()
                slices = [
                    {
                        'category': str(cat),
                        'value': int(cnt),
                        '_original_rows': category_rows.get(str(cat), [])  # Almacenar todas las filas originales de esta categoría
                    }
                    for cat, cnt in counts.items()
                ]
        else:
            items = data or []
            
            # IMPORTANTE: Almacenar items originales para cada categoría
            category_rows = defaultdict(list)  # Diccionario: categoría -> lista de items
            
            # Agrupar items por categoría
            for it in items:
                cat = it.get(category_col, 'unknown')
                if cat is not None:
                    category_rows[str(cat)].append(it)
            
            if value_col:
                sums = defaultdict(float)
                for it in items:
                    cat = str(it.get(category_col, 'unknown'))
                    val = it.get(value_col, 0)
                    try:
                        sums[cat] += float(val)
                    except Exception:
                        pass
                slices = [
                    {
                        'category': k,
                        'value': float(v),
                        '_original_rows': category_rows.get(k, [])  # Almacenar todos los items originales de esta categoría
                    }
                    for k, v in sums.items()
                ]
            else:
                counts = Counter([str(it.get(category_col, 'unknown')) for it in items])
                slices = [
                    {
                        'category': k,
                        'value': int(v),
                        '_original_rows': category_rows.get(k, [])  # Almacenar todos los items originales de esta categoría
                    }
                    for k, v in counts.items()
                ]
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = { 'type': 'pie', 'data': slices, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_violin(cls, letter, data, value_col=None, category_col=None, bins=20, **kwargs):
        """
        Crea datos para violin: para cada categoría, calcula histograma normalizado
        y retorna perfiles (x: bin, width: densidad) para render (aproximación).
        """
        if value_col is None:
            raise ValueError("value_col es requerido para violin")
        def build_profile(values):
            values = [float(v) for v in values if v is not None]
            if not values:
                return []
            try:
                import numpy as np
                hist, edges = np.histogram(values, bins=bins)
                if len(hist) == 0 or np.max(hist) == 0:
                    # Si no hay datos válidos, retornar perfil vacío
                    return []
                dens = hist / (np.max(hist) if np.max(hist) > 0 else 1)
                centers = [(edges[i] + edges[i+1]) / 2 for i in range(len(edges)-1)]
                # Incluir todos los bins, incluso los de densidad 0, para mantener la forma del violín
                # Pero usar un valor mínimo para w (densidad) para que sea visible
                profile = [{'y': float(c), 'w': float(max(d, 0.01))} for c, d in zip(centers, dens)]
                return profile
            except Exception:
                mn, mx = min(values), max(values)
                step = (mx - mn) / bins if mx > mn else 1
                counts = [0]*bins
                edges = [mn + i*step for i in range(bins+1)]
                for v in values:
                    idx = min(int((v - mn)/step), bins-1) if step>0 else 0
                    counts[idx] += 1
                m = max(counts) or 1
                if m == 0:
                    # Si no hay datos válidos, retornar perfil vacío
                    return []
                dens = [c/m for c in counts]
                centers = [(edges[i] + edges[i+1]) / 2 for i in range(bins)]
                # Incluir todos los bins, incluso los de densidad 0, para mantener la forma del violín
                # Pero usar un valor mínimo para w (densidad) para que sea visible
                profile = [{'y': float(c), 'w': float(max(d, 0.01))} for c, d in zip(centers, dens)]
                return profile
        violins = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if category_col and category_col in data.columns:
                for cat, sub in data.groupby(category_col):
                    prof = build_profile(sub[value_col].dropna().tolist())
                    violins.append({'category': cat, 'profile': prof})
            else:
                prof = build_profile(data[value_col].dropna().tolist())
                violins.append({'category': 'All', 'profile': prof})
        else:
            items = data or []
            if category_col:
                from collections import defaultdict
                groups = defaultdict(list)
                for it in items:
                    groups[str(it.get(category_col, 'unknown'))].append(it.get(value_col))
                for cat, vals in groups.items():
                    violins.append({'category': cat, 'profile': build_profile(vals)})
            else:
                violins.append({'category': 'All', 'profile': build_profile([it.get(value_col) for it in items])})
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = { 'type': 'violin', 'data': violins, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_radviz(cls, letter, data, features=None, class_col=None, **kwargs):
        """
        Crea datos para RadViz simple: anclas uniformes y proyección ponderada.
        Retorna puntos {x,y,category} normalizados en [0,1].
        
        Args:
            letter: Letra del layout ASCII
            data: DataFrame de pandas
            features: Lista de columnas a usar como features (opcional, usa todas las numéricas por defecto)
            class_col: Columna para categorías (colorear puntos)
            **kwargs: Argumentos adicionales (interactive, axes, etc.)
        
        Returns:
            spec con type='radviz' y datos preparados
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_radviz requiere DataFrame")
        import math
        
        df = data.copy()
        
        # Determinar features
        if features is None:
            feats = df.select_dtypes(include=['number']).columns.tolist()
        else:
            # Validar que las features existan en el DataFrame
            feats = [f for f in features if f in df.columns]
        
        if len(feats) < 2:
            raise ValueError(f"Se requieren al menos 2 features para RadViz. Features disponibles: {list(df.columns)}")
        
        # Normalizar features a 0-1 y manejar valores NaN
        for c in feats:
            col = df[c].astype(float)
            # Reemplazar NaN con 0.5 (valor medio)
            col = col.fillna(0.5)
            mn, mx = col.min(), col.max()
            if mx > mn:
                df[c] = (col - mn) / (mx - mn)
            else:
                # Si todos los valores son iguales, usar 0.5
                df[c] = 0.5
        
        k = len(feats)
        anchors = []
        for i in range(k):
            ang = 2*math.pi * i / k - math.pi / 2  # Empezar desde arriba
            anchors.append((math.cos(ang), math.sin(ang)))
        
        points = []
        for idx, row in df.iterrows():
            try:
                # Obtener weights normalizados
                weights = [float(row[c]) if not (isinstance(row[c], float) and math.isnan(row[c])) else 0.5 for c in feats]
                
                # Validar que todos los weights sean válidos
                weights = [w if not (math.isnan(w) or math.isinf(w)) else 0.5 for w in weights]
                
                # Calcular posición ponderada
                s = sum(weights) or 1.0
                if s == 0:
                    s = 1.0
                
                x = sum(w * anchors[i][0] for i, w in enumerate(weights)) / s
                y = sum(w * anchors[i][1] for i, w in enumerate(weights)) / s
                
                # Validar coordenadas
                if math.isnan(x) or math.isinf(x):
                    x = 0.0
                if math.isnan(y) or math.isinf(y):
                    y = 0.0
                
                # Guardar valores normalizados de features para recalcular cuando se muevan los anchors
                # Manejar categoría con validación
                category = None
                if class_col and class_col in df.columns:
                    cat_val = row[class_col]
                    if cat_val is not None and not (isinstance(cat_val, float) and math.isnan(cat_val)):
                        category = str(cat_val)
                
                point_data = {
                    'x': float(x), 
                    'y': float(y), 
                    'category': category,
                    '_weights': [float(w) for w in weights]  # Valores normalizados de cada feature
                }
                points.append(point_data)
            except Exception as e:
                # Si hay error procesando una fila, saltarla
                if cls._debug:
                    print(f"⚠️ [map_radviz] Error procesando fila {idx}: {e}")
                continue
        
        if len(points) == 0:
            raise ValueError("No se pudieron procesar puntos válidos para RadViz. Verifica que los datos tengan valores numéricos válidos.")
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = { 'type': 'radviz', 'data': points, 'features': feats, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_star_coordinates(cls, letter, data, features=None, class_col=None, **kwargs):
        """
        Crea datos para Star Coordinates: similar a RadViz pero los nodos pueden moverse libremente.
        Retorna puntos {x,y,category} con valores normalizados de features guardados.
        
        Args:
            letter: Letra del layout ASCII
            data: DataFrame de pandas
            features: Lista de columnas a usar como features (opcional, usa todas las numéricas por defecto)
            class_col: Columna para categorías (colorear puntos)
            **kwargs: Argumentos adicionales (interactive, axes, etc.)
        
        Returns:
            spec con type='star_coordinates' y datos preparados
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_star_coordinates requiere DataFrame")
        import math
        
        df = data.copy()
        
        # Determinar features
        if features is None:
            feats = df.select_dtypes(include=['number']).columns.tolist()
        else:
            # Validar que las features existan en el DataFrame
            feats = [f for f in features if f in df.columns]
        
        if len(feats) < 2:
            raise ValueError(f"Se requieren al menos 2 features para Star Coordinates. Features disponibles: {list(df.columns)}")
        
        # Normalizar features a 0-1 y manejar valores NaN
        for c in feats:
            col = df[c].astype(float)
            # Reemplazar NaN con 0.5 (valor medio)
            col = col.fillna(0.5)
            mn, mx = col.min(), col.max()
            if mx > mn:
                df[c] = (col - mn) / (mx - mn)
            else:
                # Si todos los valores son iguales, usar 0.5
                df[c] = 0.5
        
        k = len(feats)
        # IMPORTANTE: Ordenar features alfabéticamente para mantener orden consistente
        # Esto asegura que los nodos siempre tengan el mismo orden
        sorted_feats = sorted(feats)
        
        # Inicializar posiciones de nodos en círculo unitario (normalizado)
        # Los nodos se moverán en JS, pero las coordenadas iniciales están normalizadas
        anchors = []
        for i in range(k):
            ang = 2*math.pi * i / k - math.pi / 2  # Empezar desde arriba
            anchors.append((math.cos(ang), math.sin(ang)))
        
        points = []
        for idx, row in df.iterrows():
            try:
                # Obtener weights normalizados en el orden original de feats
                weights_original = [float(row[c]) if not (isinstance(row[c], float) and math.isnan(row[c])) else 0.5 for c in feats]
                
                # Validar que todos los weights sean válidos
                weights_original = [w if not (math.isnan(w) or math.isinf(w)) else 0.5 for w in weights_original]
                
                # IMPORTANTE: Reordenar weights al orden alfabético para que coincidan con sorted_feats
                # Esto asegura que los weights estén en el mismo orden que los nodos en JavaScript
                weights = [weights_original[feats.index(feat)] for feat in sorted_feats]
                
                # Calcular posición ponderada (Star Coordinates)
                # Los anchors están en orden alfabético (sorted_feats), y ahora weights también
                s = sum(weights) or 1.0
                if s == 0:
                    s = 1.0
                
                # Calcular posición ponderada (weights y anchors están en el mismo orden)
                x = sum(weights[i] * anchors[i][0] for i in range(len(weights))) / s
                y = sum(weights[i] * anchors[i][1] for i in range(len(weights))) / s
                
                # IMPORTANTE: Normalizar para que los puntos estén dentro de un círculo unitario
                # Esto asegura que los puntos estén dentro del área visible incluso cuando los nodos se mueven
                distance = math.sqrt(x * x + y * y)
                if distance > 1.0:
                    # Si el punto está fuera del círculo unitario, normalizarlo
                    x = x / distance
                    y = y / distance
                
                # Validar coordenadas
                if math.isnan(x) or math.isinf(x):
                    x = 0.0
                if math.isnan(y) or math.isinf(y):
                    y = 0.0
                
                # Asegurar que las coordenadas estén en [-1, 1]
                x = max(-1.0, min(1.0, x))
                y = max(-1.0, min(1.0, y))
                
                # Manejar categoría con validación
                category = None
                if class_col and class_col in df.columns:
                    cat_val = row[class_col]
                    if cat_val is not None and not (isinstance(cat_val, float) and math.isnan(cat_val)):
                        category = str(cat_val)
                
                point_data = {
                    'x': float(x),
                    'y': float(y),
                    'category': category,
                    '_weights': [float(w) for w in weights]  # Valores normalizados para recalcular
                }
                points.append(point_data)
            except Exception as e:
                # Si hay error procesando una fila, saltarla
                if cls._debug:
                    print(f"⚠️ [map_star_coordinates] Error procesando fila {idx}: {e}")
                continue
        
        if len(points) == 0:
            raise ValueError("No se pudieron procesar puntos válidos para Star Coordinates. Verifica que los datos tengan valores numéricos válidos.")
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        # IMPORTANTE: Pasar features ordenados alfabéticamente para mantener consistencia
        # El orden de los features determina el orden de los nodos en el gráfico
        spec = { 'type': 'star_coordinates', 'data': points, 'features': sorted_feats, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_parallel_coordinates(cls, letter, data, dimensions=None, category_col=None, **kwargs):
        """
        Crea datos para Parallel Coordinates Plot.
        
        Args:
            letter: Letra del layout ASCII
            data: DataFrame de pandas
            dimensions: Lista de columnas a usar como ejes (opcional, usa todas las numéricas por defecto)
            category_col: Columna para categorías (colorear líneas)
            **kwargs: Argumentos adicionales (interactive, axes, etc.)
        
        Returns:
            spec con type='parallel_coordinates' y datos preparados
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_parallel_coordinates requiere DataFrame")
        
        import math
        
        # Determinar dimensiones
        if dimensions is None:
            dims = data.select_dtypes(include=['number']).columns.tolist()
        else:
            # Validar que las dimensiones existan en el DataFrame
            dims = [d for d in dimensions if d in data.columns]
        
        if len(dims) < 2:
            raise ValueError(f"Se requieren al menos 2 dimensiones numéricas para Parallel Coordinates. Dimensiones disponibles: {list(data.select_dtypes(include=['number']).columns.tolist())}")
        
        # Validar que haya al menos una dimensión con valores válidos
        valid_dims = []
        for dim in dims:
            col = data[dim].astype(float)
            if col.notna().sum() > 0:  # Si hay al menos un valor válido
                valid_dims.append(dim)
        
        if len(valid_dims) < 2:
            raise ValueError(f"Se requieren al menos 2 dimensiones con valores válidos para Parallel Coordinates. Dimensiones válidas: {valid_dims}")
        
        dims = valid_dims  # Usar solo dimensiones válidas
        
        # Preparar datos: cada fila es un punto con valores para cada dimensión
        points = []
        for idx, row in data.iterrows():
            try:
                point = {}
                has_valid_value = False
                
                for dim in dims:
                    val = row[dim]
                    # Manejar valores NaN e infinitos
                    if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                        try:
                            point[dim] = float(val)
                            if not (math.isnan(point[dim]) or math.isinf(point[dim])):
                                has_valid_value = True
                        except (ValueError, TypeError):
                            point[dim] = None
                    else:
                        point[dim] = None
                
                # Solo agregar punto si tiene al menos un valor válido
                if has_valid_value:
                    # Manejar categoría con validación
                    if category_col and category_col in data.columns:
                        cat_val = row[category_col]
                        if cat_val is not None and not (isinstance(cat_val, float) and math.isnan(cat_val)):
                            point['category'] = str(cat_val)
                    points.append(point)
            except Exception as e:
                # Si hay error procesando una fila, saltarla
                if cls._debug:
                    print(f"⚠️ [map_parallel_coordinates] Error procesando fila {idx}: {e}")
                continue
        
        if len(points) == 0:
            raise ValueError("No se pudieron procesar puntos válidos para Parallel Coordinates. Verifica que los datos tengan valores numéricos válidos.")
        
        # Procesar figsize si está en kwargs
        cls._process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': 'parallel_coordinates',
            'data': points,
            'dimensions': dims,
            'category_col': category_col,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_line_plot(cls, letter, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """
        Crea line plot completo (versión mejorada del line chart).
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            series_col: Nombre de columna para series (opcional)
            **kwargs: Argumentos adicionales (colorMap, strokeWidth, markers, axes, etc.)
        
        Returns:
            dict: Especificación del line plot para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('line_plot')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        except Exception:
            # Fallback a implementación directa si ChartRegistry no está disponible
            spec = cls.map_line(letter, data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
            spec['type'] = 'line_plot'
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_horizontal_bar(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Crea horizontal bar chart.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, cuenta si se omite)
            **kwargs: Argumentos adicionales (color, colorMap, axes, etc.)
        
        Returns:
            dict: Especificación del horizontal bar chart para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('horizontal_bar')
            spec = chart.get_spec(data, category_col=category_col, value_col=value_col, **kwargs)
        except Exception:
            # Fallback a implementación directa
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                if category_col is None:
                    raise ValueError("category_col requerido para horizontal bar")
                if value_col:
                    df = data[[category_col, value_col]].dropna()
                    bar_data = [{'category': str(cat), 'value': float(val)} for cat, val in zip(df[category_col], df[value_col])]
                else:
                    counts = data[category_col].value_counts()
                    bar_data = [{'category': str(cat), 'value': int(count)} for cat, count in counts.items()]
            else:
                if category_col is None:
                    raise ValueError("category_col requerido para horizontal bar")
                from collections import Counter
                if value_col:
                    bar_data = [{'category': str(d.get(category_col)), 'value': float(d.get(value_col, 0))} for d in data if category_col in d]
                else:
                    cats = [d.get(category_col) for d in data if category_col in d]
                    counts = Counter(cats)
                    bar_data = [{'category': str(cat), 'value': int(count)} for cat, count in counts.items()]
            
            spec = {'type': 'horizontal_bar', 'data': bar_data, **kwargs}
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_hexbin(cls, letter, data, x_col=None, y_col=None, **kwargs):
        """
        Crea hexbin chart (visualización de densidad).
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Argumentos adicionales (bins, colorScale, axes, etc.)
        
        Returns:
            dict: Especificación del hexbin chart para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('hexbin')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, **kwargs)
        except Exception:
            # Fallback a implementación directa
            processed_data, _ = cls._prepare_data(data, x_col=x_col, y_col=y_col)
            spec = {'type': 'hexbin', 'data': processed_data, 'options': {'bins': kwargs.get('bins', 20)}, **kwargs}
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_errorbars(cls, letter, data, x_col=None, y_col=None, yerr=None, xerr=None, **kwargs):
        """
        Crea errorbars chart.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            yerr: Nombre de columna para error en Y (opcional)
            xerr: Nombre de columna para error en X (opcional)
            **kwargs: Argumentos adicionales (color, strokeWidth, capSize, axes, etc.)
        
        Returns:
            dict: Especificación del errorbars chart para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('errorbars')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
        except Exception:
            # Fallback a implementación directa
            processed_data, _ = cls._prepare_data(data, x_col=x_col, y_col=y_col)
            # Agregar errores si existen
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                if yerr and yerr in data.columns:
                    for idx, val in enumerate(data[yerr]):
                        if idx < len(processed_data):
                            processed_data[idx]['yerr'] = float(val) if pd.notna(val) else 0
                if xerr and xerr in data.columns:
                    for idx, val in enumerate(data[xerr]):
                        if idx < len(processed_data):
                            processed_data[idx]['xerr'] = float(val) if pd.notna(val) else 0
            spec = {'type': 'errorbars', 'data': processed_data, **kwargs}
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_fill_between(cls, letter, data, x_col=None, y1=None, y2=None, **kwargs):
        """
        Crea fill_between chart (área entre dos líneas).
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1: Nombre de columna para primera línea Y
            y2: Nombre de columna para segunda línea Y
            **kwargs: Argumentos adicionales (color, opacity, axes, etc.)
        
        Returns:
            dict: Especificación del fill_between chart para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('fill_between')
            spec = chart.get_spec(data, x_col=x_col, y1=y1, y2=y2, **kwargs)
        except Exception:
            # Fallback a implementación directa
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                if x_col is None or y1 is None or y2 is None:
                    raise ValueError("x_col, y1 e y2 son requeridos para fill_between")
                df = data[[x_col, y1, y2]].dropna()
                fill_data = [{'x': float(x), 'y1': float(y1_val), 'y2': float(y2_val)} 
                            for x, y1_val, y2_val in zip(df[x_col], df[y1], df[y2])]
            else:
                fill_data = [{'x': float(d.get(x_col, 0)), 'y1': float(d.get(y1, 0)), 'y2': float(d.get(y2, 0))} 
                           for d in data if x_col in d and y1 in d and y2 in d]
            spec = {'type': 'fill_between', 'data': fill_data, 'options': {'opacity': kwargs.get('opacity', 0.3)}, **kwargs}
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_step(cls, letter, data, x_col=None, y_col=None, **kwargs):
        """
        Crea step plot (líneas escalonadas).
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Argumentos adicionales (stepType, color, strokeWidth, axes, etc.)
        
        Returns:
            dict: Especificación del step plot para usar en map()
        """
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('step_plot')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, **kwargs)
        except Exception:
            # Fallback a implementación directa
            processed_data, _ = cls._prepare_data(data, x_col=x_col, y_col=y_col)
            # Ordenar por x para step plot
            processed_data = sorted(processed_data, key=lambda d: d.get('x', 0))
            spec = {'type': 'step_plot', 'data': processed_data, 'options': {'stepType': kwargs.get('stepType', 'step')}, **kwargs}
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_kde(cls, letter, data, column=None, bandwidth=None, **kwargs):
        """Crea KDE (Kernel Density Estimation) chart."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('kde')
            spec = chart.get_spec(data, column=column, bandwidth=bandwidth, **kwargs)
        except Exception as e:
            if cls._debug:
                print(f"⚠️  [MatrixLayout] Error en map_kde: {e}")
                import traceback
                traceback.print_exc()
            spec = {'type': 'kde', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_distplot(cls, letter, data, column=None, bins=30, kde=True, rug=False, **kwargs):
        """Crea distribution plot (histograma + KDE)."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('distplot')
            spec = chart.get_spec(data, column=column, bins=bins, kde=kde, rug=rug, **kwargs)
        except Exception as e:
            if cls._debug:
                print(f"⚠️  [MatrixLayout] Error en map_distplot: {e}")
                import traceback
                traceback.print_exc()
            spec = {'type': 'distplot', 'data': {}, **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_rug(cls, letter, data, column=None, axis='x', **kwargs):
        """Crea rug plot."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('rug')
            spec = chart.get_spec(data, column=column, axis=axis, **kwargs)
        except Exception as e:
            if cls._debug:
                print(f"⚠️  [MatrixLayout] Error en map_rug: {e}")
                import traceback
                traceback.print_exc()
            spec = {'type': 'rug', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_qqplot(cls, letter, data, column=None, dist='norm', **kwargs):
        """Crea Q-Q plot."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('qqplot')
            spec = chart.get_spec(data, column=column, dist=dist, **kwargs)
        except Exception as e:
            if cls._debug:
                print(f"⚠️  [MatrixLayout] Error en map_qqplot: {e}")
                import traceback
                traceback.print_exc()
            spec = {'type': 'qqplot', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ecdf(cls, letter, data, column=None, **kwargs):
        """Crea ECDF (Empirical Cumulative Distribution Function) chart."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('ecdf')
            spec = chart.get_spec(data, column=column, **kwargs)
        except Exception as e:
            if cls._debug:
                print(f"⚠️  [MatrixLayout] Error en map_ecdf: {e}")
                import traceback
                traceback.print_exc()
            spec = {'type': 'ecdf', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ridgeline(cls, letter, data, column=None, category_col=None, bandwidth=None, **kwargs):
        """Crea ridgeline plot (joy plot)."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('ridgeline')
            spec = chart.get_spec(data, column=column, category_col=category_col, bandwidth=bandwidth, **kwargs)
        except Exception:
            spec = {'type': 'ridgeline', 'series': {}, **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ribbon(cls, letter, data, x_col=None, y1_col=None, y2_col=None, **kwargs):
        """Crea ribbon plot (área entre líneas con gradiente)."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('ribbon')
            spec = chart.get_spec(data, x_col=x_col, y1_col=y1_col, y2_col=y2_col, **kwargs)
        except Exception:
            spec = {'type': 'ribbon', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_hist2d(cls, letter, data, x_col=None, y_col=None, bins=20, **kwargs):
        """Crea 2D histogram."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('hist2d')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, bins=bins, **kwargs)
        except Exception:
            spec = {'type': 'hist2d', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_polar(cls, letter, data, angle_col=None, radius_col=None, angle_unit='rad', **kwargs):
        """Crea polar plot."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('polar')
            spec = chart.get_spec(data, angle_col=angle_col, radius_col=radius_col, angle_unit=angle_unit, **kwargs)
        except Exception:
            spec = {'type': 'polar', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_funnel(cls, letter, data, stage_col=None, value_col=None, **kwargs):
        """Crea funnel plot."""
        try:
            from .charts import ChartRegistry
            chart = ChartRegistry.get('funnel')
            spec = chart.get_spec(data, stage_col=stage_col, value_col=value_col, **kwargs)
        except Exception:
            spec = {'type': 'funnel', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def set_safe_html(cls, safe: bool):
        cls._safe_html = bool(safe)
    
    @classmethod
    def get_status(cls):
        """Retorna el estado actual del sistema de comunicación."""
        active_instances = {
            div_id: ref() is not None 
            for div_id, ref in cls._instances.items()
        }
        
        return {
            "comm_registered": cls._comm_registered,
            "debug_mode": cls._debug,
            "active_instances": sum(active_instances.values()),
            "total_instances": len(cls._instances),
            "instance_ids": list(cls._instances.keys()),
            "global_handlers": list(cls._global_handlers.keys()),
        }

    def __init__(self, ascii_layout=None, figsize=None, row_heights=None, col_widths=None, gap=None, cell_padding=None, max_width=None):
        """
        Crea una nueva instancia de MatrixLayout.
        
        Args:
            ascii_layout (str, optional): Layout ASCII. Si no se proporciona, se genera uno simple.
            figsize (tuple, optional): Tamaño global de gráficos (width, height) en pulgadas. Por defecto None.
            row_heights (list, optional): Lista de alturas por fila (px o fr). Por defecto None.
            col_widths (list, optional): Lista de anchos por columna (px, fr, o ratios). Por defecto None.
            gap (int, optional): Espaciado entre celdas en píxeles. Por defecto None (usa 12px).
            cell_padding (int, optional): Padding de celdas en píxeles. Por defecto None (usa 15px).
            max_width (int, optional): Ancho máximo del layout en píxeles. Por defecto None (usa 1200px).
        """
        # Si no se proporciona layout, crear uno simple
        if ascii_layout is None:
            ascii_layout = "A"
        
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())
        MatrixLayout._instances[self.div_id] = weakref.ref(self)
        self._handlers = {}
        self._has_custom_select_handler = False  # Flag para rastrear handlers personalizados
        self._reactive_model = None  # Para modelo reactivo
        self._merge_opt = None  # Merge explícito por instancia (True | False | [letras])
        
        # Inicializar self._map vacío (no se usa, todos los map_* guardan en MatrixLayout._map)
        # Se mantiene por compatibilidad pero _prepare_repr_data usa MatrixLayout._map directamente
        self._map = {}
        
        # ✅ NUEVO: Sistema de selección para MatrixLayout básico
        self._selected_data = []  # Datos seleccionados (lista de diccionarios)
        self._selected_dataframe = None  # DataFrame de pandas (si está disponible)
        
        # Registrar handler por defecto para eventos 'select' que muestre los datos seleccionados
        self._register_default_select_handler()
        
        # ✅ NUEVO: Registrar handler automático que guarda datos seleccionados
        def auto_save_selection_handler(payload):
            """Handler automático que guarda datos seleccionados en la instancia"""
            items = payload.get('items', [])
            if items:
                self._selected_data = items
                # Intentar convertir a DataFrame
                try:
                    from .reactive.selection import _items_to_dataframe
                    self._selected_dataframe = _items_to_dataframe(items)
                except Exception as e:
                    if MatrixLayout._debug:
                        print(f"⚠️ [MatrixLayout] No se pudo convertir selección a DataFrame: {e}")
                    self._selected_dataframe = None
        
        self.on('select', auto_save_selection_handler)
        self._figsize = figsize  # Tamaño global de gráficos
        self._row_heights = row_heights
        self._col_widths = col_widths
        self._gap = gap
        self._cell_padding = cell_padding
        
        # 🔒 OPTIMIZACIÓN: Ajustar max_width automáticamente para dashboards grandes
        # Calcular número de celdas en el layout
        if ascii_layout:
            rows = ascii_layout.strip().split('\n')
            num_rows = len(rows)
            num_cols = len(rows[0]) if rows else 1
            total_cells = num_rows * num_cols
            
            # Si es un dashboard grande (9+ celdas) y max_width es muy pequeño, ajustarlo
            if total_cells >= 9 and max_width is not None and max_width < 1000:
                # Calcular ancho mínimo recomendado: ~300px por columna para dashboards grandes
                recommended_width = num_cols * 300
                # Asegurar mínimo de 1000px para 3x3, 1200px para 4x4
                if total_cells >= 16:  # 4x4 o mayor
                    recommended_width = max(recommended_width, 1600)
                else:  # 3x3
                    recommended_width = max(recommended_width, 1200)
                
                if max_width < recommended_width:
                    if MatrixLayout._debug:
                        print(f"ℹ️ [MatrixLayout] Ajustando max_width de {max_width}px a {recommended_width}px para dashboard {num_rows}x{num_cols} ({total_cells} celdas)")
                    max_width = recommended_width
        
        self._max_width = max_width
        
        # Asegurar que el comm esté registrado
        MatrixLayout._ensure_comm_target()
    
    def connect_selection(self, reactive_model, scatter_letter=None):
        """
        Conecta un modelo reactivo para actualizar automáticamente.
        
        Args:
            reactive_model: Instancia de ReactiveData o SelectionModel
            scatter_letter: Letra del scatter plot (opcional, para enrutamiento específico)
        
        Ejemplo:
            from BESTLIB.reactive import SelectionModel
            
            selection = SelectionModel()
            selection.on_change(lambda items, count: print(f"{count} seleccionados"))
            
            layout = MatrixLayout("S")
            layout.connect_selection(selection, scatter_letter='S')
            layout.display()
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado. Instala con: pip install ipywidgets")
            return
        
        self._reactive_model = reactive_model
        self._scatter_letter = scatter_letter  # Guardar letra del scatter para enrutamiento
        
        # Crear handler que actualiza el modelo reactivo
        def update_model(payload):
            # Verificar si el evento viene del scatter plot correcto
            event_scatter_letter = payload.get('__scatter_letter__')
            if scatter_letter and event_scatter_letter and event_scatter_letter != scatter_letter:
                # Este evento no es para este scatter plot
                if self._debug:
                    print(f"   ⏭️ Connect_selection handler ignorando evento de '{event_scatter_letter}' (esperado: '{scatter_letter}')")
                return
            
            items = payload.get('items', [])
            if self._debug:
                print(f"   📤 Connect_selection handler actualizando reactive_model con {len(items)} items")
            
            # Extraer filas originales completas si existen
            original_rows = []
            for item in items:
                if '_original_row' in item:
                    original_rows.append(item['_original_row'])
                else:
                    # Si no hay _original_row, usar el item completo
                    original_rows.append(item)
            reactive_model.update(original_rows)
            
            if self._debug:
                print(f"   ✅ Connect_selection handler completado")
        
        # Registrar el handler
        self.on('select', update_model)
        # Marcar que hay un handler personalizado (connect_selection también cuenta como personalizado)
        self._has_custom_select_handler = True
        
        return self
    
    def __del__(self):
        """Limpia la referencia cuando se destruye la instancia"""
        if hasattr(self, 'div_id') and self.div_id in MatrixLayout._instances:
            del MatrixLayout._instances[self.div_id]
    
    @staticmethod
    def _load_js_css():
        """
        Carga y cachea los archivos JS y CSS.
        Solo los carga una vez, luego usa el cache.
        
        Returns:
            tuple: (js_code, css_code)
        """
        global _cached_js, _cached_css
        
        if _cached_js is None:
            js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
            with open(js_path, "r", encoding="utf-8") as f:
                _cached_js = f.read()
        
        if _cached_css is None:
            css_path = os.path.join(os.path.dirname(__file__), "style.css")
            with open(css_path, "r", encoding="utf-8") as f:
                _cached_css = f.read()
        
        return _cached_js, _cached_css
    
    def _prepare_repr_data(self, layout_to_use=None):
        """
        Prepara datos comunes para _repr_html_ y _repr_mimebundle_.
        
        Args:
            layout_to_use: Layout ASCII a usar. Si es None, usa self.ascii_layout.
        
        Returns:
            dict: Diccionario con 'js_code', 'css_code', 'escaped_layout', 'meta', 'mapping_js'
        """
        # Cargar JS y CSS (cacheado)
        js_code, css_code = self._load_js_css()
        
        # Usar el layout proporcionado o el de la instancia
        layout = layout_to_use if layout_to_use is not None else self.ascii_layout
        
        # Validar layout ASCII
        rows = [r for r in layout.strip().split("\n") if r]
        if not rows:
            raise ValueError("ascii_layout no puede estar vacío")
        col_len = len(rows[0])
        if any(len(r) != col_len for r in rows):
            raise ValueError("Todas las filas del ascii_layout deben tener igual longitud")
        
        # Escapar backticks para no romper el template literal JS
        escaped_layout = layout.replace("`", "\\`")
        
        # Calcular número de filas y columnas para mejorar dimensiones en dashboards grandes
        row_count = len(rows)
        col_count = len(rows[0]) if rows else 1
        
        # Preparar metadata
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id,
            "__row_count__": row_count,  # Para cálculos de dimensiones en JS
            "__col_count__": col_count   # Para cálculos de dimensiones en JS
        }
        
        # Agregar configuración de matriz si existe
        if self._row_heights is not None:
            meta["__row_heights__"] = self._row_heights
        if self._col_widths is not None:
            meta["__col_widths__"] = self._col_widths
        if self._gap is not None:
            meta["__gap__"] = self._gap
        if self._cell_padding is not None:
            meta["__cell_padding__"] = self._cell_padding
        if self._max_width is not None:
            meta["__max_width__"] = self._max_width
        if self._figsize is not None:
            figsize_px = self._figsize_to_pixels(self._figsize)
            if figsize_px:
                meta["__figsize__"] = figsize_px
        
        # Combinar mapping con metadata
        # Usar MatrixLayout._map (todos los map_* son @classmethod y guardan ahí)
        mapping_merged = {**MatrixLayout._map, **meta}
        if self._merge_opt is not None:
            mapping_merged["__merge__"] = self._merge_opt
        
        # Diagnóstico: verificar que los specs estén en el mapping
        if MatrixLayout._debug:
            chart_keys = [k for k in MatrixLayout._map.keys() if not k.startswith('__')]
            print(f"🔍 [MatrixLayout] _prepare_repr_data:")
            print(f"   - MatrixLayout._map keys (charts): {chart_keys}")
            for key in chart_keys[:3]:  # Solo primeros 3 para no saturar
                spec = MatrixLayout._map.get(key)
                if spec:
                    print(f"   - Spec '{key}': type={spec.get('type')}, has_data={'data' in spec}, has_series={'series' in spec}")
        
        mapping_js = json.dumps(_sanitize_for_json(mapping_merged))
        
        # Generar estilo inline para el contenedor si hay max_width
        inline_style = ""
        if self._max_width is not None:
            inline_style = f' style="max-width: {self._max_width}px; margin: 0 auto; box-sizing: border-box;"'
        
        return {
            'js_code': js_code,
            'css_code': css_code,
            'escaped_layout': escaped_layout,
            'meta': meta,
            'mapping_js': mapping_js,
            'inline_style': inline_style
        }

    def _generate_render_js(self, data):
        """
        Genera el código JavaScript común para renderizar el layout.
        
        Args:
            data: Diccionario con datos preparados por _prepare_repr_data()
        
        Returns:
            str: Código JavaScript para renderizar
        """
        return f"""
        (function() {{
          {data['js_code']}
          const mapping = {data['mapping_js']};
          const container = document.getElementById("{self.div_id}");
          if (container) {{
            container.__mapping__ = mapping;
          }}
          render("{self.div_id}", `{data['escaped_layout']}`, mapping);
        }})();
        """
    
    def _repr_html_(self):
        """
        Representación HTML del layout (compatible con Jupyter Notebook clásico).
        
        Returns:
            str: HTML con CSS, contenedor y JavaScript inline
        """
        import sys
        
        # Detectar si estamos en Colab y cargar assets automáticamente
        is_colab = "google.colab" in sys.modules
        if is_colab:
            try:
                AssetManager = None
                try:
                    from ..render.assets import AssetManager
                except (ImportError, ValueError, AttributeError):
                    try:
                        from BESTLIB.render.assets import AssetManager
                    except (ImportError, AttributeError):
                        pass
                
                if AssetManager is not None:
                    try:
                        AssetManager.ensure_colab_assets_loaded()
                    except Exception:
                        pass
            except Exception:
                pass
        
        # Preparar datos comunes
        data = self._prepare_repr_data()

        # Render HTML con contenedor + CSS + JS inline (compatible con Notebook clásico)
        render_js = self._generate_render_js(data).strip()
        html = f"""
        <style>{data['css_code']}</style>
        <div id="{self.div_id}" class="matrix-layout"{data['inline_style']}></div>
        <script>
        {render_js}
        </script>
        """
        return html

    def _repr_mimebundle_(self, include=None, exclude=None):
        """
        Representación MIME bundle del layout (compatible con JupyterLab).
        
        Args:
            include: Tipos MIME a incluir (ignorado)
            exclude: Tipos MIME a excluir (ignorado)
        
        Returns:
            dict: Diccionario con 'text/html' y 'application/javascript'
        """
        import sys
        
        # Detectar si estamos en Colab y cargar assets automáticamente (solo carga, sin espera)
        is_colab = "google.colab" in sys.modules
        if is_colab:
            try:
                # Intentar importar AssetManager de forma segura
                AssetManager = None
                
                # Intentar import relativo (versión modular)
                try:
                    from ..render.assets import AssetManager
                except (ImportError, ValueError, AttributeError):
                    pass
                
                # Si falla, intentar import absoluto
                if AssetManager is None:
                    try:
                        from BESTLIB.render.assets import AssetManager
                    except (ImportError, AttributeError):
                        pass
                
                # Si tenemos AssetManager, usarlo
                if AssetManager is not None:
                    try:
                        AssetManager.ensure_colab_assets_loaded()
                    except Exception:
                        # Si falla, continuar sin carga automática
                        pass
            except Exception:
                # Cualquier otro error, continuar sin carga automática
                pass
        
        # Asegurar que el comm target está registrado
        MatrixLayout._ensure_comm_target()
        
        # Preparar datos comunes
        data = self._prepare_repr_data()
        
        html = f"""
        <style>{data['css_code']}</style>
        <div id="{self.div_id}" class="matrix-layout"{data['inline_style']}></div>
        """
        
        # Usar el método original que siempre funcionó
        # matrix.js ya maneja la carga de D3.js internamente con ensureD3()
        render_js = self._generate_render_js(data).strip()
        js = data['js_code'] + "\n" + render_js

        return {
            "text/html": html,
            "application/javascript": js,
        }
    
    def display(self, ascii_layout=None):
        """
        Muestra el layout usando IPython.display.
        
        Args:
            ascii_layout (str, optional): Layout ASCII a usar. Si no se proporciona, usa self.ascii_layout.
        """
        try:
            from IPython.display import display, HTML, Javascript
            import sys
            
            # Detectar si estamos en Colab y cargar assets automáticamente (solo carga, sin espera)
            is_colab = "google.colab" in sys.modules
            if is_colab:
                try:
                    # Intentar importar AssetManager de forma segura
                    AssetManager = None
                    
                    # Intentar import relativo (versión modular)
                    try:
                        from ..render.assets import AssetManager
                    except (ImportError, ValueError, AttributeError):
                        pass
                    
                    # Si falla, intentar import absoluto
                    if AssetManager is None:
                        try:
                            from BESTLIB.render.assets import AssetManager
                        except (ImportError, AttributeError):
                            pass
                    
                    # Si tenemos AssetManager, usarlo
                    if AssetManager is not None:
                        try:
                            AssetManager.ensure_colab_assets_loaded()
                        except Exception:
                            # Si falla, continuar sin carga automática
                            pass
                except Exception:
                    # Cualquier otro error, continuar sin carga automática
                    pass
            
            MatrixLayout._ensure_comm_target()
            
            # Preparar datos comunes (usa cache)
            data = self._prepare_repr_data(ascii_layout)
            
            html_content = f"""
            <style>{data['css_code']}</style>
            <div id="{self.div_id}" class="matrix-layout"{data['inline_style']}></div>
            """
            
            # Usar el método original que siempre funcionó
            # matrix.js ya maneja la carga de D3.js internamente con ensureD3()
            js_content = self._generate_render_js(data).strip()
            
            display(HTML(html_content))
            display(Javascript(js_content))
            
        except Exception as e:
            print(f"❌ Error: {e}")

    # ==========================
    # API de Merge por Instancia
    # ==========================
    def merge(self, letters=True):
        """Configura merge explícito para este layout.

        Args:
            letters: True para todas las letras, False para desactivar, o lista de letras ["A", "B"].
        """
        self._merge_opt = letters
        return self

    def merge_all(self):
        """Activa merge para todas las letras (equivalente a merge(True))."""
        self._merge_opt = True
        return self

    def merge_off(self):
        """Desactiva merge (equivalente a merge(False))."""
        self._merge_opt = False
        return self

    def merge_only(self, letters):
        """Activa merge solo para las letras indicadas (equivalente a merge([...]))."""
        self._merge_opt = list(letters) if letters is not None else []
        return self


# ==========================
# Utilidades
# ==========================
def _sanitize_for_json(obj):
    """Convierte recursivamente tipos numpy y no serializables a tipos JSON puros."""
    try:
        import numpy as _np  # opcional
    except Exception:
        _np = None

    if obj is None:
        return None
    if isinstance(obj, (str, bool, int, float)):
        return int(obj) if type(obj).__name__ in ("int64", "int32") else (float(obj) if type(obj).__name__ in ("float32", "float64") else obj)
    if _np is not None:
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.ndarray):
            return _sanitize_for_json(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    # Fallback a string para objetos desconocidos
    return str(obj)
