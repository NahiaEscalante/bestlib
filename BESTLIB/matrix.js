(function (global) {
  
  // ==========================================
  // Sistema de Comunicación (JS → Python)
  // ==========================================
  
  /**
   * Obtiene o crea un comm de Jupyter para comunicación con Python
   * Compatible con Jupyter Notebook clásico y Google Colab
   * @param {string} divId - ID del contenedor matrix
   * @param {number} maxRetries - Número máximo de intentos (por defecto 3)
   * @returns {object|Promise|null} Comm de Jupyter, Promise, o null si no está disponible
   */
  function getComm(divId, maxRetries = 3) {
    // Cache global de comms por div_id
    if (!global._bestlibComms) {
      global._bestlibComms = {};
    }
    
    // Si ya existe un comm en cache, retornarlo
    if (global._bestlibComms[divId]) {
      const cachedComm = global._bestlibComms[divId];
      // Si es una promesa, verificar si ya se resolvió
      if (cachedComm instanceof Promise) {
        return cachedComm;
      }
      // Si es un comm válido, retornarlo
      if (cachedComm && typeof cachedComm.send === 'function') {
        return cachedComm;
      }
      // Si el comm es inválido, limpiarlo y crear uno nuevo
      delete global._bestlibComms[divId];
    }
    
    // Función interna para crear comm con retry
    function createComm(attempt = 1) {
      try {
        // Intentar primero con Jupyter clásico
        const J = global.Jupyter;
        if (J && J.notebook && J.notebook.kernel) {
          try {
            const comm = J.notebook.kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
            global._bestlibComms[divId] = comm;
            return comm;
          } catch (e) {
            if (attempt < maxRetries) {
              console.warn(`Intento ${attempt} fallido para crear comm, reintentando...`);
              setTimeout(() => createComm(attempt + 1), 100 * attempt);
              return null;
            }
            throw e;
          }
        }
        
        // Si no funciona, intentar con Google Colab (retorna Promise)
        if (global.google && global.google.colab && global.google.colab.kernel) {
          const commPromise = global.google.colab.kernel.comms.open("bestlib_matrix", { div_id: divId });
          
          // Guardar la promesa en cache
          global._bestlibComms[divId] = commPromise;
          
          // Manejar errores de la promesa
          commPromise.then(comm => {
            global._bestlibComms[divId] = comm;
          }).catch(err => {
            console.error('Error al crear comm en Colab:', err);
            // Limpiar cache en caso de error
            delete global._bestlibComms[divId];
            // Mostrar mensaje visual en el contenedor si existe
            const container = document.getElementById(divId);
            if (container) {
              const errorDiv = document.createElement('div');
              errorDiv.style.cssText = 'color: red; padding: 10px; border: 1px solid red; background: #ffeeee;';
              errorDiv.textContent = 'Error al establecer comunicación con Python. Algunas funciones interactivas pueden no funcionar.';
              container.appendChild(errorDiv);
            }
          });
          
          return commPromise;
        }
        
        // Último intento: buscar kernel en window
        if (global.IPython && global.IPython.notebook && global.IPython.notebook.kernel) {
          try {
            const comm = global.IPython.notebook.kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
            global._bestlibComms[divId] = comm;
            return comm;
          } catch (e) {
            if (attempt < maxRetries) {
              console.warn(`Intento ${attempt} fallido para crear comm, reintentando...`);
              setTimeout(() => createComm(attempt + 1), 100 * attempt);
              return null;
            }
            throw e;
          }
        }
        
        return null;
        
      } catch (e) {
        console.error('Error al crear comm (intento ' + attempt + '):', e);
        if (attempt < maxRetries) {
          setTimeout(() => createComm(attempt + 1), 100 * attempt);
          return null;
        }
        // Mostrar mensaje visual en el contenedor si existe
        const container = document.getElementById(divId);
        if (container) {
          const errorDiv = document.createElement('div');
          errorDiv.style.cssText = 'color: red; padding: 10px; border: 1px solid red; background: #ffeeee;';
          errorDiv.textContent = 'No se pudo establecer comunicación con Python después de ' + maxRetries + ' intentos.';
          container.appendChild(errorDiv);
        }
        return null;
      }
    }
    
    return createComm();
  }
  
  /**
   * Envía un evento desde JavaScript a Python
   * Compatible con Jupyter Notebook clásico y Google Colab
   * @param {string} divId - ID del contenedor matrix
   * @param {string} type - Tipo de evento (ej: 'select', 'click', 'brush')
   * @param {object} payload - Datos del evento
   * @param {number} maxRetries - Número máximo de intentos (por defecto 3)
   */
  async function sendEvent(divId, type, payload, maxRetries = 3) {
    let attempts = 0;
    
    while (attempts < maxRetries) {
      try {
        attempts++;
        const commOrPromise = getComm(divId, maxRetries);
        
        if (!commOrPromise) {
          if (attempts >= maxRetries) {
            console.warn('No se pudo obtener comm después de ' + maxRetries + ' intentos. Evento no enviado:', type);
          }
          return;
        }
        
        // Si es una promesa (Colab), esperar a que se resuelva con timeout
        let comm;
        if (commOrPromise instanceof Promise) {
          try {
            comm = await Promise.race([
              commOrPromise,
              new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
            ]);
          } catch (e) {
            if (e.message === 'Timeout') {
              console.warn('Timeout esperando comm (intento ' + attempts + ')');
              if (attempts < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 100 * attempts));
                continue;
              }
              return;
            }
            throw e;
          }
        } else {
          comm = commOrPromise;
        }
        
        if (!comm) {
          if (attempts < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 100 * attempts));
            continue;
          }
          return;
        }
        
        const message = { 
          type: type, 
          div_id: divId, 
          payload: payload 
        };
        
        // Enviar datos
        if (typeof comm.send === 'function') {
          comm.send(message);
          return; // Éxito, salir
        } else {
          console.warn('Comm no tiene método send (intento ' + attempts + ')');
          if (attempts < maxRetries) {
            // Limpiar comm inválido y reintentar
            if (global._bestlibComms && global._bestlibComms[divId]) {
              delete global._bestlibComms[divId];
            }
            await new Promise(resolve => setTimeout(resolve, 100 * attempts));
            continue;
          }
        }
      } catch (e) {
        console.error('Error al enviar datos (intento ' + attempts + '):', e);
        if (attempts < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 100 * attempts));
          continue;
        }
        // Si falla después de todos los intentos, mostrar error pero no lanzar excepción
        console.error('No se pudo enviar evento después de ' + maxRetries + ' intentos:', type, e);
      }
    }
  }
  
  // ==========================================
  // Renderizado Principal
  // ==========================================
  
  function render(divId, asciiLayout, mapping) {
    const container = document.getElementById(divId);
    if (!container) return;

    const rows = asciiLayout.trim().split("\n");
    const R = rows.length;
    const C = rows[0].length;
    
    container.style.display = "grid";
    
    // Configuración dinámica de columnas
    if (mapping.__col_widths__ && Array.isArray(mapping.__col_widths__) && mapping.__col_widths__.length === C) {
      // Convertir ratios a fr si es necesario
      const colWidths = mapping.__col_widths__.map(w => {
        if (typeof w === 'number') {
          return `${w}fr`;
        }
        return String(w);
      });
      container.style.gridTemplateColumns = colWidths.join(' ');
    } else {
      container.style.gridTemplateColumns = `repeat(${C}, 1fr)`;
    }
    
    // Configuración dinámica de filas
    if (mapping.__row_heights__ && Array.isArray(mapping.__row_heights__) && mapping.__row_heights__.length === R) {
      const rowHeights = mapping.__row_heights__.map(h => {
        if (typeof h === 'number') {
          return `minmax(${h}px, auto)`;
        }
        return String(h);
      });
      container.style.gridTemplateRows = rowHeights.join(' ');
    } else {
      // Aumentar altura de filas para evitar recorte - altura mínima para gráficos completos
      // Considerando: padding (30px) + gráfico (320px) + espacio para ejes (20px extra)
      container.style.gridTemplateRows = `repeat(${R}, minmax(350px, auto))`;
    }
    
    // Configuración dinámica de gap
    const gap = mapping.__gap__ !== undefined ? mapping.__gap__ : 12;
    container.style.gap = `${gap}px`;
    
    // Configuración dinámica de max-width
    if (mapping.__max_width__ !== undefined) {
      container.style.maxWidth = `${mapping.__max_width__}px`;
    }
    
    // Configuración dinámica de cell padding (aplicar a cada celda después)
    const cellPadding = mapping.__cell_padding__ !== undefined ? mapping.__cell_padding__ : 15;

    const safeHtml = mapping.__safe_html__ !== false;
    const divIdFromMapping = mapping.__div_id__ || divId;
    
    // Soporte para merge de celdas - MERGE EXPLÍCITO (por defecto desactivado)
    // El usuario controla el merge con __merge__ en el mapping (true | false | [letras])
    const mergeOpt = mapping.__merge__;
    
    // Lógica de merge:
    // - Si __merge__ es false o undefined → NO merge (por defecto)
    // - Si __merge__ es true → Merge para todas las letras (explícito)
    // - Si __merge__ es array → Solo merge para las letras en el array
    const mergeAllExplicit = mergeOpt === true;
    const mergeSet = Array.isArray(mergeOpt) ? new Set(mergeOpt) : null;

    const shouldMerge = (letter) => {
      if (letter === '.') return false; // Nunca fusionar espacios vacíos
      if (mergeAllExplicit) return true; // Merge para todas (explícito)
      if (mergeSet) return mergeSet.has(letter); // Solo las letras especificadas
      return false; // Por defecto SIN merge
    };

    function isD3Spec(value) {
      return value && typeof value === 'object' && (
        value.type === 'bar' || 
        value.type === 'scatter' || 
        value.type === 'histogram' ||
        value.type === 'pie' ||
        value.type === 'boxplot' ||
        value.type === 'heatmap'
      );
    }
    
    function isSimpleViz(value) {
      if (!value || typeof value !== 'object') return false;
      const type = value.type || value.shape;
      return type === 'circle' || type === 'rect' || type === 'line';
    }

    // Sistema de merge mejorado: marcar celdas visitadas
    const visited = Array.from({length: R}, () => Array(C).fill(false));
    
    for (let r = 0; r < R; r++) {
      for (let c = 0; c < C; c++) {
        if (visited[r][c]) continue;
        
        const letter = rows[r][c];
        if (letter === '.') {
          visited[r][c] = true;
          continue;
        }
        
        let width = 1;
        let height = 1;
        
        // Si debe hacer merge, calcular el área rectangular completa
        if (shouldMerge(letter)) {
          // Expandir horizontalmente primero
          while (c + width < C && !visited[r][c + width] && rows[r][c + width] === letter) {
            width++;
          }
          
          // Expandir verticalmente: verificar que todas las filas debajo tengan la misma letra en el mismo rango
          let canGrow = true;
          while (r + height < R && canGrow) {
            // Verificar que todas las celdas en la fila siguiente dentro del rango sean la misma letra
            for (let cc = c; cc < c + width; cc++) {
              if (visited[r + height][cc] || rows[r + height][cc] !== letter) {
                canGrow = false;
                break;
              }
            }
            if (canGrow) {
              height++;
            }
          }
        }
        
        // Marcar todas las celdas como visitadas
        for (let rr = r; rr < r + height; rr++) {
          for (let cc = c; cc < c + width; cc++) {
            visited[rr][cc] = true;
          }
        }
        
        // Crear celda
        const spec = mapping[letter];
        const cell = document.createElement("div");
        cell.className = "matrix-cell";
        // Agregar ID único basado en letra y posición para LinkedViews
        cell.id = `${divId}-cell-${letter}-${r}-${c}`;
        cell.setAttribute('data-letter', letter);
        // Usar grid-row y grid-column con span para fusionar celdas
        cell.style.gridRow = `${r + 1} / span ${height}`;
        cell.style.gridColumn = `${c + 1} / span ${width}`;
        
        // Aplicar padding personalizado si existe
        if (mapping.__cell_padding__ !== undefined) {
          cell.style.padding = `${mapping.__cell_padding__}px`;
        }

        if (isD3Spec(spec) || isSimpleViz(spec)) {
          // Guardar referencia al mapping en el contenedor para acceso desde funciones de renderizado
          if (!container.__mapping__) {
            container.__mapping__ = mapping;
          }
          // Cargar D3 y renderizar (para gráficos Y formas simples)
          ensureD3().then(d3 => {
            if (isD3Spec(spec)) {
              // Guardar spec y divId en el elemento para uso en ResizeObserver
              cell._chartSpec = spec;
              cell._chartDivId = divIdFromMapping;
              
              // Renderizar inicialmente
              renderChartD3(cell, spec, d3, divIdFromMapping);
              
              // Agregar ResizeObserver para re-renderizar cuando cambie el tamaño
              // Usar debounce para evitar re-renderizados excesivos
              setupResizeObserver(cell, () => {
                // Debounce: esperar 150ms antes de re-renderizar
                if (cell._resizeTimeout) {
                  clearTimeout(cell._resizeTimeout);
                }
                cell._resizeTimeout = setTimeout(() => {
                  // Verificar que D3 todavía esté disponible
                  if (global.d3 && cell._chartSpec) {
                    // Limpiar SVG anterior
                    const existingSvg = cell.querySelector('svg');
                    if (existingSvg) {
                      existingSvg.remove();
                    }
                    // Re-renderizar el gráfico
                    renderChartD3(cell, cell._chartSpec, global.d3, cell._chartDivId);
                  }
                }, 150);
              });
            } else if (isSimpleViz(spec)) {
              renderSimpleVizD3(cell, spec, d3);
            }
          }).catch(err => {
            cell.textContent = 'Error: No se pudo cargar D3.js';
            cell.style.color = '#e74c3c';
            cell.style.padding = '20px';
            console.error('[BESTLIB]', err);
          });
        } else if (safeHtml) {
          cell.innerHTML = spec || letter;
        } else {
          cell.textContent = (typeof spec === 'string') ? spec : letter;
        }

        container.appendChild(cell);
      }
    }
  }
  
  /**
   * Configura un ResizeObserver para un elemento y ejecuta un callback cuando cambia de tamaño
   * @param {HTMLElement} element - Elemento a observar
   * @param {Function} callback - Función a ejecutar cuando cambia el tamaño
   */
  function setupResizeObserver(element, callback) {
    // Evitar múltiples observadores en el mismo elemento
    if (element._resizeObserver) {
      return;
    }
    
    // Verificar si ResizeObserver está disponible
    if (typeof ResizeObserver === 'undefined') {
      // Fallback: usar window resize si ResizeObserver no está disponible
      const resizeHandler = () => {
        if (element && element.parentElement && element.offsetWidth > 0 && element.offsetHeight > 0) {
          callback();
        }
      };
      window.addEventListener('resize', resizeHandler);
      // Guardar referencia al handler para poder limpiarlo más tarde si es necesario
      element._resizeHandler = resizeHandler;
      return;
    }
    
    // Usar ResizeObserver si está disponible
    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        // Solo re-renderizar si el tamaño cambió significativamente (más de 10px)
        // y el elemento tiene dimensiones válidas
        const width = entry.contentRect.width;
        const height = entry.contentRect.height;
        
        if (width <= 0 || height <= 0) {
          // Ignorar si el elemento no tiene dimensiones válidas
          continue;
        }
        
        if (element._lastWidth && element._lastHeight) {
          const widthDiff = Math.abs(width - element._lastWidth);
          const heightDiff = Math.abs(height - element._lastHeight);
          // Solo re-renderizar si el cambio es significativo (más de 10px)
          if (widthDiff > 10 || heightDiff > 10) {
            callback();
          }
        } else {
          // Primera vez, guardar dimensiones pero no ejecutar callback
          // (el callback ya se ejecutó en el render inicial)
        }
        element._lastWidth = width;
        element._lastHeight = height;
      }
    });
    
    resizeObserver.observe(element);
    
    // Guardar referencia al observer para poder desconectarlo más tarde si es necesario
    element._resizeObserver = resizeObserver;
  }

  // ==========================================
  // Renderizado de Visualizaciones Simples con D3
  // ==========================================
  
  /**
   * Renderiza elementos visuales simples (círculos, rectángulos, líneas) usando D3.js
   */
  function renderSimpleVizD3(container, spec, d3) {
    const width = container.clientWidth || 140;
    const height = container.clientHeight || 140;
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 100 100`)
      .style('display', 'block');
    
    const shape = spec.type || spec.shape;
    
    if (shape === 'circle') {
      svg.append('circle')
        .attr('cx', spec.cx || 50)
        .attr('cy', spec.cy || 50)
        .attr('r', 0)
        .attr('fill', spec.fill || spec.color || '#4a90e2')
        .attr('opacity', spec.opacity || 1)
        .attr('stroke', spec.stroke || 'none')
        .attr('stroke-width', spec.strokeWidth || 0)
        .transition()
        .duration(800)
        .attr('r', spec.r || 40);
      
    } else if (shape === 'rect') {
      const rectX = spec.x || 10;
      const rectY = spec.y || 10;
      const rectW = spec.width || 80;
      const rectH = spec.height || 80;
      
      svg.append('rect')
        .attr('x', rectX)
        .attr('y', rectY)
        .attr('width', 0)
        .attr('height', 0)
        .attr('fill', spec.fill || spec.color || '#4a90e2')
        .attr('opacity', spec.opacity || 1)
        .attr('rx', spec.borderRadius || spec.rx || 0)
        .attr('stroke', spec.stroke || 'none')
        .attr('stroke-width', spec.strokeWidth || 0)
        .transition()
        .duration(800)
        .attr('width', rectW)
        .attr('height', rectH);
      
    } else if (shape === 'line') {
      svg.append('line')
        .attr('x1', spec.x1 || 10)
        .attr('y1', spec.y1 || 50)
        .attr('x2', spec.x1 || 10)
        .attr('y2', spec.y1 || 50)
        .attr('stroke', spec.stroke || spec.color || '#4a90e2')
        .attr('stroke-width', spec.strokeWidth || 3)
        .attr('stroke-linecap', 'round')
        .transition()
        .duration(800)
        .attr('x2', spec.x2 || 90)
        .attr('y2', spec.y2 || 50);
    }
  }

  // ==========================================
  // Renderizado de Gráficos con D3.js
  // ==========================================
  
  /**
   * Renderiza etiquetas de ejes con soporte para personalización
   */
  function renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg) {
    // Etiqueta del eje X (debajo del gráfico)
    if (spec.xLabel) {
      const xLabelFontSize = spec.xLabelFontSize || 13;
      const xLabelRotation = spec.xLabelRotation || 0;
      // Posición X: centro del gráfico (en coordenadas del grupo g)
      // Posición Y: debajo del gráfico, dentro del margen inferior
      const xLabelX = chartWidth / 2;
      const xLabelY = chartHeight + margin.bottom - 10;
      
      const xLabelText = g.append('text')
        .attr('x', xLabelX)
        .attr('y', xLabelY)
        .attr('text-anchor', 'middle')
        .style('font-size', `${xLabelFontSize}px`)
        .style('font-weight', '700')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif')
        .text(spec.xLabel);
      
      if (xLabelRotation !== 0) {
        xLabelText.attr('transform', `rotate(${xLabelRotation} ${xLabelX} ${xLabelY})`)
          .attr('text-anchor', xLabelRotation > 0 ? 'start' : 'end')
          .attr('dx', xLabelRotation > 0 ? '0.5em' : '-0.5em')
          .attr('dy', '0.5em');
      }
    }
    
    // Etiqueta del eje Y (a la izquierda del gráfico, rotada -90 grados)
    // IMPORTANTE: El texto debe renderizarse en el SVG principal, no en el grupo g,
    // porque el grupo g tiene un transform que lo desplaza, y necesitamos
    // colocar el texto en coordenadas absolutas del SVG para que sea visible
    if (spec.yLabel && svg) {
      const yLabelFontSize = spec.yLabelFontSize || 13;
      const yLabelRotation = spec.yLabelRotation !== undefined ? spec.yLabelRotation : -90;
      
      // Coordenadas en el espacio del SVG (no del grupo g)
      // X: en el centro del margen izquierdo (margin.left / 2) - posición horizontal
      // Y: en el centro vertical del área del gráfico (margin.top + chartHeight / 2) - posición vertical
      // NOTA: Estas coordenadas están en el espacio del SVG, donde (0,0) es la esquina superior izquierda
      const yLabelX = margin.left / 2;
      const yLabelY = margin.top + chartHeight / 2;
      
      // DEBUG: Verificar que las coordenadas sean válidas
      if (isNaN(yLabelX) || isNaN(yLabelY) || !isFinite(yLabelX) || !isFinite(yLabelY)) {
        console.warn('[BESTLIB] Coordenadas inválidas para etiqueta Y:', { yLabelX, yLabelY, margin, chartHeight });
        return;  // No renderizar si las coordenadas son inválidas
      }
      
      // Crear texto en el SVG principal (no en el grupo g) para que sea visible
      // El texto se renderiza primero sin rotar, luego se rota
      const yLabelText = svg.append('text')
        .attr('x', yLabelX)
        .attr('y', yLabelY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')  // Usar 'central' en lugar de 'middle' para mejor alineación
        .style('font-size', `${yLabelFontSize}px`)
        .style('font-weight', '700')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif')
        .style('pointer-events', 'none')  // No interferir con eventos del gráfico
        .text(spec.yLabel);
      
      // Aplicar rotación (por defecto -90 grados para texto vertical)
      // La rotación se aplica alrededor del punto (yLabelX, yLabelY)
      // IMPORTANTE: Después de la rotación, el texto vertical tendrá su centro en (yLabelX, yLabelY)
      if (yLabelRotation !== 0) {
        yLabelText.attr('transform', `rotate(${yLabelRotation} ${yLabelX} ${yLabelY})`);
      }
    }
  }
  
  /**
   * Calcula márgenes dinámicamente según tamaño de etiquetas de ejes
   */
  function calculateAxisMargins(spec, defaultMargin) {
    const margin = { ...defaultMargin };
    
    // Calcular espacio necesario para etiqueta X
    if (spec.xLabel) {
      const xLabelFontSize = spec.xLabelFontSize || 13;
      const xLabelRotation = spec.xLabelRotation || 0;
      // Si está rotada, necesita más espacio
      if (xLabelRotation !== 0) {
        const rotationRad = Math.abs(xLabelRotation) * Math.PI / 180;
        const labelHeight = xLabelFontSize * 1.2; // Aproximación de altura de texto
        const rotatedHeight = Math.abs(Math.sin(rotationRad) * (spec.xLabel.length * xLabelFontSize * 0.6)) + labelHeight;
        margin.bottom = Math.max(margin.bottom, rotatedHeight + 20);
      } else {
        margin.bottom = Math.max(margin.bottom, xLabelFontSize + 25);
      }
    }
    
    // Calcular espacio necesario para etiqueta Y
    // IMPORTANTE: El texto del eje Y rotado necesita espacio en el margen izquierdo
    if (spec.yLabel) {
      const yLabelFontSize = spec.yLabelFontSize || 13;
      const yLabelRotation = spec.yLabelRotation !== undefined ? spec.yLabelRotation : -90;
      
      // Para texto vertical (-90 grados), necesitamos espacio HORIZONTAL para la altura del texto
      // Cuando el texto se rota -90 grados, su ancho horizontal es igual a su altura vertical original
      // IMPORTANTE: El margen izquierdo debe incluir:
      //   1. Espacio para el eje Y y sus etiquetas (aprox. 40-50px)
      //   2. Espacio para la etiqueta del eje Y rotada (altura del texto / 2 hacia la izquierda desde el centro)
      if (Math.abs(yLabelRotation) === 90 || Math.abs(yLabelRotation) === 270) {
        // Texto vertical: la altura del texto sin rotar se convierte en el ancho cuando está rotado
        // Altura del texto ≈ número de caracteres * tamaño de fuente * 0.7
        // Cuando se rota -90°, el texto vertical necesita espacio horizontal = altura del texto
        // El centro del texto está en margin.left/2, pero el texto se extiende textHeight/2 en cada dirección
        const textHeight = spec.yLabel.length * yLabelFontSize * 0.7; // Altura aproximada del texto
        // Necesitamos espacio para: eje Y (40px) + etiqueta Y rotada (textHeight/2) + padding (20px)
        // El margen izquierdo debe ser al menos: eje Y + mitad del texto rotado + padding
        const minLeftMargin = 40 + (textHeight / 2) + 20; // Espacio para eje + texto + padding
        margin.left = Math.max(margin.left, minLeftMargin);
      } else {
        // Texto rotado en otro ángulo: calcular ancho proyectado
        const rotationRad = Math.abs(yLabelRotation) * Math.PI / 180;
        const labelWidth = spec.yLabel.length * yLabelFontSize * 0.6;
        const labelHeight = yLabelFontSize * 1.2;
        // Calcular el ancho proyectado considerando tanto el ancho como la altura
        const projectedWidth = Math.abs(Math.cos(rotationRad) * labelWidth) + Math.abs(Math.sin(rotationRad) * labelHeight);
        margin.left = Math.max(margin.left, 40 + (projectedWidth / 2) + 20); // Eje Y + texto + padding
      }
    }
    
    return margin;
  }
  
  /**
   * Calcula dimensiones del gráfico basándose en figsize o valores por defecto
   */
  function getChartDimensions(container, spec, defaultWidth, defaultHeight) {
    // Si hay figsize en el spec, usarlo
    if (spec.figsize && Array.isArray(spec.figsize) && spec.figsize.length === 2) {
      return {
        width: spec.figsize[0],
        height: spec.figsize[1]
      };
    }
    
    // Buscar el contenedor padre matrix-layout para acceder al mapping
    let parentContainer = container;
    let mapping = null;
    for (let i = 0; i < 5 && parentContainer; i++) {
      if (parentContainer.classList && parentContainer.classList.contains('matrix-layout')) {
        mapping = parentContainer.__mapping__;
        break;
      }
      parentContainer = parentContainer.parentElement;
    }
    
    // Si hay figsize global en el mapping, usarlo
    if (mapping && mapping.__figsize__ && Array.isArray(mapping.__figsize__) && mapping.__figsize__.length === 2) {
      return {
        width: mapping.__figsize__[0],
        height: mapping.__figsize__[1]
      };
    }
    
    // Usar valores por defecto basados en el contenedor
    const width = container.clientWidth || defaultWidth;
    const availableHeight = Math.max(container.clientHeight - 30, defaultHeight - 30);
    const height = Math.min(availableHeight, defaultHeight);
    
    return { width, height };
  }
  
  /**
   * Renderiza gráficos con D3.js
   */
  function renderChartD3(container, spec, d3, divId) {
    if (spec.type === 'bar') {
      renderBarChartD3(container, spec, d3, divId);
    } else if (spec.type === 'scatter') {
      renderScatterPlotD3(container, spec, d3, divId);
    } else if (spec.type === 'histogram') {
      renderHistogramD3(container, spec, d3, divId);
    } else if (spec.type === 'boxplot') {
      renderBoxplotD3(container, spec, d3, divId);
    } else if (spec.type === 'heatmap') {
      renderHeatmapD3(container, spec, d3, divId);
    } else if (spec.type === 'line') {
      renderLineD3(container, spec, d3, divId);
    } else if (spec.type === 'pie') {
      renderPieD3(container, spec, d3, divId);
    } else if (spec.type === 'violin') {
      renderViolinD3(container, spec, d3, divId);
    } else if (spec.type === 'radviz') {
      renderRadVizD3(container, spec, d3, divId);
    } else {
      // Tipo de gráfico no soportado aún, mostrar mensaje
      container.innerHTML = `<div style="padding: 20px; text-align: center; color: #999;">
        Gráfico tipo '${spec.type}' no implementado aún
      </div>`;
    }
  }

  /**
   * Heatmap con D3.js
   */
  function renderHeatmapD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 500, 400);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 30, right: 20, bottom: 60, left: 70 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }

    const xLabels = spec.xLabels || Array.from(new Set(data.map(d => d.x)));
    const yLabels = spec.yLabels || Array.from(new Set(data.map(d => d.y)));

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(xLabels).range([0, chartWidth]).padding(0.05);
    const y = d3.scaleBand().domain(yLabels).range([0, chartHeight]).padding(0.05);

    const vmin = d3.min(data, d => d.value) ?? 0;
    const vmax = d3.max(data, d => d.value) ?? 1;
    const color = (spec.colorScale === 'diverging')
      ? d3.scaleDiverging([ -1, 0, 1 ], d3.interpolateRdBu)
      : d3.scaleSequential([vmin, vmax], d3.interpolateViridis);

    g.selectAll('rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('x', d => x(d.x))
      .attr('y', d => y(d.y))
      .attr('width', x.bandwidth())
      .attr('height', y.bandwidth())
      .attr('fill', d => color(d.value))
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .attr('opacity', 1);

    if (spec.axes !== false) {
      const tickFontSize = spec.tickFontSize || 12;
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      xAxis.selectAll('text').style('font-size', `${tickFontSize}px`).style('fill', '#000');
      
      const yAxis = g.append('g').call(d3.axisLeft(y));
      yAxis.selectAll('text').style('font-size', `${tickFontSize}px`).style('fill', '#000');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  /**
   * Line chart (multi-series) con hover sincronizado
   */
  function renderLineD3(container, spec, d3, divId) {
    const seriesMap = spec.series || {};
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 40, left: 50 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }

    const allPoints = Object.values(seriesMap).flat();
    const x = d3.scaleLinear().domain(d3.extent(allPoints, d => d.x)).nice().range([0, chartWidth]);
    const y = d3.scaleLinear().domain(d3.extent(allPoints, d => d.y)).nice().range([chartHeight, 0]);

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(Object.keys(seriesMap));
    const line = d3.line().x(d => x(d.x)).y(d => y(d.y));

    Object.entries(seriesMap).forEach(([name, pts]) => {
      g.append('path')
        .datum(pts)
        .attr('fill', 'none')
        .attr('stroke', color(name))
        .attr('stroke-width', 2)
        .attr('d', line)
        .attr('opacity', 0)
        .transition().duration(500).attr('opacity', 1);
    });

    // puntos invisibles para hover sincronizado
    Object.entries(seriesMap).forEach(([name, pts]) => {
      g.selectAll(`.pt-${name}`)
        .data(pts)
        .enter()
        .append('circle')
        .attr('class', `pt pt-${name}`)
        .attr('cx', d => x(d.x))
        .attr('cy', d => y(d.y))
        .attr('r', 4)
        .attr('fill', color(name))
        .attr('opacity', 0)
        .on('mouseenter', function(event, d) {
          // resaltar puntos con mismo x (hover sincronizado)
          const xVal = d.x;
          g.selectAll('.pt')
            .attr('opacity', p => (Math.abs(p.x - xVal) < 1e-9 ? 1 : 0.2))
            .attr('r', p => (Math.abs(p.x - xVal) < 1e-9 ? 5 : 3));
        })
        .on('mouseleave', function() {
          g.selectAll('.pt').attr('opacity', 0).attr('r', 4);
        });
    });

    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g').call(d3.axisLeft(y));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  /**
   * Pie / Donut con click que emite selección por categoría
   */
  function renderPieD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 320, 240);
    let width = dims.width;
    let height = dims.height;
    
    // Calcular radio del pie chart
    // Dejar espacio para etiquetas externas (aproximadamente 50-60px de padding)
    const paddingForLabels = 80; // Espacio adicional para etiquetas externas y líneas de conexión
    const baseRadius = Math.min(width, height) / 2;
    const radius = Math.max(baseRadius - paddingForLabels, 50); // Radio mínimo de 50px
    const innerR = spec.innerRadius != null ? spec.innerRadius : (spec.donut ? radius * 0.5 : 0);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas externas
    // Expandir el SVG si es necesario para acomodar las etiquetas
    const requiredWidth = (radius + paddingForLabels) * 2;
    const requiredHeight = (radius + paddingForLabels) * 2;
    if (width < requiredWidth) {
      width = requiredWidth;
    }
    if (height < requiredHeight) {
      height = requiredHeight;
    }
    
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(data.map(d => d.category));

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${width/2},${height/2})`);

    const arc = d3.arc().innerRadius(innerR).outerRadius(radius);
    const pie = d3.pie().value(d => d.value);
    const arcs = pie(data);

    // Calcular el total para porcentajes
    const total = d3.sum(data, d => d.value);
    
    // Renderizar los paths (segmentos del pie)
    const paths = g.selectAll('path')
      .data(arcs)
      .enter()
      .append('path')
      .attr('d', arc)
      .attr('fill', d => color(d.data.category))
      .attr('opacity', 0.9)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (!spec.interactive) return;
        const category = d.data.category;
        // Emitir evento select con items filtrados si existen en spec._original_rows
        // Compatibilidad: payload simple con categoría
        sendEvent(divId, 'select', {
          type: 'pie',
          items: [{ category }],
          indices: [],
          selected_category: category
        });
      })
      .on('mouseenter', function(event, d) {
        // Resaltar el segmento al pasar el mouse
        d3.select(this)
          .attr('opacity', 1)
          .attr('stroke-width', 3);
      })
      .on('mouseleave', function(event, d) {
        // Restaurar opacidad y stroke
        d3.select(this)
          .attr('opacity', 0.9)
          .attr('stroke-width', 2);
      });
    
    // Agregar etiquetas de texto para cada segmento
    // Configuración de etiquetas desde el spec
    const showLabels = spec.showLabels !== false; // Por defecto mostrar etiquetas (siempre mostrar nombre)
    const showPercentage = spec.showPercentage === true; // Por defecto NO mostrar porcentaje (solo si se especifica)
    const showValue = spec.showValue === true; // Por defecto NO mostrar valor (solo si se especifica)
    const labelFontSize = spec.labelFontSize || 12;
    const labelDistance = spec.labelDistance || (radius * 0.65); // Distancia desde el centro para etiquetas internas
    
    if (showLabels) {
      // Crear un arco para etiquetas internas (más cerca del centro)
      const labelArc = d3.arc()
        .innerRadius(labelDistance)
        .outerRadius(labelDistance);
      
      // Crear grupos para cada etiqueta
      const labelGroups = g.selectAll('.pie-label-group')
        .data(arcs)
        .enter()
        .append('g')
        .attr('class', 'pie-label-group');
      
      // Para cada grupo, agregar etiqueta según el tamaño del segmento
      labelGroups.each(function(d) {
        const group = d3.select(this);
        const percentage = (d.value / total) * 100;
        const midAngle = d.startAngle + (d.endAngle - d.startAngle) / 2;
        
        // Determinar si usar etiqueta interna o externa
        // Usar etiqueta interna solo si:
        // 1. No es donut (innerR === 0)
        // 2. El segmento es suficientemente grande (> 3% del total o > 10 grados)
        const angleSpan = (d.endAngle - d.startAngle) * 180 / Math.PI;
        const isLargeEnough = (percentage > 3) && (angleSpan > 10);
        const useInternalLabel = isLargeEnough && innerR === 0;
        
        if (useInternalLabel) {
          // Etiqueta interna para segmentos grandes (solo si no es donut)
          const labelCentroid = labelArc.centroid(d);
          
          // Etiqueta principal (nombre de la categoría)
          // Siempre mostrar el nombre de la categoría
          group.append('text')
            .attr('transform', `translate(${labelCentroid})`)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('dy', showPercentage || showValue ? '-0.4em' : '0')
            .style('font-size', `${labelFontSize}px`)
            .style('font-weight', '600')
            .style('fill', '#000000')
            .style('font-family', 'Arial, sans-serif')
            .style('pointer-events', 'none')
            .style('text-shadow', '1px 1px 2px rgba(255,255,255,0.8)')  // Sombra para mejor legibilidad
            .text(d.data.category);
          
          // Si también mostrar porcentaje o valor, agregar segunda línea debajo
          if (showPercentage || showValue) {
            const secondLineText = showPercentage && showValue 
              ? `${d.data.value.toFixed(1)} (${percentage.toFixed(1)}%)`
              : showPercentage 
                ? `${percentage.toFixed(1)}%`
                : `${d.data.value.toFixed(1)}`;
            
            group.append('text')
              .attr('transform', `translate(${labelCentroid})`)
              .attr('text-anchor', 'middle')
              .attr('dominant-baseline', 'middle')
              .attr('dy', '1.2em')
              .style('font-size', `${labelFontSize - 2}px`)
              .style('font-weight', '400')
              .style('fill', '#555555')
              .style('font-family', 'Arial, sans-serif')
              .style('pointer-events', 'none')
              .style('text-shadow', '1px 1px 2px rgba(255,255,255,0.8)')  // Sombra para mejor legibilidad
              .text(secondLineText);
          }
        } else {
          // Etiqueta externa con línea de conexión (líder) para segmentos pequeños o donut
          // Calcular posición de la etiqueta externa
          const outerRadius = radius + 35; // Radio exterior para etiquetas (aumentado para más espacio)
          const labelX = Math.cos(midAngle) * outerRadius;
          const labelY = Math.sin(midAngle) * outerRadius;
          
          // Punto en el borde del arco (donde comienza la línea)
          const arcEdgeX = Math.cos(midAngle) * radius;
          const arcEdgeY = Math.sin(midAngle) * radius;
          
          // Punto intermedio para una línea más elegante
          const midRadius = radius + 18;
          const midX = Math.cos(midAngle) * midRadius;
          const midY = Math.sin(midAngle) * midRadius;
          
          // Línea de conexión desde el borde del arco hasta la etiqueta
          // Usar path para crear una línea polilínea
          const linePath = d3.path();
          linePath.moveTo(arcEdgeX, arcEdgeY);
          linePath.lineTo(midX, midY);
          linePath.lineTo(labelX, labelY);
          
          group.append('path')
            .attr('d', linePath.toString())
            .attr('fill', 'none')
            .attr('stroke', '#666')
            .attr('stroke-width', 1.5)
            .style('pointer-events', 'none');
          
          // Etiqueta de texto externa
          const textAnchor = labelX > 0 ? 'start' : 'end';
          const dx = labelX > 0 ? 12 : -12;
          
          // Etiqueta principal (nombre de la categoría)
          // Siempre mostrar el nombre de la categoría
          group.append('text')
            .attr('x', labelX)
            .attr('y', labelY)
            .attr('text-anchor', textAnchor)
            .attr('dominant-baseline', 'middle')
            .attr('dx', dx)
            .attr('dy', showPercentage || showValue ? '-0.4em' : '0')
            .style('font-size', `${labelFontSize}px`)
            .style('font-weight', '600')
            .style('fill', '#000000')
            .style('font-family', 'Arial, sans-serif')
            .style('pointer-events', 'none')
            .text(d.data.category);
          
          // Si también mostrar porcentaje o valor, agregar segunda línea debajo
          if (showPercentage || showValue) {
            const secondLineText = showPercentage && showValue 
              ? `${d.data.value.toFixed(1)} (${percentage.toFixed(1)}%)`
              : showPercentage 
                ? `${percentage.toFixed(1)}%`
                : `${d.data.value.toFixed(1)}`;
            
            group.append('text')
              .attr('x', labelX)
              .attr('y', labelY)
              .attr('text-anchor', textAnchor)
              .attr('dominant-baseline', 'middle')
              .attr('dx', dx)
              .attr('dy', '1.2em')
              .style('font-size', `${labelFontSize - 2}px`)
              .style('font-weight', '400')
              .style('fill', '#555555')
              .style('font-family', 'Arial, sans-serif')
              .style('pointer-events', 'none')
              .text(secondLineText);
          }
        }
      });
    }
  }

  /**
   * Violin plot simplificado (perfiles de densidad normalizada)
   */
  function renderViolinD3(container, spec, d3, divId) {
    const violins = spec.data || [];
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 60, left: 60 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const categories = violins.map(v => v.category);
    const yAll = violins.flatMap(v => v.profile.map(p => p.y));
    const x = d3.scaleBand().domain(categories).range([0, chartWidth]).padding(0.2);
    const y = d3.scaleLinear().domain(d3.extent(yAll)).nice().range([chartHeight, 0]);
    const wScale = d3.scaleLinear().domain([0, 1]).range([0, (x.bandwidth() / 2) || 20]);
    const color = d3.scaleOrdinal(d3.schemeSet2).domain(categories);

    violins.forEach(v => {
      const cx = x(v.category) + x.bandwidth() / 2;
      const area = d3.area()
        .x0(p => cx - wScale(p.w))
        .x1(p => cx + wScale(p.w))
        .y(p => y(p.y))
        .curve(d3.curveCatmullRom.alpha(0.5));
      g.append('path')
        .datum(v.profile)
        .attr('d', area)
        .attr('fill', color(v.category))
        .attr('opacity', 0.7)
        .attr('stroke', '#333')
        .attr('stroke-width', 1);
    });

    if (spec.axes !== false) {
      const xAxis = g.append('g').attr('transform', `translate(0,${chartHeight})`).call(d3.axisBottom(x));
      xAxis.selectAll('text').style('font-size', '12px').style('font-weight', '600').style('fill', '#000000');
      xAxis.selectAll('line, path').style('stroke', '#000000').style('stroke-width', '1.5px');
      
      const yAxis = g.append('g').call(d3.axisLeft(y));
      yAxis.selectAll('text').style('font-size', '12px').style('font-weight', '600').style('fill', '#000000');
      yAxis.selectAll('line, path').style('stroke', '#000000').style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  /**
   * RadViz simple
   */
  function renderRadVizD3(container, spec, d3, divId) {
    const points = spec.data || [];
    const width = container.clientWidth || 520;
    const height = Math.max(container.clientHeight || 380, 380);
    const margin = { top: 20, right: 20, bottom: 40, left: 40 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${margin.left + chartWidth/2},${margin.top + chartHeight/2})`);

    const radius = Math.min(chartWidth, chartHeight) / 2 - 10;
    // circle axis
    g.append('circle').attr('r', radius).attr('fill', 'none').attr('stroke', '#aaa');

    // anchors (features)
    const feats = spec.features || [];
    const anchorPos = feats.map((f, i) => {
      const ang = 2 * Math.PI * i / Math.max(1, feats.length);
      return { x: radius * Math.cos(ang), y: radius * Math.sin(ang), name: f };
    });
    g.selectAll('.anchor').data(anchorPos).enter().append('circle')
      .attr('class', 'anchor').attr('r', 3).attr('cx', d => d.x).attr('cy', d => d.y).attr('fill', '#555');
    g.selectAll('.alabel').data(anchorPos).enter().append('text')
      .attr('class', 'alabel').attr('x', d => d.x).attr('y', d => d.y)
      .attr('dx', 4).attr('dy', -4).style('font-size', '10px').text(d => d.name);

    // scale from [-1,1] to circle radius (points expected in that range)
    const toX = d3.scaleLinear().domain([-1, 1]).range([-radius, radius]);
    const toY = d3.scaleLinear().domain([-1, 1]).range([-radius, radius]);
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    g.selectAll('.rvpt')
      .data(points)
      .enter()
      .append('circle')
      .attr('class', 'rvpt')
      .attr('cx', d => toX(d.x))
      .attr('cy', d => toY(d.y))
      .attr('r', 4)
      .attr('fill', d => d.category ? color(d.category) : '#4a90e2')
      .attr('opacity', 0.7);
  }
  
  /**
   * Boxplot con D3.js
   */
  function renderBoxplotD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 400, 350);
    const width = dims.width;
    const height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 40, left: 50 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3
    const x = d3.scaleBand()
      .domain(data.map(d => d.category))
      .range([0, chartWidth])
      .padding(0.2);
    
    const y = d3.scaleLinear()
      .domain([d3.min(data, d => d.lower), d3.max(data, d => d.upper)])
      .nice()
      .range([chartHeight, 0]);
    
    // Dibujar boxplot para cada categoría
    data.forEach((d) => {
      const xPos = x(d.category);
      const boxWidth = x.bandwidth();
      const centerX = xPos + boxWidth / 2;
      
      // Bigotes (whiskers)
      g.append('line')
        .attr('x1', centerX)
        .attr('x2', centerX)
        .attr('y1', y(d.lower))
        .attr('y2', y(d.q1))
        .attr('stroke', '#000')
        .attr('stroke-width', 2);
      
      g.append('line')
        .attr('x1', centerX)
        .attr('x2', centerX)
        .attr('y1', y(d.q3))
        .attr('y2', y(d.upper))
        .attr('stroke', '#000')
        .attr('stroke-width', 2);
      
      // Caja (box)
      g.append('rect')
        .attr('x', xPos)
        .attr('y', y(d.q3))
        .attr('width', boxWidth)
        .attr('height', y(d.q1) - y(d.q3))
        .attr('fill', spec.color || '#4a90e2')
        .attr('stroke', '#000')
        .attr('stroke-width', 2);
      
      // Mediana (median line)
      g.append('line')
        .attr('x1', xPos)
        .attr('x2', xPos + boxWidth)
        .attr('y1', y(d.median))
        .attr('y2', y(d.median))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    });
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Histograma con D3.js
   */
  function renderHistogramD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 40, left: 50 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3
    const x = d3.scaleBand()
      .domain(data.map(d => d.bin))
      .range([0, chartWidth])
      .padding(0.1);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.count) || 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Barras del histograma
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.bin))
      .attr('y', chartHeight)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', spec.color || '#4a90e2')
      .transition()
      .duration(800)
      .attr('y', d => y(d.count))
      .attr('height', d => chartHeight - y(d.count));
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x).tickFormat(d => d.toFixed(2)));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Gráfico de barras con D3.js
   */
  function renderBarChartD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 40, left: 50 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minWidth = margin.left + margin.right + Math.max(chartWidth, 200); // Mínimo 200px para el gráfico
    if (width < minWidth) {
      width = minWidth;
    }
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3
    const x = d3.scaleBand()
      .domain(data.map(d => d.category))
      .range([0, chartWidth])
      .padding(0.2);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) || 100])
      .nice()
      .range([chartHeight, 0]);
    
  if (spec.grouped) {
    // Grouped/nested bars
    const groups = spec.groups || [];
    const series = spec.series || [];
    const x0 = d3.scaleBand().domain(groups).range([0, chartWidth]).padding(0.2);
    const x1 = d3.scaleBand().domain(series).range([0, x0.bandwidth()]).padding(0.1);
    const y2 = d3.scaleLinear().domain([0, d3.max(spec.data, d => d.value) || 100]).nice().range([chartHeight, 0]);
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(series);

    const groupG = g.selectAll('.g-group')
      .data(groups)
      .enter()
      .append('g')
      .attr('class', 'g-group')
      .attr('transform', d => `translate(${x0(d)},0)`);

    groupG.selectAll('rect')
      .data(gname => series.map(sname => ({ group: gname, series: sname, value: (spec.data.find(d => d.group === gname && d.series === sname)?.value) || 0 })))
      .enter()
      .append('rect')
      .attr('x', d => x1(d.series))
      .attr('y', chartHeight)
      .attr('width', x1.bandwidth())
      .attr('height', 0)
      .attr('fill', d => color(d.series))
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (!spec.interactive) return;
        sendEvent(divId, 'select', {
          type: 'select',
          items: [{ group: d.group, series: d.series }],
          indices: [],
          original_items: [d]
        });
      })
      .transition()
      .duration(700)
      .attr('y', d => y2(d.value))
      .attr('height', d => chartHeight - y2(d.value));

    // axes for grouped version (renderizar por defecto a menos que axes === false)
    if (spec.axes !== false) {
      const xAxis = g.append('g').attr('transform', `translate(0,${chartHeight})`).call(d3.axisBottom(x0));
      xAxis.selectAll('text').style('font-size', '12px').style('font-weight', '600').style('fill', '#000000');
      xAxis.selectAll('line, path').style('stroke', '#000000').style('stroke-width', '1.5px');
      
      const yAxis = g.append('g').call(d3.axisLeft(y2));
      yAxis.selectAll('text').style('font-size', '12px').style('font-weight', '600').style('fill', '#000000');
      yAxis.selectAll('line, path').style('stroke', '#000000').style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  } else {
    // Simple bars
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.category))
      .attr('y', chartHeight)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', spec.color || '#4a90e2')
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (spec.interactive) {
          const index = data.indexOf(d);
          const originalRow = d._original_row || d;
          sendEvent(divId, 'select', {
            type: 'select',
            items: [originalRow],
            indices: [index],
            original_items: [d]
          });
        }
      })
      .on('mouseenter', function() {
        if (spec.interactive) {
          d3.select(this).attr('fill', spec.hoverColor || '#357abd');
        }
      })
      .on('mouseleave', function() {
        if (spec.interactive) {
          d3.select(this).attr('fill', spec.color || '#4a90e2');
        }
      })
      .transition()
      .duration(800)
      .attr('y', d => y(d.value))
      .attr('height', d => chartHeight - y(d.value));
  }
    
    // Ejes con D3 - Texto NEGRO y visible (renderizar por defecto a menos que axes === false)
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')  // NEGRO
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')  // NEGRO
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Gráfico de dispersión con D3.js
   */
  function renderScatterPlotD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 20, bottom: 40, left: 50 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain(d3.extent(data, d => d.y) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Optional size scale from data.size
    const hasSize = data.length > 0 && data[0] && (data[0].size !== undefined && data[0].size !== null);
    const sizeRange = spec.sizeRange || [3, 9];
    const sizeScale = hasSize
      ? d3.scaleLinear()
          .domain(d3.extent(data, d => +d.size))
          .range(sizeRange)
          .nice()
      : null;
    const getRadius = d => {
      if (sizeScale) return sizeScale(+d.size);
      return spec.pointRadius || 4;
    };

    // Puntos con D3 (renderizar PRIMERO)
    const dots = g.selectAll('.dot')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', d => x(d.x))
      .attr('cy', d => y(d.y))
      .attr('r', d => getRadius(d))
      .attr('fill', d => {
        if (d.color) return d.color;
        if (spec.colorMap && d.category) {
          return spec.colorMap[d.category] || spec.color || '#4a90e2';
        }
        return spec.color || '#4a90e2';
      })
      .attr('opacity', 0.7)
      .style('cursor', spec.interactive ? 'crosshair' : 'default')
      .on('click', function(event, d) {
        // Solo procesar clicks si NO estamos en modo brush
        if (spec.interactive) {
          event.stopPropagation();
          const index = data.indexOf(d);
          const originalRow = d._original_row || d;
          sendEvent(divId, 'point_click', {
            type: 'point_click',
            point: originalRow,
            index: index,
            original_point: d
          });
        }
      })
      .on('mouseenter', function() {
        if (!spec.interactive) return;
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', d => (getRadius(d)) * 1.5)
          .attr('opacity', 1);
      })
      .on('mouseleave', function() {
        if (!spec.interactive) return;
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', d => getRadius(d))
          .attr('opacity', 0.7);
      });
    
    // BRUSH para selección de área (renderizar DESPUÉS de los puntos para estar visualmente encima)
    // El brush captura eventos porque está en una capa superior
    if (spec.interactive) {
      // Crear grupo de brush que estará en la parte superior
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer');
      
      const brush = d3.brush()
        .extent([[0, 0], [chartWidth, chartHeight]])
        .on('start', function(event) {
          // Cuando comienza el brush, desactivar eventos de puntos temporalmente
          g.selectAll('.dot')
            .style('pointer-events', 'none')
            .style('opacity', 0.4);
        })
        .on('brush', function(event) {
          if (!event.selection) {
            // Si no hay selección, resetear
            g.selectAll('.dot')
              .style('opacity', 0.7)
              .attr('r', d => getRadius(d));
            return;
          }
          
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Resaltar puntos dentro de la selección
          g.selectAll('.dot')
            .style('opacity', d => {
              const px = x(d.x);
              const py = y(d.y);
              const inSelection = px >= x0 && px <= x1 && py >= y0 && py <= y1;
              return inSelection ? 1 : 0.2;
            })
            .attr('r', d => {
              const px = x(d.x);
              const py = y(d.y);
              const inSelection = px >= x0 && px <= x1 && py >= y0 && py <= y1;
              const base = getRadius(d);
              return inSelection ? base * 1.3 : base;
            });
        })
        .on('end', function(event) {
          // Si no hay selección, resetear y salir
          if (!event.selection) {
            g.selectAll('.dot')
              .style('pointer-events', 'all')
              .style('opacity', 0.7)
              .attr('r', d => getRadius(d));
            return;
          }
          
          // Obtener coordenadas de la selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Convertir coordenadas de píxeles a valores de datos
          const xInverted0 = x.invert(Math.min(x0, x1));
          const xInverted1 = x.invert(Math.max(x0, x1));
          const yInverted0 = y.invert(Math.max(y0, y1));  // y está invertido
          const yInverted1 = y.invert(Math.min(y0, y1));
          
          // Filtrar puntos dentro de la selección usando valores de datos
          const selected = data.filter(d => {
            return d.x >= Math.min(xInverted0, xInverted1) && 
                   d.x <= Math.max(xInverted0, xInverted1) &&
                   d.y >= Math.min(yInverted0, yInverted1) && 
                   d.y <= Math.max(yInverted0, yInverted1);
          });
          
          // Extraer filas originales completas si existen
          const selectedItems = selected.map(d => {
            return d._original_row || d;
          });
          
          // Obtener letra del scatter plot desde el spec o del contenedor
          // El container es la celda, que tiene un data-letter attribute
          let scatterLetter = spec.__scatter_letter__ || null;
          if (!scatterLetter && container) {
            // El container es la celda, obtener la letra del attribute
            const letterAttr = container.getAttribute('data-letter');
            if (letterAttr) {
              scatterLetter = letterAttr;
            } else {
              // Si no hay attribute, intentar obtenerlo del ID de la celda
              // El ID tiene formato: {divId}-cell-{letter}-{r}-{c}
              const idMatch = container.id && container.id.match(/-cell-([A-Z])-/);
              if (idMatch) {
                scatterLetter = idMatch[1];
              }
            }
          }
          
          // Enviar el evento de selección con filas originales
          if (selectedItems.length > 0) {
            sendEvent(divId, 'select', {
              type: 'select',
              items: selectedItems,
              count: selected.length,
              original_items: selected,
              __scatter_letter__: scatterLetter
            });
          }
          
          // Mantener puntos resaltados brevemente, luego resetear
          setTimeout(() => {
            g.selectAll('.dot')
              .style('pointer-events', 'all')
              .transition()
              .duration(300)
              .style('opacity', 0.7)
              .attr('r', d => getRadius(d));
            
            // Limpiar el brush visual después de un breve delay
            brushGroup.call(brush.move, null);
          }, 200);
        });
      
      // Aplicar brush al grupo (esto lo renderiza visualmente encima de los puntos)
      brushGroup.call(brush);
      
      // Estilo del brush overlay (área de captura de eventos)
      brushGroup.selectAll('.overlay')
        .style('cursor', 'crosshair')
        .style('pointer-events', 'all');  // Asegurar que capture eventos
      
      // Estilo del brush selection (área seleccionada)
      brushGroup.selectAll('.selection')
        .attr('stroke', '#333')
        .attr('stroke-width', '2px')
        .attr('stroke-dasharray', '5,5')
        .attr('fill', 'steelblue')
        .attr('fill-opacity', 0.1)
        .style('pointer-events', 'none');  // La selección no debe capturar eventos
      
      // Estilo de los handles del brush (esquinas)
      brushGroup.selectAll('.handle')
        .style('cursor', 'move')
        .style('pointer-events', 'all');  // Los handles deben capturar eventos
    }
    
    // Ejes con texto NEGRO y visible (renderizar por defecto a menos que axes === false)
    // IMPORTANTE: Renderizar ejes DESPUÉS del brush para que estén debajo visualmente
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x).ticks(6));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(6));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  // ==========================================
  // Carga de D3.js (Optimizado para Colab)
  // ==========================================
  
  // Cache global para la promesa de D3
  let _d3Promise = null;
  
  /**
   * Asegura que D3.js esté cargado y listo para usar
   * @param {number} timeout - Timeout en milisegundos (por defecto 10000)
   * @returns {Promise} Promise que se resuelve con d3 cuando está listo
   */
  function ensureD3(timeout = 10000) {
    // Si D3 ya está disponible, retornar inmediatamente
    if (global.d3) {
      return Promise.resolve(global.d3);
    }
    
    // Si ya hay una promesa en curso, retornarla para evitar múltiples cargas
    if (_d3Promise) {
      return _d3Promise;
    }
    
    // Crear nueva promesa para cargar D3
    _d3Promise = new Promise((resolve, reject) => {
      // Buscar script existente por ID único o por src
      const scriptId = 'bestlib-d3-script';
      let existingScript = document.getElementById(scriptId);
      
      // Si no existe por ID, buscar por src
      if (!existingScript) {
        existingScript = document.querySelector('script[src*="d3"][src*="d3.min.js"], script[src*="d3"][src*="d3.js"]');
      }
      
      if (existingScript) {
        // Script ya existe, esperar a que se cargue
        const checkD3 = setInterval(() => {
          if (global.d3) {
            clearInterval(checkD3);
            _d3Promise = null; // Reset cache para permitir re-chequeo si falla
            resolve(global.d3);
          }
        }, 100);
        
        // Timeout para evitar esperar indefinidamente
        setTimeout(() => {
          clearInterval(checkD3);
          if (global.d3) {
            _d3Promise = null;
            resolve(global.d3);
          } else {
            _d3Promise = null;
            reject(new Error('Timeout esperando D3.js (script existente pero no se inicializó)'));
          }
        }, timeout);
        return;
      }
      
      // CDNs disponibles (intentar en orden)
      const cdns = [
        'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js',
        'https://d3js.org/d3.v7.min.js',
        'https://unpkg.com/d3@7/dist/d3.min.js'
      ];
      
      let cdnIndex = 0;
      
      function tryLoadCDN(index) {
        if (index >= cdns.length) {
          _d3Promise = null;
          reject(new Error('No se pudo cargar D3.js desde ningún CDN disponible'));
          return;
        }
        
        const script = document.createElement('script');
        script.id = scriptId;
        script.src = cdns[index];
        script.async = true;
        
        script.onload = () => {
          // Esperar un momento para que D3 se inicialice
          setTimeout(() => {
            if (global.d3) {
              _d3Promise = null; // Reset cache
              resolve(global.d3);
            } else {
              // Si no se inicializó, intentar siguiente CDN
              script.remove();
              tryLoadCDN(index + 1);
            }
          }, 50);
        };
        
        script.onerror = () => {
          // Si falla, intentar siguiente CDN
          script.remove();
          console.warn('Falló carga de D3 desde ' + cdns[index] + ', intentando siguiente CDN...');
          tryLoadCDN(index + 1);
        };
        
        document.head.appendChild(script);
      }
      
      tryLoadCDN(0);
    });
    
    // Limpiar cache después de resolver o rechazar (con un pequeño delay)
    _d3Promise.then(
      () => setTimeout(() => { _d3Promise = null; }, 1000),
      () => setTimeout(() => { _d3Promise = null; }, 1000)
    );
    
    return _d3Promise;
  }

  // ==========================================
  // Código muerto eliminado (líneas 1443-1761)
  // Las funciones renderD3, renderBarChart, renderScatterPlot fueron reemplazadas
  // por renderChartD3, renderBarChartD3, renderScatterPlotD3 que son las versiones activas
  // ==========================================

  // Exponer funciones globalmente
  global.render = render;
})(window);