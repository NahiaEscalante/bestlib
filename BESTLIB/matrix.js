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
    // Validar que spec tenga type
    if (!spec || !spec.type) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: Spec no tiene tipo definido</strong><br/>' +
        '<small>Keys en spec: ' + (spec ? Object.keys(spec).join(', ') : 'spec es null/undefined') + '</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('renderChartD3: Spec inválido', { spec, divId });
      return;
    }
    
    const chartType = spec.type;
    
    if (chartType === 'bar') {
      renderBarChartD3(container, spec, d3, divId);
    } else if (chartType === 'scatter') {
      renderScatterPlotD3(container, spec, d3, divId);
    } else if (chartType === 'histogram') {
      renderHistogramD3(container, spec, d3, divId);
    } else if (chartType === 'boxplot') {
      renderBoxplotD3(container, spec, d3, divId);
    } else if (chartType === 'heatmap') {
      renderHeatmapD3(container, spec, d3, divId);
    } else if (chartType === 'line') {
      renderLineD3(container, spec, d3, divId);
    } else if (chartType === 'pie') {
      renderPieD3(container, spec, d3, divId);
    } else if (chartType === 'violin') {
      renderViolinD3(container, spec, d3, divId);
    } else if (chartType === 'radviz') {
      renderRadVizD3(container, spec, d3, divId);
    } else {
      // Tipo de gráfico no soportado aún, mostrar mensaje visible
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: Gráfico tipo "' + chartType + '" no implementado aún</strong><br/>' +
        '<small>Tipos soportados: bar, scatter, histogram, boxplot, heatmap, line, pie, violin, radviz</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('renderChartD3: Tipo de gráfico no soportado', { chartType, spec });
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
    
    // Para correlation heatmap, necesitamos espacio para el colorbar
    const isCorrelation = spec.isCorrelation === true;
    const showValues = spec.showValues === true;
    const colorbarWidth = isCorrelation ? 80 : 0;  // Ancho del colorbar
    const colorbarPadding = isCorrelation ? 20 : 0;  // Padding entre gráfico y colorbar
    
    // Ajustar márgenes para el colorbar
    if (isCorrelation) {
      margin.right = margin.right + colorbarWidth + colorbarPadding;
    }
    
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

    // Para correlation heatmap, asegurar que xLabels e yLabels estén en el mismo orden
    let xLabels = spec.xLabels || Array.from(new Set(data.map(d => d.x)));
    let yLabels = spec.yLabels || Array.from(new Set(data.map(d => d.y)));
    
    // Ordenar las etiquetas de la misma manera si es correlation heatmap
    if (isCorrelation) {
      // Ordenar alfabéticamente para consistencia
      xLabels = [...xLabels].sort();
      yLabels = [...yLabels].sort();
      // Asegurar que ambas listas sean idénticas
      if (xLabels.length === yLabels.length && xLabels.every((val, idx) => val === yLabels[idx])) {
        // Ya están en el mismo orden
      } else {
        // Usar xLabels como referencia y ordenar yLabels igual
        yLabels = [...xLabels];
      }
    }

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(xLabels).range([0, chartWidth]).padding(0.05);
    const y = d3.scaleBand().domain(yLabels).range([0, chartHeight]).padding(0.05);

    const vmin = d3.min(data, d => d.value) ?? 0;
    const vmax = d3.max(data, d => d.value) ?? 1;
    
    // Para correlation heatmap, usar escala divergente centrada en 0
    // INVERTIDA: Rojo para correlación positiva, Azul para correlación negativa
    let color;
    if (isCorrelation) {
      // Escala divergente para correlación (-1 a 1)
      const absMax = Math.max(Math.abs(vmin), Math.abs(vmax));
      // Crear interpolador invertido: azul (negativo) -> blanco (neutral) -> rojo (positivo)
      // d3.interpolateRdBu va de rojo (t=0) a azul (t=1)
      // Queremos: azul (t=0) -> blanco (t=0.5) -> rojo (t=1)
      // Entonces invertimos: usar interpolateRdBu(1 - t) para intercambiar los extremos
      const invertedInterpolator = t => {
        // Para t=0 (negativo), queremos azul: interpolateRdBu(1-0) = interpolateRdBu(1) = azul ✓
        // Para t=0.5 (neutral), queremos blanco: interpolateRdBu(1-0.5) = interpolateRdBu(0.5) = blanco ✓
        // Para t=1 (positivo), queremos rojo: interpolateRdBu(1-1) = interpolateRdBu(0) = rojo ✓
        return d3.interpolateRdBu(1 - t);
      };
      // Usar scaleDiverging con interpolador invertido
      // domain: [-absMax, 0, absMax] donde -absMax es negativo, 0 es neutral, absMax es positivo
      color = d3.scaleDiverging(invertedInterpolator)
        .domain([-absMax, 0, absMax]);
    } else if (spec.colorScale === 'diverging') {
      color = d3.scaleDiverging(d3.interpolateRdBu)
        .domain([vmin, (vmin + vmax) / 2, vmax]);
    } else {
      color = d3.scaleSequential([vmin, vmax], d3.interpolateViridis);
    }

    // Crear mapa de datos para acceso rápido
    const dataMap = new Map();
    data.forEach(d => {
      dataMap.set(`${d.x}|${d.y}`, d.value);
    });

    // Renderizar celdas
    const cells = g.selectAll('rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('x', d => x(String(d.x)))
      .attr('y', d => y(String(d.y)))
      .attr('width', x.bandwidth())
      .attr('height', y.bandwidth())
      .attr('fill', d => color(d.value))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .attr('opacity', 1);

    // Mostrar valores numéricos si está habilitado
    if (showValues) {
      g.selectAll('.heatmap-text')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'heatmap-text')
        .attr('x', d => x(String(d.x)) + x.bandwidth() / 2)
        .attr('y', d => y(String(d.y)) + y.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'middle')
        .attr('font-size', Math.min(x.bandwidth(), y.bandwidth()) / 3 + 'px')
        .attr('fill', d => {
          // Color del texto basado en el color de fondo (negro o blanco)
          const bgColor = color(d.value);
          // Convertir a RGB y calcular luminosidad
          const rgb = d3.rgb(bgColor);
          const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
          return luminance > 0.5 ? '#000' : '#fff';
        })
        .attr('font-weight', 'bold')
        .text(d => d.value.toFixed(2))
        .attr('opacity', 0)
        .transition()
        .duration(500)
        .attr('opacity', 1);
    }

    // Renderizar colorbar para correlation heatmap
    if (isCorrelation) {
      // Calcular absMax una sola vez (ya se calculó antes)
      const absMax = Math.max(Math.abs(vmin), Math.abs(vmax));
      
      const colorbarHeight = chartHeight * 0.6;
      const colorbarY = (chartHeight - colorbarHeight) / 2;
      const colorbarX = chartWidth + colorbarPadding;
      const colorbarGroup = g.append('g').attr('class', 'colorbar-group');
      
      // Crear gradiente para el colorbar
      const defs = svg.append('defs');
      const gradientId = `colorbar-gradient-${divId}-${Date.now()}`; // ID único para evitar conflictos
      const gradient = defs.append('linearGradient')
        .attr('id', gradientId)
        .attr('x1', '0%')
        .attr('x2', '0%')
        .attr('y1', '0%')
        .attr('y2', '100%');
      
      const steps = 100; // Más pasos para gradiente más suave
      for (let i = 0; i <= steps; i++) {
        // Calcular valor desde absMax hasta -absMax (de arriba a abajo)
        // Pero queremos que el colorbar muestre: rojo (positivo) arriba, azul (negativo) abajo
        // Como usamos un interpolador invertido, el color ya está correcto
        const t = i / steps; // 0 a 1
        const value = absMax - (2 * absMax * t); // absMax a -absMax (de arriba a abajo)
        try {
          const colorValue = color(value);
          gradient.append('stop')
            .attr('offset', `${(i / steps) * 100}%`)
            .attr('stop-color', colorValue);
        } catch (e) {
          // Si hay error, usar color por defecto (rojo para positivo, azul para negativo)
          console.warn('Error al calcular color para colorbar:', e);
          // Rojo para valores positivos (arriba), azul para valores negativos (abajo)
          const defaultColor = i < steps / 2 ? '#b2182b' : '#2166ac'; // Rojo a azul (invertido)
          gradient.append('stop')
            .attr('offset', `${(i / steps) * 100}%`)
            .attr('stop-color', defaultColor);
        }
      }
      
      // Rectángulo del colorbar
      colorbarGroup.append('rect')
        .attr('x', colorbarX)
        .attr('y', colorbarY)
        .attr('width', colorbarWidth)
        .attr('height', colorbarHeight)
        .attr('fill', `url(#${gradientId})`)
        .attr('stroke', '#000')
        .attr('stroke-width', 1);
      
      // Etiquetas del colorbar
      const colorbarScale = d3.scaleLinear()
        .domain([absMax, -absMax])  // De arriba (absMax) a abajo (-absMax)
        .range([colorbarY, colorbarY + colorbarHeight]);
      
      const colorbarAxis = d3.axisRight(colorbarScale)
        .ticks(5)
        .tickFormat(d3.format('.2f'));
      
      const axisGroup = colorbarGroup.append('g')
        .attr('transform', `translate(${colorbarX + colorbarWidth}, 0)`)
        .call(colorbarAxis);
      
      axisGroup.selectAll('text')
        .style('font-size', '10px')
        .style('fill', '#000');
      
      axisGroup.selectAll('line')
        .style('stroke', '#000')
        .style('stroke-width', 1);
      
      axisGroup.selectAll('path')
        .style('stroke', '#000')
        .style('stroke-width', 1);
      
      // Título del colorbar
      colorbarGroup.append('text')
        .attr('x', colorbarX + colorbarWidth / 2)
        .attr('y', colorbarY - 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('fill', '#000')
        .text('Correlación');
      
      // Etiqueta adicional: Rojo = Positivo, Azul = Negativo
      colorbarGroup.append('text')
        .attr('x', colorbarX + colorbarWidth / 2)
        .attr('y', colorbarY + colorbarHeight + 20)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#666')
        .text('Rojo: Positivo | Azul: Negativo');
    }

    if (spec.axes !== false) {
      const tickFontSize = spec.tickFontSize || 12;
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      xAxis.selectAll('text')
        .style('font-size', `${tickFontSize}px`)
        .style('fill', '#000')
        .attr('transform', 'rotate(-45)')
        .attr('dx', '-0.5em')
        .attr('dy', '0.5em')
        .style('text-anchor', 'end');
      
      const yAxis = g.append('g').call(d3.axisLeft(y));
      yAxis.selectAll('text')
        .style('font-size', `${tickFontSize}px`)
        .style('fill', '#000');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  /**
   * Line chart (multi-series) con hover sincronizado
   */
  function renderLineD3(container, spec, d3, divId) {
    // Limpiar contenedor primero
    container.innerHTML = '';
    
    const seriesMap = spec.series || {};
    const specKeys = Object.keys(spec);
    
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 20, right: 150, bottom: 40, left: 50 }; // Más espacio a la derecha para leyenda
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

    // Obtener todos los puntos para calcular dominios
    const allPoints = [];
    const seriesNames = Object.keys(seriesMap);
    
    // Validar que haya series
    if (seriesNames.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay series para mostrar</strong><br/>' +
        '<small>Keys en spec: ' + specKeys.join(', ') + '</small><br/>' +
        '<small>seriesMap está vacío o no existe</small><br/>' +
        '<small>Verifica que los datos contengan la columna de series especificada (series_col)</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Line Chart: No hay series en seriesMap', { seriesMap, spec, specKeys });
      return;
    }
    
    // Recopilar todos los puntos de todas las series
    seriesNames.forEach(name => {
      const pts = seriesMap[name];
      if (pts && Array.isArray(pts) && pts.length > 0) {
        // Validar que cada punto tenga x e y
        const validPts = pts.filter(p => p != null && p.x != null && !isNaN(p.x) && p.y != null && !isNaN(p.y));
        if (validPts.length > 0) {
          allPoints.push(...validPts);
        }
      }
    });

    if (allPoints.length === 0) {
      // Información detallada sobre cada serie
      const seriesInfo = seriesNames.map(name => {
        const pts = seriesMap[name];
        const count = pts && Array.isArray(pts) ? pts.length : 0;
        const validCount = pts && Array.isArray(pts) ? pts.filter(p => p != null && p.x != null && !isNaN(p.x) && p.y != null && !isNaN(p.y)).length : 0;
        return `${name}: ${count} puntos (${validCount} válidos)`;
      }).join('<br/>');
      
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay datos válidos para mostrar</strong><br/>' +
        '<small>Series encontradas: ' + seriesNames.join(', ') + '</small><br/>' +
        '<small>Información de series:<br/>' + seriesInfo + '</small><br/>' +
        '<small>Verifica que los datos tengan valores válidos para x e y</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Line Chart: No hay puntos válidos', { seriesNames, seriesMap, spec });
      return;
    }

    // Calcular dominios
    const xExtent = d3.extent(allPoints, d => d.x);
    const yExtent = d3.extent(allPoints, d => d.y);
    
    // Asegurar que los dominios no sean iguales
    if (xExtent[0] === xExtent[1]) {
      xExtent[0] = xExtent[0] - 1;
      xExtent[1] = xExtent[1] + 1;
    }
    if (yExtent[0] === yExtent[1]) {
      yExtent[0] = yExtent[0] - 1;
      yExtent[1] = yExtent[1] + 1;
    }

    const x = d3.scaleLinear().domain(xExtent).nice().range([0, chartWidth]);
    const y = d3.scaleLinear().domain(yExtent).nice().range([chartHeight, 0]);

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(seriesNames);
    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveMonotoneX)  // Curva suave
      .defined(d => d != null && d.x != null && !isNaN(d.x) && d.y != null && !isNaN(d.y));

    // Contador de series renderizadas
    let renderedSeries = 0;
    const errors = [];
    
    // Renderizar líneas (ordenar puntos por x antes de dibujar)
    seriesNames.forEach(name => {
      const pts = seriesMap[name];
      if (!pts || !Array.isArray(pts) || pts.length === 0) {
        errors.push(`Serie "${name}": No tiene datos válidos`);
        return;
      }
      
      // Filtrar puntos válidos y ordenar por x
      const validPts = pts.filter(p => p != null && p.x != null && !isNaN(p.x) && p.y != null && !isNaN(p.y));
      if (validPts.length === 0) {
        errors.push(`Serie "${name}": No tiene puntos válidos después del filtrado`);
        return;
      }
      
      const sortedPts = [...validPts].sort((a, b) => a.x - b.x);
      
      // Crear path para esta serie
      const pathData = line(sortedPts);
      if (!pathData || pathData === 'M0,0' || pathData.length < 10) {
        errors.push(`Serie "${name}": No se pudo generar path (pathData: ${pathData ? pathData.substring(0, 20) : 'null'})`);
        return;
      }
      
      // Dibujar la línea
      g.append('path')
        .datum(sortedPts)
        .attr('fill', 'none')
        .attr('stroke', color(name))
        .attr('stroke-width', spec.strokeWidth || 2)
        .attr('d', pathData)
        .attr('opacity', 1)  // Mostrar inmediatamente
        .attr('class', `line-series-${name.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`);
      
      renderedSeries++;
    });
    
    // Si no se renderizó ninguna serie, mostrar error visible
    if (renderedSeries === 0) {
      // Información detallada del spec recibido
      const specInfo = Object.keys(spec).map(key => {
        const value = spec[key];
        if (key === 'series') {
          const seriesKeys = Object.keys(value || {});
          return `series: ${seriesKeys.length} series (${seriesKeys.join(', ')})`;
        }
        if (typeof value === 'object' && value !== null) {
          return `${key}: ${Array.isArray(value) ? 'array[' + value.length + ']' : 'object'}`;
        }
        return `${key}: ${String(value)}`;
      }).join('<br/>');
      
      const errorMsg = '<div style="padding: 20px; text-align: left; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px; font-family: monospace; font-size: 12px;">' +
        '<strong style="font-size: 14px;">❌ Error: No se pudo renderizar ninguna serie en Line Chart</strong><br/><br/>' +
        '<strong>Errores encontrados:</strong><br/>' +
        '<small style="color: #c62828;">' + (errors.length > 0 ? errors.join('<br/>') : 'No se encontraron errores específicos') + '</small><br/><br/>' +
        '<strong>Información del spec recibido:</strong><br/>' +
        '<small style="color: #555;">' + specInfo + '</small><br/><br/>' +
        '<strong>Series en seriesMap:</strong><br/>' +
        '<small style="color: #555;">' + seriesNames.join(', ') + ' (total: ' + seriesNames.length + ')</small><br/><br/>' +
        '<strong>Sugerencias:</strong><br/>' +
        '<small style="color: #555;">1. Verifica que los datos tengan la columna de series especificada (series_col)<br/>' +
        '2. Verifica que los datos tengan valores válidos para x e y<br/>' +
        '3. Verifica que los valores numéricos no sean NaN o null</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Line Chart: Errores al renderizar', { errors, seriesMap, spec, seriesNames });
      return;
    }

    // Crear tooltip (usar ID único para evitar conflictos)
    const tooltipId = `line-tooltip-${divId}`;
    let tooltip = d3.select(`#${tooltipId}`);
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div')
        .attr('id', tooltipId)
        .attr('class', 'line-chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '10px')
        .style('border-radius', '4px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)');
    }

    // Puntos invisibles para hover y tooltip
    seriesNames.forEach(name => {
      const pts = seriesMap[name];
      if (!pts || !Array.isArray(pts) || pts.length === 0) return;
      
      // Filtrar puntos válidos y ordenar
      const validPts = pts.filter(p => p != null && p.x != null && !isNaN(p.x) && p.y != null && !isNaN(p.y));
      if (validPts.length === 0) return;
      
      const sortedPts = [...validPts].sort((a, b) => a.x - b.x);
      const className = `pt-line-${name.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`;
      
      g.selectAll(`.${className}`)
        .data(sortedPts)
        .enter()
        .append('circle')
        .attr('class', className)
        .attr('cx', d => x(d.x))
        .attr('cy', d => y(d.y))
        .attr('r', 4)
        .attr('fill', color(name))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .attr('opacity', 0)
        .style('cursor', 'pointer')
        .on('mouseenter', function(event, d) {
          // Mostrar tooltip
          const mouseX = event.pageX || event.clientX || 0;
          const mouseY = event.pageY || event.clientY || 0;
          
          tooltip
            .style('left', (mouseX + 10) + 'px')
            .style('top', (mouseY - 10) + 'px')
            .style('display', 'block')
            .html(`<strong>${name}</strong><br/>X: ${d.x.toFixed(2)}<br/>Y: ${d.y.toFixed(2)}`)
            .transition()
            .duration(200)
            .style('opacity', 1);
          
          // Resaltar punto actual
          d3.select(this)
            .attr('r', 6)
            .attr('opacity', 1);
          
          // Resaltar línea de esta serie
          g.selectAll(`.line-series-${name.replace(/\s+/g, '-')}`)
            .attr('stroke-width', (spec.strokeWidth || 2) + 1)
            .attr('opacity', 1);
        })
        .on('mouseleave', function() {
          tooltip.transition().duration(200).style('opacity', 0).style('display', 'none');
          d3.select(this).attr('r', 4).attr('opacity', 0);
          g.selectAll(`.line-series-${name.replace(/\s+/g, '-')}`)
            .attr('stroke-width', spec.strokeWidth || 2)
            .attr('opacity', 1);
        });
    });

    // Renderizar ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x).ticks(8));
      
      xAxis.selectAll('text')
        .style('font-size', '11px')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line')
        .style('stroke', '#000000')
        .style('stroke-width', '1px');
      
      xAxis.selectAll('path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(6));
      
      yAxis.selectAll('text')
        .style('font-size', '11px')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line')
        .style('stroke', '#000000')
        .style('stroke-width', '1px');
      
      yAxis.selectAll('path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }

    // Renderizar leyenda si hay múltiples series
    if (seriesNames.length > 1) {
      const legendWidth = 100;
      const legendX = chartWidth + 10;
      const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${legendX}, 0)`);
      
      seriesNames.forEach((name, i) => {
        const legendRow = legend.append('g')
          .attr('transform', `translate(0, ${i * 20})`);
        
        legendRow.append('rect')
          .attr('width', 15)
          .attr('height', 12)
          .attr('fill', color(name));
        
        legendRow.append('text')
          .attr('x', 20)
          .attr('y', 9)
          .attr('font-size', '11px')
          .attr('fill', '#000')
          .text(name);
      });
    }
  }

  /**
   * Función auxiliar para mostrar tooltip del Pie Chart (compatible con Colab)
   */
  function showPieTooltip(event, tooltip, category, value, percentage, container, width, height) {
    // Obtener coordenadas del mouse de manera robusta (compatible con Colab)
    let mouseX = 0;
    let mouseY = 0;
    
    try {
      // Método 1: Usar getBoundingClientRect para obtener posición del contenedor
      const rect = container.getBoundingClientRect();
      
      // Obtener coordenadas del mouse relativo a la ventana
      if (event.clientX !== undefined && event.clientX !== null) {
        // clientX/Y son relativos a la ventana del navegador (funciona en Colab)
        mouseX = event.clientX;
        mouseY = event.clientY;
      } else if (event.pageX !== undefined && event.pageX !== null) {
        // pageX/Y son relativos al documento (puede no estar disponible en Colab)
        mouseX = event.pageX;
        mouseY = event.pageY;
      } else if (event.offsetX !== undefined) {
        // offsetX/Y son relativos al elemento (fallback)
        mouseX = rect.left + event.offsetX;
        mouseY = rect.top + event.offsetY;
      } else {
        // Último recurso: usar coordenadas del centro del gráfico
        mouseX = rect.left + width / 2;
        mouseY = rect.top + height / 2;
      }
    } catch (e) {
      // Si falla todo, usar coordenadas del centro
      try {
        const rect = container.getBoundingClientRect();
        mouseX = rect.left + width / 2;
        mouseY = rect.top + height / 2;
      } catch (e2) {
        mouseX = width / 2;
        mouseY = height / 2;
      }
    }
    
    // Mostrar tooltip con la información
    tooltip
      .style('left', (mouseX + 15) + 'px')
      .style('top', (mouseY - 50) + 'px')
      .style('display', 'block')
      .style('pointer-events', 'none')
      .style('opacity', 1)
      .html(`<strong>${category}</strong><br/>Cantidad: ${value.toFixed(2)}<br/>Porcentaje: ${percentage.toFixed(2)}%`);
  }
  
  /**
   * Pie / Donut con leyenda y tooltips interactivos
   */
  function renderPieD3(container, spec, d3, divId) {
    // Limpiar contenedor
    container.innerHTML = '';
    
    const data = spec.data || [];
    if (data.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos para mostrar</div>';
      return;
    }
    
    const dims = getChartDimensions(container, spec, 320, 240);
    let width = dims.width;
    let height = dims.height;
    
    // Calcular radio del pie chart (más espacio ahora que no hay etiquetas externas)
    const baseRadius = Math.min(width, height) / 2;
    const radius = Math.max(baseRadius - 40, 50); // Radio mínimo de 50px, menos padding
    const innerR = spec.innerRadius != null ? spec.innerRadius : (spec.donut ? radius * 0.5 : 0);
    
    // Ajustar dimensiones para acomodar leyenda a la derecha
    const legendWidth = 150; // Ancho para la leyenda
    const pieWidth = Math.min(width, height);
    const totalWidth = pieWidth + legendWidth + 20; // Espacio adicional entre pie y leyenda
    
    if (width < totalWidth) {
      width = totalWidth;
    }
    
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(data.map(d => d.category));

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');
    
    // Grupo principal para el pie chart (centrado a la izquierda)
    const pieCenterX = pieWidth / 2;
    const pieCenterY = height / 2;
    const g = svg.append('g').attr('transform', `translate(${pieCenterX},${pieCenterY})`);

    const arc = d3.arc().innerRadius(innerR).outerRadius(radius);
    const pie = d3.pie().value(d => d.value).sort(null); // No ordenar para mantener el orden original
    const arcs = pie(data);

    // Calcular el total para porcentajes
    const total = d3.sum(data, d => d.value);
    
    // Crear tooltip (usar ID único para evitar conflictos)
    // Limpiar tooltip existente si existe
    const tooltipId = `pie-tooltip-${divId}`;
    d3.select(`#${tooltipId}`).remove();
    
    const tooltip = d3.select('body').append('div')
      .attr('id', tooltipId)
      .attr('class', 'pie-chart-tooltip')
      .style('position', 'fixed')  // Usar 'fixed' en lugar de 'absolute' para mejor compatibilidad con Colab
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', '#fff')
      .style('padding', '10px 12px')
      .style('border-radius', '6px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('font-size', '13px')
      .style('font-family', 'Arial, sans-serif')
      .style('z-index', 99999)
      .style('display', 'none')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.4)')
      .style('white-space', 'nowrap')
      .style('border', '1px solid rgba(255,255,255,0.2)');
    
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
      .style('cursor', 'pointer')
      .on('click', function(event, d) {
        if (!spec.interactive) return;
        const category = d.data.category;
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
          .attr('stroke-width', 3)
          .attr('transform', 'scale(1.05)'); // Efecto de zoom
        
        // Mostrar tooltip inmediatamente
        const percentage = (d.value / total) * 100;
        showPieTooltip(event, tooltip, d.data.category, d.data.value, percentage, container, width, height);
      })
      .on('mousemove', function(event, d) {
        // Actualizar posición del tooltip mientras el mouse se mueve
        const percentage = (d.value / total) * 100;
        showPieTooltip(event, tooltip, d.data.category, d.data.value, percentage, container, width, height);
      })
      .on('mouseleave', function(event, d) {
        // Restaurar opacidad y stroke
        d3.select(this)
          .attr('opacity', 0.9)
          .attr('stroke-width', 2)
          .attr('transform', 'scale(1)'); // Restaurar escala
        
        // Ocultar tooltip
        tooltip
          .style('opacity', 0)
          .style('display', 'none');
      });
    
    // Crear leyenda a la derecha del pie chart
    const legendX = pieWidth + 20;
    const legendY = (height - (data.length * 25)) / 2; // Centrar verticalmente
    const legend = svg.append('g')
      .attr('class', 'pie-legend')
      .attr('transform', `translate(${legendX}, ${legendY})`);
    
    // Agregar título a la leyenda
    legend.append('text')
      .attr('x', 0)
      .attr('y', -10)
      .style('font-size', '14px')
      .style('font-weight', 'bold')
      .style('fill', '#000')
      .text('Categorías');
    
    // Crear elementos de leyenda
    data.forEach((d, i) => {
      const percentage = (d.value / total) * 100;
      const legendRow = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`)
        .style('cursor', 'pointer')
        .on('mouseenter', function() {
          // Resaltar el segmento correspondiente en el pie
          const correspondingPath = paths.filter(p => p.data.category === d.category);
          correspondingPath
            .attr('opacity', 1)
            .attr('stroke-width', 3)
            .attr('transform', 'scale(1.05)');
        })
        .on('mouseleave', function() {
          // Restaurar el segmento
          const correspondingPath = paths.filter(p => p.data.category === d.category);
          correspondingPath
            .attr('opacity', 0.9)
            .attr('stroke-width', 2)
            .attr('transform', 'scale(1)');
        });
      
      // Círculo de color
      legendRow.append('circle')
        .attr('r', 8)
        .attr('cx', 8)
        .attr('cy', 0)
        .attr('fill', color(d.category))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
      
      // Texto de la categoría (sin porcentaje en la leyenda)
      legendRow.append('text')
        .attr('x', 22)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .style('font-size', '12px')
        .style('fill', '#000')
        .style('font-family', 'Arial, sans-serif')
        .text(d.category);
    });
  }

  /**
   * Violin plot simplificado (perfiles de densidad normalizada)
   */
  function renderViolinD3(container, spec, d3, divId) {
    // Limpiar contenedor
    container.innerHTML = '';
    
    const violins = spec.data || [];
    
    // Validar datos
    if (!violins || violins.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos para mostrar (violins vacío)</div>';
      return;
    }
    
    // Validar que cada violín tenga un perfil válido
    // Validación más flexible: permitir perfiles con al menos 1 punto (dibujar línea)
    const validViolins = violins.filter(v => {
      if (!v || !v.category) return false;
      if (!v.profile || !Array.isArray(v.profile)) return false;
      // Permitir perfiles con al menos 1 punto válido
      const validProfile = v.profile.filter(p => p != null && p.y != null && !isNaN(p.y) && p.w != null && !isNaN(p.w));
      return validProfile.length > 0;
    });
    
    if (validViolins.length === 0) {
      // Mensaje más informativo visible en el DOM
      const debugInfo = violins.length > 0 
        ? `Se encontraron ${violins.length} violines pero ninguno tiene datos válidos`
        : 'No se encontraron violines en los datos';
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error en Violin Plot:</strong><br/>' +
        '<small>' + debugInfo + '</small><br/>' +
        '<small>Verifica que los datos tengan la estructura correcta: {category: string, profile: [{y: number, w: number}]}</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Violin plot: No hay datos válidos', { violins, spec });
      return;
    }
    
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
      .style('overflow', 'visible');
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const categories = validViolins.map(v => String(v.category || 'Unknown'));
    const yAll = validViolins.flatMap(v => v.profile.map(p => p.y)).filter(y => y != null && !isNaN(y));
    
    if (yAll.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay valores válidos para mostrar</div>';
      return;
    }
    
    const yExtent = d3.extent(yAll);
    if (yExtent[0] === yExtent[1]) {
      yExtent[0] = yExtent[0] - 1;
      yExtent[1] = yExtent[1] + 1;
    }
    
    const x = d3.scaleBand().domain(categories).range([0, chartWidth]).padding(0.2);
    const y = d3.scaleLinear().domain(yExtent).nice().range([chartHeight, 0]);
    
    // Calcular el ancho máximo del violín
    const maxWidth = validViolins.reduce((max, v) => {
      if (!v.profile || v.profile.length === 0) return max;
      const maxW = d3.max(v.profile.map(p => (p && p.w != null) ? p.w : 0));
      return Math.max(max, maxW || 0);
    }, 0);
    
    // Asegurar que maxWidth no sea 0
    const finalMaxWidth = maxWidth > 0 ? maxWidth : 1;
    const bandwidth = x.bandwidth() || 40;
    const maxViolinWidth = bandwidth / 2 - 5; // Dejar espacio para el borde
    
    const wScale = d3.scaleLinear()
      .domain([0, finalMaxWidth])
      .range([0, maxViolinWidth]);
    
    const color = d3.scaleOrdinal(d3.schemeSet2).domain(categories);

    // Contador de violines renderizados
    let renderedViolins = 0;
    const violinErrors = [];
    
    // Renderizar violines
    validViolins.forEach((v, idx) => {
      const category = String(v.category || 'Unknown');
      const cx = x(category);
      if (cx == null || isNaN(cx)) {
        violinErrors.push(`Categoría "${category}": No se pudo obtener posición X`);
        return;
      }
      const centerX = cx + x.bandwidth() / 2;
      
      // Filtrar y validar perfil
      const profile = v.profile.filter(p => {
        if (!p || p.y == null || isNaN(p.y)) return false;
        // Si w no está definido, usar un valor por defecto pequeño
        if (p.w == null || isNaN(p.w)) {
          p.w = 0.01;
        }
        return true;
      });
      
      if (profile.length === 0) {
        violinErrors.push(`Categoría "${category}": Perfil vacío después del filtrado`);
        return;
      }
      
      // Ordenar perfil por y (valor)
      profile.sort((a, b) => a.y - b.y);
      
      // Verificar que el perfil tenga datos válidos
      if (profile.length === 1) {
        // Si hay solo 1 punto, dibujar un círculo pequeño
        const yVal = profile[0].y;
        g.append('circle')
          .attr('cx', centerX)
          .attr('cy', y(yVal))
          .attr('r', 3)
          .attr('fill', color(category))
          .attr('opacity', 0.7);
        return;
      }
      
      // Crear área completa del violín (simétrica)
      // Asegurar que w no sea null o undefined y que sea positivo
      const safeProfile = profile.map(p => ({
        y: p.y,
        w: Math.max((p.w != null && !isNaN(p.w) && p.w > 0) ? p.w : 0.01, 0.01)  // Valor mínimo para w
      }));
      
      // Verificar que el perfil tenga valores válidos
      if (safeProfile.length < 2) {
        // Dibujar línea vertical simple
        const yMin = d3.min(safeProfile.map(p => p.y));
        const yMax = d3.max(safeProfile.map(p => p.y));
        g.append('line')
          .attr('x1', centerX)
          .attr('x2', centerX)
          .attr('y1', y(yMin))
          .attr('y2', y(yMax))
          .attr('stroke', color(category))
          .attr('stroke-width', 2)
          .attr('opacity', 0.7);
        return;
      }
      
      // Crear área simétrica usando d3.area
      const area = d3.area()
        .x0(p => centerX - wScale(p.w))  // Lado izquierdo
        .x1(p => centerX + wScale(p.w))  // Lado derecho
        .y(p => y(p.y))
        .curve(d3.curveCatmullRom.alpha(0.5))
        .defined(d => d != null && d.y != null && !isNaN(d.y) && d.w != null && !isNaN(d.w) && d.w > 0);
      
      // Generar el path y verificar que sea válido
      try {
        const pathData = area(safeProfile);
        if (!pathData || pathData === 'M0,0' || pathData.length < 10) {
          console.warn('Violin plot: Path inválido para categoría', category, 'pathData:', pathData?.substring(0, 50));
          // Intentar dibujar una línea vertical simple como fallback
          const yMin = d3.min(safeProfile.map(p => p.y));
          const yMax = d3.max(safeProfile.map(p => p.y));
          g.append('line')
            .attr('x1', centerX)
            .attr('x2', centerX)
            .attr('y1', y(yMin))
            .attr('y2', y(yMax))
            .attr('stroke', color(category))
            .attr('stroke-width', 3)
            .attr('opacity', 0.7);
          return;
        }
        
        // Dibujar violín completo (área cerrada simétrica)
        g.append('path')
          .attr('d', pathData)
          .attr('fill', color(category))
          .attr('opacity', 0.7)
          .attr('stroke', '#333')
          .attr('stroke-width', 1)
          .attr('stroke-linejoin', 'round')
          .attr('stroke-linecap', 'round');
        
        renderedViolins++;
      } catch (e) {
        violinErrors.push(`Categoría "${category}": Error al generar path (${e.message})`);
        // Fallback: dibujar una línea vertical simple
        const yMin = d3.min(safeProfile.map(p => p.y));
        const yMax = d3.max(safeProfile.map(p => p.y));
        g.append('line')
          .attr('x1', centerX)
          .attr('x2', centerX)
          .attr('y1', y(yMin))
          .attr('y2', y(yMax))
          .attr('stroke', color(category))
          .attr('stroke-width', 3)
          .attr('opacity', 0.7);
        renderedViolins++; // Contar como renderizado (aunque sea solo una línea)
        return;
      }
      
      // Dibujar línea central (mediana) para referencia visual
      const medianY = d3.median(safeProfile.map(p => p.y));
      if (medianY != null && !isNaN(medianY)) {
        const maxW = d3.max(safeProfile.map(p => p.w));
        if (maxW != null && maxW > 0) {
          g.append('line')
            .attr('x1', centerX - wScale(maxW))
            .attr('x2', centerX + wScale(maxW))
            .attr('y1', y(medianY))
            .attr('y2', y(medianY))
            .attr('stroke', '#000')
            .attr('stroke-width', 1.5)
            .attr('opacity', 0.8);
        }
      }
    });
    
    // Si no se renderizó ningún violín, mostrar error detallado
    if (renderedViolins === 0 && validViolins.length > 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error en Violin Plot: No se pudo renderizar ningún violín</strong><br/>' +
        '<small>Categorías encontradas: ' + categories.join(', ') + '</small><br/>' +
        (violinErrors.length > 0 ? '<small>Errores: ' + violinErrors.join('; ') + '</small>' : '') +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Violin plot: No se renderizó ningún violín', { validViolins, violinErrors });
      return;
    }

    // Renderizar ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      xAxis.selectAll('text')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('fill', '#000000');
      
      xAxis.selectAll('line')
        .style('stroke', '#000000')
        .style('stroke-width', '1px');
      
      xAxis.selectAll('path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(6));
      
      yAxis.selectAll('text')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('fill', '#000000');
      
      yAxis.selectAll('line')
        .style('stroke', '#000000')
        .style('stroke-width', '1px');
      
      yAxis.selectAll('path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }

  /**
   * RadViz simple
   */
  function renderRadVizD3(container, spec, d3, divId) {
    // Limpiar contenedor
    container.innerHTML = '';
    
    const points = spec.data || [];
    const features = spec.features || [];
    
    // Validar datos con mensajes más informativos
    if (!points || points.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos para mostrar (points vacío)</div>';
      console.warn('RadViz: No hay puntos', { spec });
      return;
    }
    
    if (!features || features.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay features para mostrar</div>';
      console.warn('RadViz: No hay features', { spec });
      return;
    }
    
    // Validar que los puntos tengan coordenadas válidas
    const validPoints = points.filter(p => {
      if (!p) return false;
      if (p.x == null || isNaN(p.x)) return false;
      if (p.y == null || isNaN(p.y)) return false;
      return true;
    });
    
    if (validPoints.length === 0) {
      const debugInfo = points.length > 0 
        ? `Se encontraron ${points.length} puntos pero ninguno tiene coordenadas válidas`
        : 'No se encontraron puntos en los datos';
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error en RadViz:</strong><br/>' +
        '<small>' + debugInfo + '</small><br/>' +
        '<small>Features: ' + (features.length > 0 ? features.join(', ') : 'ninguna') + '</small><br/>' +
        '<small>Verifica que los datos tengan la estructura correcta: {x: number, y: number, category: string}</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('RadViz: No hay puntos válidos', { points: points.slice(0, 3), spec });
      return;
    }
    
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    const defaultMargin = { top: 60, right: 60, bottom: 60, left: 60 };
    const margin = calculateAxisMargins(spec, defaultMargin);
    
    // Calcular dimensiones del gráfico
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar dimensiones mínimas
    const minChartWidth = 300;
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    }
    
    const minChartHeight = 300;
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }

    const svg = d3.select(container).append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');
    
    // Calcular centro del gráfico
    const centerX = margin.left + chartWidth / 2;
    const centerY = margin.top + chartHeight / 2;
    const radius = Math.min(chartWidth, chartHeight) / 2 - 40;
    
    const g = svg.append('g')
      .attr('transform', `translate(${centerX},${centerY})`);

    // Círculo de referencia
    g.append('circle')
      .attr('r', radius)
      .attr('fill', 'none')
      .attr('stroke', '#aaa')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '2,2');

    // Anchors (features)
    const anchorPos = features.map((f, i) => {
      const ang = 2 * Math.PI * i / Math.max(1, features.length) - Math.PI / 2; // Empezar desde arriba
      return { 
        x: radius * Math.cos(ang), 
        y: radius * Math.sin(ang), 
        name: String(f),
        angle: ang
      };
    });
    
    // Dibujar líneas desde el centro hasta los anchors
    anchorPos.forEach(anchor => {
      g.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', anchor.x)
        .attr('y2', anchor.y)
        .attr('stroke', '#ddd')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '1,1');
    });
    
    // Dibujar círculos en los anchors
    g.selectAll('.anchor')
      .data(anchorPos)
      .enter()
      .append('circle')
      .attr('class', 'anchor')
      .attr('r', 4)
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('fill', '#555')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);
    
    // Etiquetas de los anchors
    g.selectAll('.alabel')
      .data(anchorPos)
      .enter()
      .append('text')
      .attr('class', 'alabel')
      .attr('x', d => d.x * 1.15)
      .attr('y', d => d.y * 1.15)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '11px')
      .style('fill', '#333')
      .style('font-weight', 'bold')
      .text(d => d.name);

    // Escala para los puntos (normalizados en rango dinámico)
    const xExtent = d3.extent(validPoints, d => d.x);
    const yExtent = d3.extent(validPoints, d => d.y);
    
    // Calcular el rango máximo para normalizar
    const maxExtent = Math.max(
      Math.abs(xExtent[0] || 0),
      Math.abs(xExtent[1] || 0),
      Math.abs(yExtent[0] || 0),
      Math.abs(yExtent[1] || 0)
    ) || 1;
    
    // Escalar para que los puntos estén dentro del círculo
    const toX = d3.scaleLinear()
      .domain([-maxExtent, maxExtent])
      .range([-radius * 0.85, radius * 0.85]);
    
    const toY = d3.scaleLinear()
      .domain([-maxExtent, maxExtent])
      .range([-radius * 0.85, radius * 0.85]);
    
    // Obtener categorías únicas
    const categories = [...new Set(validPoints.map(p => p.category).filter(c => c != null && c !== ''))];
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(categories.length > 0 ? categories : ['default']);

    // Dibujar puntos
    g.selectAll('.rvpt')
      .data(validPoints)
      .enter()
      .append('circle')
      .attr('class', 'rvpt')
      .attr('cx', d => toX(d.x))
      .attr('cy', d => toY(d.y))
      .attr('r', 3)
      .attr('fill', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('opacity', 0.6)
      .attr('stroke', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event, d) {
        d3.select(this)
          .attr('r', 5)
          .attr('opacity', 1);
      })
      .on('mouseleave', function() {
        d3.select(this)
          .attr('r', 3)
          .attr('opacity', 0.6);
      });
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
    const groupedData = spec.data || [];
    
    // Validar datos
    if (!groups || groups.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay grupos para mostrar</div>';
      return;
    }
    
    if (!series || series.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay series para mostrar</div>';
      return;
    }
    
    if (!groupedData || groupedData.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos para mostrar</div>';
      return;
    }
    
    const x0 = d3.scaleBand().domain(groups).range([0, chartWidth]).padding(0.2);
    const x1 = d3.scaleBand().domain(series).range([0, x0.bandwidth()]).padding(0.1);
    
    // Calcular el valor máximo de los datos
    const maxValue = d3.max(groupedData, d => d.value != null && !isNaN(d.value) ? d.value : 0) || 1;
    const y2 = d3.scaleLinear().domain([0, maxValue]).nice().range([chartHeight, 0]);
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

    // Estado de selección persistente
    // Mantener un conjunto de índices de puntos seleccionados
    let selectedIndices = new Set();
    let isBrushing = false;
    
    // Función para obtener el color base de un punto
    const getBaseColor = (d) => {
      if (d.color) return d.color;
      if (spec.colorMap && d.category) {
        return spec.colorMap[d.category] || spec.color || '#4a90e2';
      }
      return spec.color || '#4a90e2';
    };
    
    // Función para actualizar la visualización de puntos según su estado de selección
    const updatePointVisualization = (dotsSelection, selectedSet, isHighlighting = false) => {
      dotsSelection.each(function(d, i) {
        const dot = d3.select(this);
        const isSelected = selectedSet.has(i);
        const baseRadius = getRadius(d);
        const baseColor = getBaseColor(d);
        
        if (isSelected) {
          // Punto seleccionado: más grande, opacidad completa, borde destacado
          dot
            .attr('r', baseRadius * 1.5)
            .attr('fill', baseColor)
            .attr('stroke', '#ff6b35')
            .attr('stroke-width', 2)
            .attr('opacity', 1);
        } else if (isHighlighting) {
          // Durante el brush: puntos no seleccionados más tenues
          dot
            .attr('r', baseRadius)
            .attr('fill', baseColor)
            .attr('stroke', 'none')
            .attr('stroke-width', 0)
            .attr('opacity', 0.15);
        } else {
          // Estado normal: puntos no seleccionados
          dot
            .attr('r', baseRadius)
            .attr('fill', baseColor)
            .attr('stroke', 'none')
            .attr('stroke-width', 0)
            .attr('opacity', 0.6);
        }
      });
    };
    
    // Función para enviar evento de selección
    const sendSelectionEvent = (indices) => {
      const selected = data.filter((d, i) => indices.has(i));
      const selectedItems = selected.map(d => d._original_row || d);
      
      // Obtener letra del scatter plot
      let scatterLetter = spec.__scatter_letter__ || null;
      if (!scatterLetter && container) {
        const letterAttr = container.getAttribute('data-letter');
        if (letterAttr) {
          scatterLetter = letterAttr;
        } else {
          const idMatch = container.id && container.id.match(/-cell-([A-Z])-/);
          if (idMatch) {
            scatterLetter = idMatch[1];
          }
        }
      }
      
      // Enviar evento de selección
      sendEvent(divId, 'select', {
        type: 'select',
        items: selectedItems,
        count: selectedItems.length,
        indices: Array.from(indices),
        __scatter_letter__: scatterLetter
      });
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
      .attr('fill', d => getBaseColor(d))
      .attr('opacity', 0.6)
      .attr('stroke', 'none')
      .attr('stroke-width', 0)
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (!spec.interactive || isBrushing) return;
        
        event.stopPropagation();
          const index = data.indexOf(d);
        const ctrlKey = event.ctrlKey || event.metaKey; // Cmd en Mac, Ctrl en Windows/Linux
        
        if (ctrlKey) {
          // Modo multi-selección: agregar o quitar de la selección
          if (selectedIndices.has(index)) {
            selectedIndices.delete(index);
          } else {
            selectedIndices.add(index);
          }
        } else {
          // Modo selección única: seleccionar solo este punto
          selectedIndices.clear();
          selectedIndices.add(index);
        }
        
        // Actualizar visualización
        updatePointVisualization(g.selectAll('.dot'), selectedIndices, false);
        
        // Enviar evento de selección
        sendSelectionEvent(selectedIndices);
      })
      .on('mouseenter', function(event, d) {
        if (!spec.interactive || isBrushing) return;
        const dot = d3.select(this);
        const index = data.indexOf(d);
        const isSelected = selectedIndices.has(index);
        
        if (!isSelected) {
          dot
            .transition()
            .duration(150)
            .attr('r', d => getRadius(d) * 1.3)
            .attr('opacity', 0.9);
        }
      })
      .on('mouseleave', function(event, d) {
        if (!spec.interactive || isBrushing) return;
        const dot = d3.select(this);
        const index = data.indexOf(d);
        const isSelected = selectedIndices.has(index);
        
        if (!isSelected) {
          dot
            .transition()
            .duration(150)
            .attr('r', d => getRadius(d))
            .attr('opacity', 0.6);
        }
      });
    
    // BRUSH para selección de área (renderizar DESPUÉS de los puntos para estar visualmente encima)
    if (spec.interactive) {
      // Crear grupo de brush que estará en la parte superior
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer');
      
      const brush = d3.brush()
        .extent([[0, 0], [chartWidth, chartHeight]])
        .on('start', function(event) {
          isBrushing = true;
          // Durante el brush, desactivar eventos de puntos temporalmente
          g.selectAll('.dot')
            .style('pointer-events', 'none');
        })
        .on('brush', function(event) {
          if (!event.selection) {
            // Si no hay selección, mostrar todos los puntos normalmente (excepto los seleccionados)
            updatePointVisualization(g.selectAll('.dot'), selectedIndices, false);
            return;
          }
          
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Identificar puntos dentro del área de brush
          const brushedIndices = new Set();
          data.forEach((d, i) => {
              const px = x(d.x);
              const py = y(d.y);
            if (px >= Math.min(x0, x1) && px <= Math.max(x0, x1) && 
                py >= Math.min(y0, y1) && py <= Math.max(y0, y1)) {
              brushedIndices.add(i);
            }
          });
          
          // Combinar selección actual con brush (union)
          // Durante el brush, mostrar visualmente qué puntos están dentro
          g.selectAll('.dot').each(function(d, i) {
            const dot = d3.select(this);
            const isInBrush = brushedIndices.has(i);
            const isSelected = selectedIndices.has(i);
            const baseRadius = getRadius(d);
            const baseColor = getBaseColor(d);
            
            if (isInBrush) {
              // Puntos dentro del brush: resaltar
              dot
                .attr('r', baseRadius * 1.4)
                .attr('fill', baseColor)
                .attr('stroke', '#4a90e2')
                .attr('stroke-width', 2)
                .attr('opacity', 1);
            } else if (isSelected) {
              // Puntos previamente seleccionados (pero fuera del brush): mantener selección
              dot
                .attr('r', baseRadius * 1.5)
                .attr('fill', baseColor)
                .attr('stroke', '#ff6b35')
                .attr('stroke-width', 2)
                .attr('opacity', 0.8);
            } else {
              // Puntos fuera del brush y no seleccionados: atenuar
              dot
                .attr('r', baseRadius)
                .attr('fill', baseColor)
                .attr('stroke', 'none')
                .attr('stroke-width', 0)
                .attr('opacity', 0.15);
            }
            });
        })
        .on('end', function(event) {
          isBrushing = false;
          
          // Restaurar eventos de puntos inmediatamente para permitir nuevos brushes y clicks
            g.selectAll('.dot')
            .style('pointer-events', 'all');
          
          // CRÍTICO: Asegurar que el overlay del brush siga capturando eventos
          // Esto permite que el usuario pueda hacer nuevos brushes después de una selección
          brushGroup.selectAll('.overlay')
            .style('pointer-events', 'all')
            .style('cursor', 'crosshair');
          
          // Si no hay selección (usuario hizo click fuera o canceló), mantener la selección actual
          // NO limpiar el brush visual - el usuario puede hacer un nuevo brush inmediatamente
          if (!event.selection) {
            updatePointVisualization(g.selectAll('.dot'), selectedIndices, false);
            // El brush visual permanece, permitiendo nuevos brushes
            // El overlay seguirá capturando eventos para permitir nuevos brushes
            return;
          }
          
          // Obtener coordenadas de la selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Convertir coordenadas de píxeles a valores de datos
          const xInverted0 = x.invert(Math.min(x0, x1));
          const xInverted1 = x.invert(Math.max(x0, x1));
          const yInverted0 = y.invert(Math.max(y0, y1));  // y está invertido
          const yInverted1 = y.invert(Math.min(y0, y1));
          
          // Identificar índices de puntos dentro de la selección
          const brushedIndices = new Set();
          data.forEach((d, i) => {
            if (d.x >= Math.min(xInverted0, xInverted1) && 
                d.x <= Math.max(xInverted0, xInverted1) &&
                d.y >= Math.min(yInverted0, yInverted1) && 
                d.y <= Math.max(yInverted0, yInverted1)) {
              brushedIndices.add(i);
            }
          });
          
          // Verificar si se presionó Ctrl/Cmd para agregar a la selección existente
          const ctrlKey = event.sourceEvent && (event.sourceEvent.ctrlKey || event.sourceEvent.metaKey);
          
          if (ctrlKey) {
            // Modo agregar: unir la selección del brush con la selección actual
            brushedIndices.forEach(i => selectedIndices.add(i));
          } else {
            // Modo reemplazar: reemplazar la selección actual con la del brush
            selectedIndices = new Set(brushedIndices);
          }
          
          // Actualizar visualización con la nueva selección
          // Los puntos seleccionados se mostrarán con borde naranja
          updatePointVisualization(g.selectAll('.dot'), selectedIndices, false);
          
          // Enviar evento de selección
          sendSelectionEvent(selectedIndices);
          
          // CRÍTICO: NO limpiar el brush visual automáticamente
          // El brush debe permanecer visible Y funcional para permitir múltiples selecciones
          // El usuario puede hacer un nuevo brush en cualquier momento
          // El área de brush permanecerá visible con la selección actual, y el usuario puede hacer un nuevo brush sobre ella
          // El nuevo brush reemplazará o agregará a la selección actual según si tiene Ctrl/Cmd presionado
          
          // NO usar setTimeout para limpiar el brush - el brush debe permanecer visible y funcional
          // El usuario puede hacer un nuevo brush en cualquier momento simplemente arrastrando sobre el gráfico
        });
      
      // Aplicar brush al grupo (esto lo renderiza visualmente encima de los puntos)
      brushGroup.call(brush);
      
      // Aplicar estilos CSS directamente al SVG para el brush
      // Usar selector más general para asegurar que los estilos se apliquen
      const styleId = `brush-style-${divId}`;
      let styleElement = document.getElementById(styleId);
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = styleId;
        document.head.appendChild(styleElement);
      }
      
      // Actualizar contenido del estilo (puede cambiar si el divId cambia)
      styleElement.textContent = `
        .matrix-layout #${divId} .brush-layer .overlay,
        #${divId} .brush-layer .overlay {
          cursor: crosshair !important;
          pointer-events: all !important;
          fill: transparent !important;
        }
        .matrix-layout #${divId} .brush-layer .selection,
        #${divId} .brush-layer .selection {
          stroke: #2563eb !important;
          stroke-width: 2.5px !important;
          stroke-dasharray: 8,4 !important;
          fill: #3b82f6 !important;
          fill-opacity: 0.25 !important;
          pointer-events: none !important;
        }
        .matrix-layout #${divId} .brush-layer .handle,
        #${divId} .brush-layer .handle {
          fill: #2563eb !important;
          stroke: #1e40af !important;
          stroke-width: 2px !important;
          cursor: move !important;
          pointer-events: all !important;
        }
        .matrix-layout #${divId} .brush-layer .handle--n,
        .matrix-layout #${divId} .brush-layer .handle--s,
        .matrix-layout #${divId} .brush-layer .handle--e,
        .matrix-layout #${divId} .brush-layer .handle--w,
        .matrix-layout #${divId} .brush-layer .handle--nw,
        .matrix-layout #${divId} .brush-layer .handle--ne,
        .matrix-layout #${divId} .brush-layer .handle--sw,
        .matrix-layout #${divId} .brush-layer .handle--se,
        #${divId} .brush-layer .handle--n,
        #${divId} .brush-layer .handle--s,
        #${divId} .brush-layer .handle--e,
        #${divId} .brush-layer .handle--w,
        #${divId} .brush-layer .handle--nw,
        #${divId} .brush-layer .handle--ne,
        #${divId} .brush-layer .handle--sw,
        #${divId} .brush-layer .handle--se {
          fill: #2563eb !important;
          stroke: #1e40af !important;
          stroke-width: 2px !important;
        }
      `;
      
      // Aplicar estilos directamente después de que el brush se crea
      // Esto asegura que los estilos se apliquen incluso si el CSS no se carga correctamente
      setTimeout(function() {
        brushGroup.selectAll('.overlay')
          .style('cursor', 'crosshair')
          .style('pointer-events', 'all')
          .style('fill', 'transparent');
        
        brushGroup.selectAll('.selection')
          .attr('stroke', '#2563eb')
          .attr('stroke-width', '2.5px')
          .attr('stroke-dasharray', '8,4')
          .attr('fill', '#3b82f6')
          .attr('fill-opacity', 0.25)
          .style('pointer-events', 'none');
        
        brushGroup.selectAll('.handle')
          .attr('fill', '#2563eb')
          .attr('stroke', '#1e40af')
          .attr('stroke-width', '2px')
          .style('cursor', 'move')
          .style('pointer-events', 'all');
      }, 100);
      
      // Aplicar estilos después de cada evento del brush para mantenerlos actualizados
      // Usar un observer o aplicar estilos periódicamente
      const styleUpdateInterval = setInterval(function() {
        // Solo aplicar estilos si el brush existe
        if (brushGroup.selectAll('.overlay').size() > 0 || brushGroup.selectAll('.selection').size() > 0) {
          brushGroup.selectAll('.overlay')
            .style('cursor', 'crosshair')
            .style('pointer-events', 'all');
          
          brushGroup.selectAll('.selection')
            .attr('stroke', '#2563eb')
            .attr('stroke-width', '2.5px')
            .attr('stroke-dasharray', '8,4')
            .attr('fill', '#3b82f6')
            .attr('fill-opacity', 0.25)
            .style('pointer-events', 'none');
          
          brushGroup.selectAll('.handle')
            .attr('fill', '#2563eb')
            .attr('stroke', '#1e40af')
            .attr('stroke-width', '2px')
            .style('cursor', 'move')
            .style('pointer-events', 'all');
        }
      }, 300);
      
      // Función para limpiar selección y brush
      const clearSelection = function() {
        selectedIndices.clear();
        updatePointVisualization(g.selectAll('.dot'), selectedIndices, false);
        brushGroup.call(brush.move, null);
        sendSelectionEvent(selectedIndices);
      };
      
      // Doble click en el overlay para limpiar selección
      // Aplicar el evento después de que el overlay se cree
      setTimeout(function() {
        brushGroup.selectAll('.overlay')
          .on('dblclick', function() {
            clearSelection();
          });
      }, 150);
      
      // Agregar listener para tecla Escape para limpiar selección
      if (!window._bestlib_escape_handlers) {
        window._bestlib_escape_handlers = new Map();
        
        // Agregar listener global al documento (solo una vez)
        document.addEventListener('keydown', function(event) {
          if (event.key === 'Escape' || event.key === 'Esc') {
            // Ejecutar todos los handlers activos
            window._bestlib_escape_handlers.forEach((handler, id) => {
              handler(event);
            });
          }
        });
      }
      
      // Crear handler específico para este gráfico
      const escapeHandler = function(event) {
        // Verificar si el contenedor está visible
        if (container && container.offsetParent !== null) {
          clearSelection();
          event.stopPropagation();
        }
      };
      
      // Agregar handler al mapa global
      window._bestlib_escape_handlers.set(divId, escapeHandler);
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