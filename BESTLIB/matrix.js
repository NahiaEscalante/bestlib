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
    
    // Configuración dinámica de gap (definir ANTES de usarlo)
    const gap = mapping.__gap__ !== undefined ? mapping.__gap__ : 12;
    
    // Configuración dinámica de cell padding (definir ANTES de usarlo)
    const cellPadding = mapping.__cell_padding__ !== undefined ? mapping.__cell_padding__ : 15;
    
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
      // 🔒 MEJORA ESTÉTICA: Ajustar altura de filas dinámicamente según tamaño del dashboard
      // Para dashboards grandes (3x3, 4x4), reducir altura mínima para que se vean mejor
      let minRowHeight = 350; // Por defecto
      
      // Calcular número total de celdas
      const totalCells = R * C;
      
      // Si hay max_width, ajustar según el número de filas
      if (mapping.__max_width__) {
        const maxWidth = parseInt(mapping.__max_width__);
        // Para dashboards grandes (9+ celdas), calcular altura basada en max_width
        if (totalCells >= 9) {
          // En dashboards grandes, la altura debe ser proporcional al ancho
          // Usar aspect ratio aproximado de 1.2:1 (ancho:alto) para dashboards grandes
          const estimatedCellWidth = (maxWidth / C) - (gap * (C - 1) / C) - (cellPadding * 2);
          const estimatedCellHeight = estimatedCellWidth / 1.2; // Aspect ratio aproximado
          minRowHeight = Math.max(200, Math.min(350, estimatedCellHeight)); // Entre 200 y 350px
        } else if (totalCells >= 6) {
          // Dashboards medianos (2x3, 3x2): altura intermedia
          minRowHeight = 280;
        }
      } else if (totalCells >= 9) {
        // Dashboards grandes sin max_width explícito: reducir altura mínima
        minRowHeight = 280;
      }
      
      // Aumentar altura de filas para evitar recorte - altura mínima para gráficos completos
      // Considerando: padding (30px) + gráfico (320px) + espacio para ejes (20px extra)
      container.style.gridTemplateRows = `repeat(${R}, minmax(${minRowHeight}px, auto))`;
    }
    
    // Aplicar gap al contenedor
    container.style.gap = `${gap}px`;
    
    // Configuración dinámica de max-width
    if (mapping.__max_width__ !== undefined) {
      container.style.maxWidth = `${mapping.__max_width__}px`;
    }

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
        value.type === 'heatmap' ||
        value.type === 'line' ||
        value.type === 'violin' ||
        value.type === 'radviz' ||
        value.type === 'star_coordinates' ||
        value.type === 'parallel_coordinates' ||
        value.type === 'line_plot' ||
        value.type === 'horizontal_bar' ||
        value.type === 'hexbin' ||
        value.type === 'errorbars' ||
        value.type === 'fill_between' ||
        value.type === 'step_plot' ||
        value.type === 'kde' ||
        value.type === 'distplot' ||
        value.type === 'rug' ||
        value.type === 'qqplot' ||
        value.type === 'ecdf' ||
        value.type === 'ridgeline' ||
        value.type === 'ribbon' ||
        value.type === 'hist2d' ||
        value.type === 'polar' ||
        value.type === 'funnel'
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
        
        // Agregar clases CSS para indicadores de enlace visual
        if (spec && typeof spec === 'object') {
          // Si es un gráfico principal (genera selecciones), agregar clase linked-primary
          // Verificar múltiples formas de identificar gráficos principales
          const isPrimary = (spec.__scatter_letter__ && spec.__scatter_letter__ === letter) ||
                           (spec.__is_primary_view__ === true) ||
                           (spec.__view_letter__ && spec.__view_letter__ === letter && spec.interactive === true);
          
          if (isPrimary) {
            cell.classList.add('linked-primary');
            cell.setAttribute('title', `Gráfico principal '${letter}' (genera selecciones)`);
            cell.setAttribute('data-is-primary', 'true');
            cell.setAttribute('data-primary-letter', letter);
            // Agregar etiqueta visual con la letra del gráfico
            const label = document.createElement('div');
            label.className = 'link-primary-label';
            label.textContent = `${letter} (LINKED)`;
            label.style.cssText = 'position: absolute; top: 6px; right: 6px; background: #2563eb; color: white; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; z-index: 100; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.5); text-transform: uppercase; white-space: nowrap; pointer-events: none;';
            cell.appendChild(label);
          }
          
          // Si está enlazado a otro gráfico (linked_to), agregar clase linked-secondary
          if (spec.__linked_to__) {
            cell.classList.add('linked-secondary');
            const linkedTo = spec.__linked_to__;
            cell.setAttribute('title', `Gráfico '${letter}' enlazado a '${linkedTo}'`);
            // Agregar atributo data para referencia
            cell.setAttribute('data-linked-to', linkedTo);
            cell.setAttribute('data-linked-from', letter);
            // Agregar etiqueta visual con ambas letras
            const label = document.createElement('div');
            label.className = 'link-secondary-label';
            label.textContent = `${letter} ← ${linkedTo}`;
            label.style.cssText = 'position: absolute; top: 6px; left: 6px; background: #dc2626; color: white; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; z-index: 100; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5); text-transform: uppercase; white-space: nowrap; pointer-events: none; animation: pulse-link 2s ease-in-out infinite;';
            cell.appendChild(label);
          }
        }
        
        // Aplicar padding personalizado si existe (usar la variable definida arriba)
        cell.style.padding = `${cellPadding}px`;

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
              
              // 🔒 MEJORA ESTÉTICA: Esperar a que el contenedor tenga dimensiones antes de renderizar
              // Usar requestAnimationFrame para asegurar que el layout esté calculado
              requestAnimationFrame(() => {
                // Verificar que el contenedor tenga dimensiones
                if (cell.offsetWidth === 0 || cell.offsetHeight === 0) {
                  // Si aún no tiene dimensiones, esperar un frame más
                  requestAnimationFrame(() => {
              renderChartD3(cell, spec, d3, divIdFromMapping);
                  });
                } else {
                  renderChartD3(cell, spec, d3, divIdFromMapping);
                }
              });
              
              // CRÍTICO: NO usar ResizeObserver para gráficos interactivos con brush
              // Esto previene que el brush desaparezca al re-renderizar
              const isInteractive = spec.interactive !== false; // Por defecto true para scatter
              const isScatterPlot = spec.type === 'scatter';
              
              if (!isInteractive || !isScatterPlot) {
                // Solo agregar ResizeObserver para gráficos NO interactivos
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
              } else {
                console.log('[BESTLIB] ResizeObserver desactivado para scatter plot interactivo (prevenir pérdida de brush)');
              }
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
    
    // 🔒 MEJORA ESTÉTICA: Dibujar líneas conectivas entre gráficos enlazados
    // Esperar a que todas las celdas estén renderizadas antes de dibujar líneas
    setTimeout(() => {
      drawLinkConnectors(container, divId, mapping);
    }, 150);
  }
  
  /**
   * Dibuja líneas conectivas entre gráficos enlazados para hacer claro el enlace
   * MEJORADO: Muestra claramente qué gráfico está enlazado con cuál
   */
  function drawLinkConnectors(container, divId, mapping) {
    // Limpiar líneas conectivas anteriores si existen
    const existingOverlay = container.querySelector('.link-connectors-overlay');
    if (existingOverlay) {
      existingOverlay.remove();
    }
    
    // Obtener todas las celdas enlazadas
    const primaryCells = container.querySelectorAll('.matrix-cell[data-is-primary="true"]');
    const secondaryCells = container.querySelectorAll('.matrix-cell[data-linked-to]');
    
    if (primaryCells.length === 0 || secondaryCells.length === 0) {
      return; // No hay enlaces para dibujar
    }
    
    // Colores diferentes para cada par de enlaces (para distinguir múltiples enlaces)
    const linkColors = [
      '#2563eb', // Azul
      '#dc2626', // Rojo
      '#16a34a', // Verde
      '#ca8a04', // Amarillo
      '#9333ea', // Púrpura
      '#ea580c', // Naranja
    ];
    
    // Crear SVG overlay para líneas conectivas
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '1';
    svg.style.overflow = 'visible';
    svg.setAttribute('class', 'link-connectors-overlay');
    
    // Crear definiciones de flechas para cada color
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // Para cada celda secundaria, dibujar línea a su celda principal
    secondaryCells.forEach((secondaryCell, index) => {
      const linkedToLetter = secondaryCell.getAttribute('data-linked-to');
      const linkedFromLetter = secondaryCell.getAttribute('data-linked-from') || secondaryCell.getAttribute('data-letter');
      const primaryCell = Array.from(primaryCells).find(cell => 
        cell.getAttribute('data-primary-letter') === linkedToLetter
      );
      
      if (primaryCell) {
        // Usar color diferente para cada enlace (cíclico)
        const linkColor = linkColors[index % linkColors.length];
        const markerId = `arrowhead-${index}`;
        
        // Crear marcador de flecha para este color
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', markerId);
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3, 0 6');
        polygon.setAttribute('fill', linkColor);
        marker.appendChild(polygon);
        defs.appendChild(marker);
        
        // Obtener posiciones de ambas celdas
        const primaryRect = primaryCell.getBoundingClientRect();
        const secondaryRect = secondaryCell.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        
        // Calcular posiciones relativas al contenedor (considerando padding)
        const primaryX = primaryRect.left + primaryRect.width / 2 - containerRect.left;
        const primaryY = primaryRect.top + primaryRect.height / 2 - containerRect.top;
        const secondaryX = secondaryRect.left + secondaryRect.width / 2 - containerRect.left;
        const secondaryY = secondaryRect.top + secondaryRect.height / 2 - containerRect.top;
        
        // Crear línea conectora
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', primaryX);
        line.setAttribute('y1', primaryY);
        line.setAttribute('x2', secondaryX);
        line.setAttribute('y2', secondaryY);
        line.setAttribute('class', 'link-connector');
        line.setAttribute('stroke', linkColor);
        line.setAttribute('stroke-width', '4');
        line.setAttribute('stroke-dasharray', '10,5');
        line.setAttribute('opacity', '0.8');
        line.setAttribute('marker-end', `url(#${markerId})`);
        line.setAttribute('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))');
        
        svg.appendChild(line);
        
        // Agregar etiqueta CLARA en el punto medio mostrando AMBAS letras
        const midX = (primaryX + secondaryX) / 2;
        const midY = (primaryY + secondaryY) / 2;
        
        // Calcular ángulo de la línea para rotar la etiqueta
        const angle = Math.atan2(secondaryY - primaryY, secondaryX - primaryX) * 180 / Math.PI;
        
        const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        
        // Etiqueta que muestra AMBAS letras: "A → X"
        const labelTextContent = `${linkedToLetter} → ${linkedFromLetter}`;
        labelText.setAttribute('x', midX);
        labelText.setAttribute('y', midY);
        labelText.setAttribute('text-anchor', 'middle');
        labelText.setAttribute('class', 'link-label');
        labelText.setAttribute('fill', linkColor);
        labelText.setAttribute('font-size', '12px');
        labelText.setAttribute('font-weight', 'bold');
        labelText.setAttribute('opacity', '1');
        labelText.textContent = labelTextContent;
        
        // Calcular tamaño del texto para el fondo
        const textLength = labelTextContent.length;
        const bgWidth = textLength * 8 + 12;
        const bgHeight = 18;
        
        labelBg.setAttribute('x', midX - bgWidth / 2);
        labelBg.setAttribute('y', midY - bgHeight / 2);
        labelBg.setAttribute('width', bgWidth);
        labelBg.setAttribute('height', bgHeight);
        labelBg.setAttribute('fill', 'white');
        labelBg.setAttribute('opacity', '0.98');
        labelBg.setAttribute('rx', '6');
        labelBg.setAttribute('stroke', linkColor);
        labelBg.setAttribute('stroke-width', '2');
        labelBg.setAttribute('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))');
        
        svg.insertBefore(labelBg, labelText);
        svg.appendChild(labelText);
      }
    });
    
    // Agregar defs al inicio del SVG
    if (defs.children.length > 0) {
      svg.insertBefore(defs, svg.firstChild);
    }
    
    // Agregar SVG al contenedor si hay líneas
    if (svg.children.length > 1) { // Más que solo defs
      container.appendChild(svg);
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
          // Solo re-renderizar si el cambio es significativo (más de 30px)
          // Aumentado de 10px a 30px para evitar re-renders innecesarios por cambios mínimos
          if (widthDiff > 30 || heightDiff > 30) {
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
   * Aplica estilos unificados a ejes D3
   * @param {object} axisSelection - Selección D3 del eje
   */
  function applyUnifiedAxisStyles(axisSelection) {
    axisSelection.selectAll('text')
      .style('font-size', '11px')
      .style('font-weight', '600')
      .style('fill', '#000000')
      .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
      .attr('class', 'bestlib-axis-text');
    
    axisSelection.selectAll('line, path')
      .style('stroke', '#000000')
      .style('stroke-width', '2px')
      .attr('class', 'bestlib-axis');
  }
  
  /**
   * Obtiene valores de estilo unificados
   * @returns {object} Objeto con valores de estilo estándar
   */
  function getUnifiedStyles() {
    return {
      primaryColor: '#4a90e2',
      primaryHover: '#357abd',
      selectionColor: '#ff6b35',
      textColor: '#000000',
      textSecondary: '#666666',
      lineWidth: 2,
      lineWidthThick: 2.5,
      lineWidthThin: 1.5,
      axisWidth: 2,
      pointRadius: 4,
      pointRadiusHover: 6,
      pointRadiusSelected: 6,
      pointStrokeWidth: 1.5,
      opacityDefault: 1,
      opacityHover: 0.85,
      opacitySelected: 1,
      opacityUnselected: 0.3,
      opacityFill: 0.3,
      labelFontSize: 13,
      labelFontWeight: 700,
      tickFontSize: 11,
      tickFontWeight: 600,
      transitionDuration: 300,
      transitionDurationSlow: 500
    };
  }
  
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
      
      const styles = getUnifiedStyles();
      const xLabelText = g.append('text')
        .attr('x', xLabelX)
        .attr('y', xLabelY)
        .attr('text-anchor', 'middle')
        .attr('class', 'bestlib-axis-label bestlib-axis-label-x')
        .style('font-size', `${spec.xLabelFontSize || styles.labelFontSize}px`)
        .style('font-weight', `${styles.labelFontWeight}`)
        .style('fill', styles.textColor)
        .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
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
      const styles = getUnifiedStyles();
      const yLabelText = svg.append('text')
        .attr('x', yLabelX)
        .attr('y', yLabelY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')  // Usar 'central' en lugar de 'middle' para mejor alineación
        .attr('class', 'bestlib-axis-label bestlib-axis-label-y')
        .style('font-size', `${spec.yLabelFontSize || styles.labelFontSize}px`)
        .style('font-weight', `${styles.labelFontWeight}`)
        .style('fill', styles.textColor)
        .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
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
   * Renderiza eje X con label de forma consistente
   * @param {object} g - Grupo D3 donde renderizar
   * @param {object} xScale - Escala D3 para eje X
   * @param {number} chartHeight - Altura del área del gráfico
   * @param {number} chartWidth - Ancho del área del gráfico
   * @param {object} margin - Márgenes {top, right, bottom, left}
   * @param {string} xLabel - Etiqueta del eje X (opcional)
   * @param {object} svg - SVG principal (para labels)
   */
  function renderXAxis(g, xScale, chartHeight, chartWidth, margin, xLabel, svg) {
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale));
    
    applyUnifiedAxisStyles(xAxis);
    
    // Renderizar label si se proporciona
    if (xLabel && svg) {
      const styles = getUnifiedStyles();
      // X: centro del gráfico (margin.left + chartWidth / 2)
      // Y: debajo del gráfico (margin.top + chartHeight + margin.bottom - 10)
      const xLabelX = margin.left + chartWidth / 2;
      const xLabelY = margin.top + chartHeight + margin.bottom - 10;
      
      svg.append('text')
        .attr('x', xLabelX)
        .attr('y', xLabelY)
        .attr('text-anchor', 'middle')
        .attr('class', 'bestlib-axis-label bestlib-axis-label-x')
        .style('font-size', `${styles.labelFontSize}px`)
        .style('font-weight', styles.labelFontWeight)
        .style('fill', styles.textColor)
        .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
        .text(xLabel);
    }
    
    return xAxis;
  }
  
  /**
   * Renderiza eje Y con label de forma consistente
   * @param {object} g - Grupo D3 donde renderizar
   * @param {object} yScale - Escala D3 para eje Y
   * @param {number} chartWidth - Ancho del área del gráfico (no usado, pero para consistencia)
   * @param {number} chartHeight - Altura del área del gráfico
   * @param {object} margin - Márgenes {top, right, bottom, left}
   * @param {string} yLabel - Etiqueta del eje Y (opcional)
   * @param {object} svg - SVG principal (para labels)
   */
  function renderYAxis(g, yScale, chartWidth, chartHeight, margin, yLabel, svg) {
    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale));
    
    applyUnifiedAxisStyles(yAxis);
    
    // Renderizar label si se proporciona
    if (yLabel && svg) {
      const styles = getUnifiedStyles();
      // X: centro del margen izquierdo (margin.left / 2)
      // Y: centro vertical del gráfico (margin.top + chartHeight / 2)
      const yLabelX = margin.left / 2;
      const yLabelY = margin.top + chartHeight / 2;
      
      const yLabelText = svg.append('text')
        .attr('x', yLabelX)
        .attr('y', yLabelY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('class', 'bestlib-axis-label bestlib-axis-label-y')
        .style('font-size', `${styles.labelFontSize}px`)
        .style('font-weight', styles.labelFontWeight)
        .style('fill', styles.textColor)
        .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
        .style('pointer-events', 'none')
        .text(yLabel);
      
      yLabelText.attr('transform', `rotate(-90 ${yLabelX} ${yLabelY})`);
    }
    
    return yAxis;
  }
  
  /**
   * Calcula márgenes dinámicamente según tamaño de etiquetas de ejes
   */
  function calculateAxisMargins(spec, defaultMargin, containerWidth, containerHeight) {
    const margin = { ...defaultMargin };
    
    // 🔒 OPTIMIZACIÓN: Detectar dashboards grandes y reducir márgenes automáticamente
    // Buscar el contenedor matrix-layout padre
    let isLargeDashboard = false;
    if (containerWidth && containerWidth < 400) {
      // Si el contenedor es pequeño, probablemente es un dashboard grande
      // Intentar encontrar el layout padre
      try {
        const layoutContainer = document.querySelector('.matrix-layout');
        if (layoutContainer) {
          const cellCount = layoutContainer.querySelectorAll('.matrix-cell').length;
          isLargeDashboard = cellCount >= 9;
        }
      } catch (e) {
        // Si falla, usar heurística basada en tamaño
        isLargeDashboard = containerWidth < 300;
      }
    }
    
    // 🔒 MEJORA ESTÉTICA: Ajustar márgenes según el tamaño del contenedor y tipo de dashboard
    // En dashboards grandes (contenedores pequeños), reducir márgenes para maximizar espacio
    const isSmallContainer = containerWidth && containerWidth < 350;
    const marginMultiplier = isLargeDashboard ? 0.7 : (isSmallContainer ? 1.0 : 1.0); // Reducir márgenes en dashboards grandes
    
    // Calcular espacio necesario para etiqueta X
    if (spec.xLabel) {
      const xLabelFontSize = spec.xLabelFontSize || 13;
      const xLabelRotation = spec.xLabelRotation || 0;
      // Si está rotada, necesita más espacio
      if (xLabelRotation !== 0) {
        const rotationRad = Math.abs(xLabelRotation) * Math.PI / 180;
        const labelHeight = xLabelFontSize * 1.2; // Aproximación de altura de texto
        const rotatedHeight = Math.abs(Math.sin(rotationRad) * (spec.xLabel.length * xLabelFontSize * 0.6)) + labelHeight;
        margin.bottom = Math.max(margin.bottom, (rotatedHeight + 25) * marginMultiplier);
      } else {
        margin.bottom = Math.max(margin.bottom, (xLabelFontSize + 30) * marginMultiplier);
      }
    }
    
    // 🔒 MEJORA ESTÉTICA: Asegurar espacio suficiente para etiquetas del eje X
    // Considerar el número de ticks y su longitud
    if (spec.xTicks && Array.isArray(spec.xTicks)) {
      const maxTickLength = Math.max(...spec.xTicks.map(t => String(t).length), 0);
      const tickFontSize = spec.xTickFontSize || 11;
      // Si hay muchos ticks o son largos, necesitar más espacio
      if (spec.xTicks.length > 5 || maxTickLength > 6) {
        // Rotación automática para etiquetas largas o muchas etiquetas
        const needsRotation = spec.xTicks.length > 8 || maxTickLength > 8;
        if (needsRotation && !spec.xLabelRotation) {
          // Marcar para rotación automática (45 grados)
          spec._autoRotateXTicks = true;
          const rotationRad = 45 * Math.PI / 180;
          const tickHeight = tickFontSize * 1.2;
          const rotatedHeight = Math.abs(Math.sin(rotationRad) * (maxTickLength * tickFontSize * 0.6)) + tickHeight;
          margin.bottom = Math.max(margin.bottom, (rotatedHeight + 30) * marginMultiplier);
        } else {
          margin.bottom = Math.max(margin.bottom, (tickFontSize + 35) * marginMultiplier);
        }
      } else {
        margin.bottom = Math.max(margin.bottom, (tickFontSize + 25) * marginMultiplier);
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
        // Necesitamos espacio para: eje Y (50px) + etiqueta Y rotada (textHeight/2) + padding (25px)
        // El margen izquierdo debe ser al menos: eje Y + mitad del texto rotado + padding
        const minLeftMargin = (50 + (textHeight / 2) + 25) * marginMultiplier; // Espacio para eje + texto + padding
        margin.left = Math.max(margin.left, minLeftMargin);
      } else {
        // Texto rotado en otro ángulo: calcular ancho proyectado
        const rotationRad = Math.abs(yLabelRotation) * Math.PI / 180;
        const labelWidth = spec.yLabel.length * yLabelFontSize * 0.6;
        const labelHeight = yLabelFontSize * 1.2;
        // Calcular el ancho proyectado considerando tanto el ancho como la altura
        const projectedWidth = Math.abs(Math.cos(rotationRad) * labelWidth) + Math.abs(Math.sin(rotationRad) * labelHeight);
        margin.left = Math.max(margin.left, (50 + (projectedWidth / 2) + 25) * marginMultiplier); // Eje Y + texto + padding
      }
    }
    
    // 🔒 MEJORA ESTÉTICA: Asegurar espacio suficiente para etiquetas del eje Y
    if (spec.yTicks && Array.isArray(spec.yTicks)) {
      const maxTickLength = Math.max(...spec.yTicks.map(t => String(t).length), 0);
      const tickFontSize = spec.yTickFontSize || 11;
      // Espacio para ticks del eje Y: ancho del tick más largo + padding
      const tickSpace = (maxTickLength * tickFontSize * 0.6 + 15) * marginMultiplier;
      margin.left = Math.max(margin.left, tickSpace);
    }
    
    // 🔒 MEJORA ESTÉTICA: Márgenes mínimos mejorados para dashboards grandes
    margin.top = Math.max(margin.top, 25 * marginMultiplier);
    margin.right = Math.max(margin.right, 20 * marginMultiplier);
    margin.bottom = Math.max(margin.bottom, 40 * marginMultiplier);
    margin.left = Math.max(margin.left, 55 * marginMultiplier);
    
    return margin;
  }
  
  /**
   * Calcula dimensiones del gráfico basándose en figsize o valores por defecto
   * Incluye validación para asegurar dimensiones válidas
   */
  function getChartDimensions(container, spec, defaultWidth, defaultHeight) {
    // Aspect ratio por defecto (width/height) para mantener proporciones consistentes
    const DEFAULT_ASPECT_RATIO = 1.3; // Ancho 30% más grande que alto
    
    // Validar que el contenedor exista
    if (!container) {
      console.warn('[BESTLIB] Contenedor no encontrado, usando dimensiones por defecto');
      return { width: defaultWidth, height: defaultHeight };
    }
    
    // Si hay figsize en el spec, validarlo y usarlo
    if (spec.figsize && Array.isArray(spec.figsize) && spec.figsize.length === 2) {
      let width = Math.max(parseInt(spec.figsize[0]) || defaultWidth, 100);
      let height = Math.max(parseInt(spec.figsize[1]) || defaultHeight, 100);
      if (isNaN(width) || isNaN(height) || !isFinite(width) || !isFinite(height)) {
        console.warn('[BESTLIB] Dimensiones inválidas en figsize, usando valores por defecto');
        width = defaultWidth;
        height = defaultHeight;
      }
      
      // Ajustar para mantener aspect ratio si es necesario
      const aspectRatio = spec.aspectRatio !== undefined ? parseFloat(spec.aspectRatio) : DEFAULT_ASPECT_RATIO;
      if (aspectRatio > 0) {
        // Ajustar altura para mantener aspect ratio
        const idealHeight = width / aspectRatio;
        if (Math.abs(idealHeight - height) / height > 0.2) {
          // Si la diferencia es mayor al 20%, ajustar
          height = idealHeight;
        }
      }
      
      return { width, height };
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
    
    // 🔒 CRÍTICO: Si el contenedor padre tiene max-width en CSS, RESPETARLO SIEMPRE
    // Esto previene expansión infinita al limitar desde el CSS
    let cssMaxWidth = null;
    if (parentContainer) {
      const computedStyle = window.getComputedStyle(parentContainer);
      const maxWidthStr = computedStyle.maxWidth;
      if (maxWidthStr && maxWidthStr !== 'none') {
        cssMaxWidth = parseInt(maxWidthStr);
        if (isNaN(cssMaxWidth) || !isFinite(cssMaxWidth) || cssMaxWidth <= 0) {
          cssMaxWidth = null;
        }
      }
    }
    
    // Si hay figsize global en el mapping, validarlo y usarlo
    if (mapping && mapping.__figsize__ && Array.isArray(mapping.__figsize__) && mapping.__figsize__.length === 2) {
      const width = Math.max(parseInt(mapping.__figsize__[0]) || defaultWidth, 100);
      const height = Math.max(parseInt(mapping.__figsize__[1]) || defaultHeight, 100);
      if (isNaN(width) || isNaN(height) || !isFinite(width) || !isFinite(height)) {
        console.warn('[BESTLIB] Dimensiones inválidas en figsize global, usando valores por defecto');
      } else {
        return { width, height };
      }
    }
    
    // 🔒 MEJORA ESTÉTICA: Usar TODO el espacio disponible del contenedor
    // Obtener dimensiones del contenedor de múltiples formas para máxima compatibilidad
    let containerWidth = 0;
    let containerHeight = 0;
    
    // Método 1: offsetWidth/offsetHeight (más confiable, incluye padding y border)
    containerWidth = container.offsetWidth || 0;
    containerHeight = container.offsetHeight || 0;
    
    // Método 2: getBoundingClientRect (más preciso si offsetWidth falla)
    if (containerWidth <= 0 || containerHeight <= 0) {
      const containerRect = container.getBoundingClientRect();
      if (containerRect.width > 0 && containerRect.height > 0) {
        containerWidth = containerRect.width;
        containerHeight = containerRect.height;
      }
    }
    
    // Método 3: clientWidth/clientHeight
    if (containerWidth <= 0 || containerHeight <= 0) {
      containerWidth = container.clientWidth || 0;
      containerHeight = container.clientHeight || 0;
    }
    
    // Método 4: computed style como último recurso
    if (containerWidth <= 0 || containerHeight <= 0) {
      const computedStyle = window.getComputedStyle(container);
      const styleWidth = parseFloat(computedStyle.width);
      const styleHeight = parseFloat(computedStyle.height);
      if (styleWidth > 0 && !isNaN(styleWidth)) containerWidth = styleWidth;
      if (styleHeight > 0 && !isNaN(styleHeight)) containerHeight = styleHeight;
    }
    
    // Si aún no tenemos dimensiones válidas, usar valores por defecto razonables
    let width = containerWidth > 0 ? containerWidth : defaultWidth;
    let height = containerHeight > 0 ? containerHeight : defaultHeight;
    
    // Validar dimensiones
    if (width <= 0 || !isFinite(width)) {
      width = defaultWidth;
    }
    if (height <= 0 || !isFinite(height)) {
      height = defaultHeight;
    }
    
    // 🔒 CRÍTICO: Asegurar dimensiones mínimas razonables
    // Pero NO reducir si el contenedor es más grande - usar TODO el espacio
    // Para dashboards grandes (9+ celdas), usar dimensiones mínimas más pequeñas
    const isLargeDashboard = parentContainer && parentContainer.querySelectorAll('.matrix-cell').length >= 9;
    const minWidth = isLargeDashboard ? 150 : 200;
    const minHeight = isLargeDashboard ? 120 : 150;
    width = Math.max(width, minWidth);
    height = Math.max(height, minHeight);
    
    // 🔒 MEJORA ESTÉTICA: NO ajustar aspect ratio - usar TODO el espacio del contenedor
    // El viewBox con preserveAspectRatio mantendrá las proporciones correctamente
    // pero el SVG ocupará 100% del contenedor, evitando gráficos pequeños en espacios grandes
    
    // 🔒 CRÍTICO: Si hay max-width CSS, usarlo como límite ABSOLUTO del contenedor
    // Esto debe aplicarse ANTES de cualquier otro cálculo
    // IMPORTANTE: Solo aplicar cuando hay max_width EXPLÍCITO (no afectar dashboards sin límite)
    let containerMaxWidth = cssMaxWidth;
    if (!containerMaxWidth && mapping && mapping.__max_width__) {
      containerMaxWidth = parseInt(mapping.__max_width__);
      if (isNaN(containerMaxWidth) || !isFinite(containerMaxWidth) || containerMaxWidth <= 0) {
        containerMaxWidth = null;
      }
    }
    
    if (containerMaxWidth) {
      // Calcular número de columnas del grid dinámicamente
      let numColumns = 3; // Valor por defecto
      let numRows = 3; // Valor por defecto
      
      // Intentar obtener el número de columnas y filas del grid desde computedStyle
      if (parentContainer) {
        const computedStyle = window.getComputedStyle(parentContainer);
        const gridCols = computedStyle.gridTemplateColumns;
        const gridRows = computedStyle.gridTemplateRows;
        if (gridCols && gridCols !== 'none') {
          // Contar el número de tracks en el grid (separados por espacios)
          const tracks = gridCols.trim().split(/\s+/);
          if (tracks.length > 0) {
            numColumns = tracks.length;
          }
        }
        if (gridRows && gridRows !== 'none') {
          const rowTracks = gridRows.trim().split(/\s+/);
          if (rowTracks.length > 0) {
            numRows = rowTracks.length;
          }
        }
      }
      
      // 🔒 MEJORA ESTÉTICA: Calcular ancho máximo por celda mejorado
      // Para dashboards grandes, usar más espacio eficientemente
      const totalCells = numColumns * numRows;
      const gap = mapping.__gap__ !== undefined ? parseInt(mapping.__gap__) : 12;
      const cellPadding = mapping.__cell_padding__ !== undefined ? parseInt(mapping.__cell_padding__) : 15;
      
      // Calcular espacio total disponible considerando gaps
      const totalGaps = gap * (numColumns - 1);
      const totalPadding = cellPadding * 2 * numColumns;
      const availableWidth = containerMaxWidth - totalGaps - totalPadding;
      
      // Calcular ancho por celda
      let estimatedMaxCellWidth = availableWidth / numColumns;
      
      // Para dashboards grandes (9+ celdas), permitir que los gráficos usen más espacio
      // reduciendo el factor de reducción y ajustando padding/gap
      if (totalCells >= 9) {
        // En dashboards grandes, reducir padding y gap para maximizar espacio
        const adjustedGap = gap * 0.7; // Reducir gap en 30%
        const adjustedPadding = cellPadding * 0.6; // Reducir padding en 40%
        const adjustedTotalGaps = adjustedGap * (numColumns - 1);
        const adjustedTotalPadding = adjustedPadding * 2 * numColumns;
        const adjustedAvailableWidth = containerMaxWidth - adjustedTotalGaps - adjustedTotalPadding;
        estimatedMaxCellWidth = (adjustedAvailableWidth / numColumns) * 0.98; // Usar 98% del espacio
      } else {
        // En dashboards pequeños, usar 90% para mantener márgenes cómodos
        estimatedMaxCellWidth = estimatedMaxCellWidth * 0.90;
      }
      
      // Asegurar un mínimo razonable (150px para dashboards grandes, 200px para pequeños)
      const minWidth = totalCells >= 9 ? 150 : 200;
      estimatedMaxCellWidth = Math.max(minWidth, estimatedMaxCellWidth);
      
      // 🔒 APLICAR EL LÍMITE
      width = Math.min(width, estimatedMaxCellWidth);
      
      // Log solo cuando sea necesario (evitar spam en dashboards sin max_width)
      if (window._bestlib_debug) {
        console.log(`[BESTLIB] max_width=${containerMaxWidth}, columns=${numColumns}, rows=${numRows}, totalCells=${totalCells}, maxCellWidth=${estimatedMaxCellWidth.toFixed(0)}, finalWidth=${width.toFixed(0)}`);
      }
    }
    // IMPORTANTE: NO aplicar límite si no hay max_width explícito
    // Esto evita que dashboards 2x2 sin límite se vean afectados
    
    // 🔒 MEJORA ESTÉTICA: Asegurar dimensiones mínimas razonables para el viewBox
    // El SVG ocupará 100% del contenedor, pero el viewBox necesita dimensiones válidas
    // Para dashboards grandes, usar mínimos más pequeños para aprovechar mejor el espacio
    const finalMinWidth = isLargeDashboard ? 180 : 200;
    const finalMinHeight = isLargeDashboard ? 130 : 150;
    width = Math.max(width, finalMinWidth);
    height = Math.max(height, finalMinHeight);
    
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
    
    // Diagnóstico: verificar estructura de datos para gráficos avanzados (siempre activo para debugging)
    if (['kde', 'distplot', 'rug', 'qqplot', 'ecdf', 'hist2d', 'polar', 'ridgeline', 'ribbon', 'funnel'].includes(chartType)) {
      console.log(`[BESTLIB] renderChartD3: ${chartType}`, {
        hasData: 'data' in spec,
        dataType: spec.data ? (Array.isArray(spec.data) ? 'array' : typeof spec.data) : 'undefined',
        dataLength: Array.isArray(spec.data) ? spec.data.length : (spec.data && typeof spec.data === 'object' ? Object.keys(spec.data).length : 0),
        hasSeries: 'series' in spec,
        seriesKeys: spec.series ? Object.keys(spec.series) : [],
        specKeys: Object.keys(spec),
        dataSample: spec.data ? (Array.isArray(spec.data) ? spec.data.slice(0, 2) : (typeof spec.data === 'object' ? Object.keys(spec.data).slice(0, 5) : spec.data)) : null
      });
    }
    
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
    } else if (chartType === 'star_coordinates') {
      renderStarCoordinatesD3(container, spec, d3, divId);
    } else if (chartType === 'parallel_coordinates') {
      renderParallelCoordinatesD3(container, spec, d3, divId);
    } else if (chartType === 'line_plot') {
      renderLinePlotD3(container, spec, d3, divId);
    } else if (chartType === 'horizontal_bar') {
      renderHorizontalBarD3(container, spec, d3, divId);
    } else if (chartType === 'hexbin') {
      renderHexbinD3(container, spec, d3, divId);
    } else if (chartType === 'errorbars') {
      renderErrorbarsD3(container, spec, d3, divId);
    } else if (chartType === 'fill_between') {
      renderFillBetweenD3(container, spec, d3, divId);
    } else if (chartType === 'step_plot') {
      renderStepPlotD3(container, spec, d3, divId);
    } else if (chartType === 'kde') {
      renderKdeD3(container, spec, d3, divId);
    } else if (chartType === 'distplot') {
      renderDistplotD3(container, spec, d3, divId);
    } else if (chartType === 'rug') {
      renderRugD3(container, spec, d3, divId);
    } else if (chartType === 'qqplot') {
      renderQqplotD3(container, spec, d3, divId);
    } else if (chartType === 'ecdf') {
      renderEcdfD3(container, spec, d3, divId);
    } else if (chartType === 'ridgeline') {
      renderRidgelineD3(container, spec, d3, divId);
    } else if (chartType === 'ribbon') {
      renderRibbonD3(container, spec, d3, divId);
    } else if (chartType === 'hist2d') {
      renderHist2dD3(container, spec, d3, divId);
    } else if (chartType === 'polar') {
      renderPolarD3(container, spec, d3, divId);
    } else if (chartType === 'funnel') {
      renderFunnelD3(container, spec, d3, divId);
    } else {
      // Tipo de gráfico no soportado aún, mostrar mensaje visible
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: Gráfico tipo "' + chartType + '" no implementado aún</strong><br/>' +
        '<small>Tipos soportados: bar, scatter, histogram, boxplot, heatmap, line, pie, violin, radviz, star_coordinates, parallel_coordinates, line_plot, horizontal_bar, hexbin, errorbars, fill_between, step_plot</small>' +
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
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 15, bottom: 40, left: 50 }  // Márgenes reducidos para dashboards grandes
      : { top: 30, right: 20, bottom: 60, left: 70 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
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

    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible')
      .style('display', 'block');
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
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    // Line chart necesita más espacio a la derecha para leyenda
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 100, bottom: 30, left: 35 }  // Márgenes reducidos, pero mantener espacio para leyenda
      : { top: 20, right: 150, bottom: 40, left: 50 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
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

    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible')
      .style('display', 'block'); // Evitar espacios en blanco
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
          
          // Obtener nombres de ejes del spec
          const xLabel = spec.xLabel || 'X';
          const yLabel = spec.yLabel || 'Y';
          
          tooltip
            .style('left', (mouseX + 10) + 'px')
            .style('top', (mouseY - 10) + 'px')
            .style('display', 'block')
            .html(`<strong>${name}</strong><br/><strong>${xLabel}:</strong> ${d.x.toFixed(2)}<br/><strong>${yLabel}:</strong> ${d.y.toFixed(2)}`)
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

    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
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
        
        // Obtener letra de la vista (para vistas principales)
        let viewLetter = spec.__view_letter__ || null;
        if (!viewLetter && container) {
          const letterAttr = container.getAttribute('data-letter');
          if (letterAttr) {
            viewLetter = letterAttr;
          }
        }
        
        // IMPORTANTE: Enviar todas las filas originales que corresponden a esta categoría
        // El slice tiene _original_rows que contiene todas las filas del DataFrame con esta categoría
        const originalRows = d.data._original_rows || d._original_row || (d._original_row ? [d._original_row] : null) || [];
        
        // Asegurar que originalRows sea un array
        const items = Array.isArray(originalRows) && originalRows.length > 0 ? originalRows : [];
        
        // Si no hay filas originales, intentar enviar al menos información de la categoría
        // (esto puede pasar si los datos no se prepararon correctamente)
        if (items.length === 0) {
          console.warn(`[Pie Chart] No se encontraron filas originales para la categoría ${category}. Asegúrese de que los datos se prepararon correctamente.`);
          // Enviar información de la categoría como fallback
          items.push({ category: category });
        }
        
        sendEvent(divId, 'select', {
          type: 'select',
          items: items,  // Enviar todas las filas originales de esta categoría
          indices: [],
          original_items: [d.data],
          _original_rows: items,  // También incluir como _original_rows para compatibilidad
          selected_category: category,
          __view_letter__: viewLetter,
          __is_primary_view__: spec.__is_primary_view__ || false
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
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 15, bottom: 40, left: 40 }  // Márgenes reducidos para dashboards grandes
      : { top: 20, right: 20, bottom: 60, left: 60 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      // Si el ancho calculado es mayor que el disponible, ajustar
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, minChartWidth);
      }
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      const maxAvailableHeight = container.clientHeight || height;
      if (height > maxAvailableHeight) {
        height = maxAvailableHeight;
        chartHeight = Math.max(height - margin.top - margin.bottom, minChartHeight);
      }
    }

    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible')
      .style('display', 'block'); // Evitar espacios en blanco
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
    
    // Validar que los puntos tengan coordenadas válidas y _weights
    const validPoints = points.filter(p => {
      if (!p) return false;
      // Verificar que tenga _weights para poder recalcular
      if (!p._weights || !Array.isArray(p._weights) || p._weights.length !== features.length) {
        return false;
      }
      // Verificar que las coordenadas iniciales sean válidas
      if (p.x == null || isNaN(p.x) || p.y == null || isNaN(p.y)) {
        return false;
      }
      return true;
    });
    
    if (validPoints.length === 0) {
      const debugInfo = points.length > 0 
        ? `Se encontraron ${points.length} puntos pero ninguno tiene _weights válidos o coordenadas válidas`
        : 'No se encontraron puntos en los datos';
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error en RadViz:</strong><br/>' +
        '<small>' + debugInfo + '</small><br/>' +
        '<small>Features: ' + (features.length > 0 ? features.join(', ') : 'ninguna') + '</small><br/>' +
        '<small>Verifica que los datos tengan _weights con ' + features.length + ' valores normalizados</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('RadViz: No hay puntos válidos', { points: points.slice(0, 3), spec });
      return;
    }
    
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 40, right: 40, bottom: 40, left: 40 }  // Márgenes reducidos para dashboards grandes
      : { top: 60, right: 60, bottom: 60, left: 60 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Calcular dimensiones del gráfico considerando límites del contenedor
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar dimensiones mínimas
    const minChartWidth = 300;
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // Asegurar que no exceda el contenedor
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, 200);
      }
    }
    
    const minChartHeight = 300;
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }

    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    // Calcular centro del gráfico
    const centerX = margin.left + chartWidth / 2;
    const centerY = margin.top + chartHeight / 2;
    const radius = Math.min(chartWidth, chartHeight) / 2 - 40;
    
    // Asegurar que el radio sea válido
    if (radius <= 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #d32f2f;">Error: Dimensiones del gráfico muy pequeñas</div>';
      return;
    }
    
    const g = svg.append('g')
      .attr('transform', `translate(${centerX},${centerY})`);

    // Círculo de referencia
    g.append('circle')
      .attr('r', radius)
      .attr('fill', 'none')
      .attr('stroke', '#aaa')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '2,2');

    // Anchors (features) - inicializar con posiciones uniformes
    const anchorPos = features.map((f, i) => {
      const ang = 2 * Math.PI * i / Math.max(1, features.length) - Math.PI / 2; // Empezar desde arriba
      return { 
        x: radius * Math.cos(ang), 
        y: radius * Math.sin(ang), 
        name: String(f),
        angle: ang,
        index: i
      };
    });
    
    // Escala para los puntos - usar dominio dinámico basado en el radio
    const maxExtent = radius * 0.9; // Margen de seguridad
    
    // Escalar para que los puntos estén dentro del círculo
    const toX = d3.scaleLinear()
      .domain([-maxExtent, maxExtent])
      .range([-radius * 0.85, radius * 0.85]);
    
    const toY = d3.scaleLinear()
      .domain([-maxExtent, maxExtent])
      .range([-radius * 0.85, radius * 0.85]);
    
    // Flag para evitar actualizaciones múltiples simultáneas
    let isUpdating = false;
    
    // Función para recalcular posiciones de puntos cuando se mueven los anchors
    function recalculateRadVizPoints() {
      if (isUpdating) return; // Evitar actualizaciones múltiples
      isUpdating = true;
      
      try {
        // Recalcular todos los puntos
        g.selectAll('.rvpt').each(function(d) {
          try {
            // Verificar que el punto tenga _weights válidos
            if (!d._weights || !Array.isArray(d._weights) || d._weights.length !== anchorPos.length) {
              console.warn('RadViz: Punto sin _weights válidos', d);
              return;
            }
            
            // Calcular nueva posición usando los nuevos anchors
            const weights = d._weights;
            const s = d3.sum(weights) || 1.0;
            
            // Calcular posición ponderada
            let newX = 0;
            let newY = 0;
            for (let i = 0; i < weights.length; i++) {
              if (i < anchorPos.length && !isNaN(weights[i]) && isFinite(weights[i])) {
                newX += weights[i] * anchorPos[i].x;
                newY += weights[i] * anchorPos[i].y;
              }
            }
            newX = newX / s;
            newY = newY / s;
            
            // Validar que las nuevas coordenadas sean válidas
            if (isNaN(newX) || !isFinite(newX) || isNaN(newY) || !isFinite(newY)) {
              console.warn('RadViz: Coordenadas inválidas después del cálculo', { newX, newY, weights });
              return;
            }
            
            // Normalizar para asegurar que el punto esté dentro del círculo
            const distance = Math.sqrt(newX * newX + newY * newY);
            const maxDistance = radius * 0.85; // Margen de seguridad
            
            if (distance > maxDistance && distance > 0) {
              // Escalar hacia el centro para mantener dentro del círculo
              const scale = maxDistance / distance;
              newX = newX * scale;
              newY = newY * scale;
            }
            
            // Actualizar posición del punto en los datos
            d.x = newX;
            d.y = newY;
            
            // Actualizar visualmente con transición suave (solo si el elemento existe)
            const element = d3.select(this);
            if (!element.empty()) {
              element
                .transition()
                .duration(200)
                .attr('cx', toX(newX))
                .attr('cy', toY(newY));
            }
          } catch (err) {
            console.error('RadViz: Error recalculando punto', err, d);
          }
        });
      } catch (err) {
        console.error('RadViz: Error en recalculateRadVizPoints', err);
      } finally {
        isUpdating = false;
      }
    }
    
    // Dibujar líneas desde el centro hasta los anchors
    const anchorLines = g.selectAll('.anchor-line')
      .data(anchorPos)
      .enter()
      .append('line')
      .attr('class', (d, i) => `anchor-line anchor-line-${i}`)
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', d => d.x)
      .attr('y2', d => d.y)
      .attr('stroke', '#ddd')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '1,1')
      .lower(); // Poner detrás de los puntos
    
    // Dibujar círculos en los anchors (arrastrables)
    const anchorCircles = g.selectAll('.anchor')
      .data(anchorPos)
      .enter()
      .append('circle')
      .attr('class', (d, i) => `anchor anchor-${i}`)
      .attr('r', 6)
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('fill', '#555')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'move')
      .style('pointer-events', 'all')
      .call(d3.drag()
        .on('start', function(event, d) {
          event.sourceEvent.stopPropagation(); // Evitar conflictos con otros eventos
          d3.select(this).attr('fill', '#ff6b35').attr('r', 8);
        })
        .on('drag', function(event, d) {
          event.sourceEvent.stopPropagation();
          
          try {
            // Calcular nuevo ángulo basado en posición del mouse relativa al centro
            const [mx, my] = d3.pointer(event, g.node());
            
            // Validar coordenadas del mouse
            if (isNaN(mx) || isNaN(my) || !isFinite(mx) || !isFinite(my)) {
              return;
            }
            
            // Calcular ángulo
            const angle = Math.atan2(my, mx);
            
            // Validar ángulo
            if (isNaN(angle) || !isFinite(angle)) {
              return;
            }
            
            // Actualizar posición del anchor (mantener en el círculo)
            d.angle = angle;
            d.x = radius * Math.cos(angle);
            d.y = radius * Math.sin(angle);
            
            // Validar nuevas coordenadas
            if (isNaN(d.x) || isNaN(d.y) || !isFinite(d.x) || !isFinite(d.y)) {
              return;
            }
            
            // Actualizar círculo
            d3.select(this)
              .attr('cx', d.x)
              .attr('cy', d.y);
            
            // Actualizar línea correspondiente
            const line = g.select(`.anchor-line-${d.index}`);
            if (!line.empty()) {
              line
                .attr('x2', d.x)
                .attr('y2', d.y);
            }
            
            // Actualizar etiqueta
            const label = g.select(`.alabel-${d.index}`);
            if (!label.empty()) {
              const labelRadius = radius * 1.15;
              label
                .attr('x', labelRadius * Math.cos(angle))
                .attr('y', labelRadius * Math.sin(angle));
            }
            
            // Recalcular posiciones de todos los puntos basado en los nuevos anchors
            recalculateRadVizPoints();
          } catch (err) {
            console.error('RadViz: Error en drag', err);
          }
        })
        .on('end', function(event, d) {
          event.sourceEvent.stopPropagation();
          d3.select(this).attr('fill', '#555').attr('r', 6);
        })
      );
    
    // Etiquetas de los anchors
    const anchorLabels = g.selectAll('.alabel')
      .data(anchorPos)
      .enter()
      .append('text')
      .attr('class', (d, i) => `alabel alabel-${i}`)
      .attr('x', d => d.x * 1.15)
      .attr('y', d => d.y * 1.15)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '11px')
      .style('fill', '#333')
      .style('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(d => d.name);

    
    // Obtener categorías únicas
    const categories = [...new Set(validPoints.map(p => p.category).filter(c => c != null && c !== ''))];
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(categories.length > 0 ? categories : ['default']);

    // Dibujar puntos (después de inicializar todo)
    const pointElements = g.selectAll('.rvpt')
      .data(validPoints)
      .enter()
      .append('circle')
      .attr('class', 'rvpt')
      .attr('cx', d => {
        try {
          return toX(d.x);
        } catch (err) {
          console.error('RadViz: Error calculando cx', err, d);
          return 0;
        }
      })
      .attr('cy', d => {
        try {
          return toY(d.y);
        } catch (err) {
          console.error('RadViz: Error calculando cy', err, d);
          return 0;
        }
      })
      .attr('r', 3)
      .attr('fill', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('opacity', 0.6)
      .attr('stroke', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .style('pointer-events', 'all')
      .on('mouseenter', function(event, d) {
        event.stopPropagation();
        d3.select(this)
          .attr('r', 5)
          .attr('opacity', 1);
      })
      .on('mouseleave', function(event) {
        event.stopPropagation();
        d3.select(this)
          .attr('r', 3)
          .attr('opacity', 0.6);
      });
    
    // Si el spec tiene interactive=true, agregar brush selection
    if (spec.interactive) {
      // Crear brush para selección (en coordenadas del grupo g, que tiene el centro en 0,0)
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer')
        .style('pointer-events', 'all');
      
      const brush = d3.brush()
        .extent([[-radius * 0.9, -radius * 0.9], [radius * 0.9, radius * 0.9]])
        .on('start', function(event) {
          // Durante el brush, desactivar eventos de puntos temporalmente
          g.selectAll('.rvpt')
            .style('pointer-events', 'none');
        })
        .on('brush', function(event) {
          if (!event.selection) {
            // Si no hay selección, mostrar todos los puntos normalmente
            g.selectAll('.rvpt')
              .attr('opacity', 0.6)
              .attr('r', 3);
            return;
          }
          
          // Obtener selección (en coordenadas del grupo g)
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Resaltar puntos dentro de la selección durante el brush
          g.selectAll('.rvpt').each(function(d) {
            try {
              // Obtener coordenadas transformadas del punto
              const px = toX(d.x);
              const py = toY(d.y);
              
              // Verificar si el punto está dentro de la selección
              const isInBrush = px >= Math.min(x0, x1) && px <= Math.max(x0, x1) &&
                                py >= Math.min(y0, y1) && py <= Math.max(y0, y1);
              
              const dot = d3.select(this);
              if (isInBrush) {
                // Resaltar puntos dentro del brush
                dot
                  .attr('r', 5)
                  .attr('opacity', 1);
              } else {
                // Atenuar puntos fuera del brush
                dot
                  .attr('r', 3)
                  .attr('opacity', 0.2);
              }
            } catch (err) {
              // Ignorar errores
            }
            });
        })
        .on('end', function(event) {
          // Restaurar eventos de puntos
          g.selectAll('.rvpt')
            .style('pointer-events', 'all');
          
          if (!event.selection) {
            // Si no hay selección, restaurar visualización y enviar todos los puntos
            g.selectAll('.rvpt')
              .attr('opacity', 0.6)
              .attr('r', 3);
            
            const allItems = validPoints.map((p, i) => {
              const item = {
                ...p,
                index: i
              };
              // Preservar _original_row si existe
              if (p._original_row) {
                item._original_row = p._original_row;
              }
              return item;
            });
            sendEvent(divId, 'select', {
              type: 'select',
              items: allItems,
              count: allItems.length
            });
            return;
          }
          
          // Obtener selección (en coordenadas del grupo g)
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Filtrar puntos dentro de la selección
          const selected = validPoints.filter((p, i) => {
            try {
              // Obtener coordenadas transformadas del punto
              const px = toX(p.x);
              const py = toY(p.y);
              
              // Validar coordenadas
              if (isNaN(px) || isNaN(py) || !isFinite(px) || !isFinite(py)) {
                return false;
              }
              
              // Verificar si el punto está dentro de la selección
              return px >= Math.min(x0, x1) && px <= Math.max(x0, x1) &&
                     py >= Math.min(y0, y1) && py <= Math.max(y0, y1);
            } catch (err) {
              console.warn('RadViz: Error verificando selección para punto', p, err);
              return false;
            }
          }).map((p, i) => {
            // Agregar datos originales si están disponibles
            const item = {
              ...p,
              index: validPoints.indexOf(p)
            };
            // Preservar _original_row si existe
            if (p._original_row) {
              item._original_row = p._original_row;
            }
            return item;
          });
          
          // Restaurar visualización de puntos
          g.selectAll('.rvpt')
            .attr('opacity', 0.6)
            .attr('r', 3);
          
          // Resaltar puntos seleccionados
          g.selectAll('.rvpt').filter((d, i) => selected.some(s => s.index === i))
            .attr('r', 5)
            .attr('opacity', 1)
            .attr('stroke-width', 2);
          
          // Enviar evento de selección
          sendEvent(divId, 'select', {
            type: 'select',
            items: selected,
            count: selected.length
          });
        });
      
      // Agregar brush al grupo (después de dibujar puntos)
      brushGroup.call(brush);
      
      // Asegurar que el overlay del brush capture eventos
      brushGroup.selectAll('.overlay')
        .style('pointer-events', 'all')
        .style('cursor', 'crosshair');
    }
  }
  
  /**
   * Star Coordinates con D3.js
   * Similar a RadViz pero los nodos pueden moverse libremente por toda el área
   */
  function renderStarCoordinatesD3(container, spec, d3, divId) {
    // Limpiar contenedor
    container.innerHTML = '';
    
    const points = spec.data || [];
    const features = spec.features || [];
    
    // Validar datos
    if (!points || points.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay datos para Star Coordinates</strong><br/>' +
        '<small>El spec debe contener data con puntos y features</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Star Coordinates: No hay datos', { spec });
      return;
    }
    
    if (!features || features.length < 2) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: Se requieren al menos 2 features para Star Coordinates</strong><br/>' +
        '<small>Features disponibles: ' + (features ? features.length : 0) + '</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Star Coordinates: Features insuficientes', { features });
      return;
    }
    
    // Validar que los puntos tengan coordenadas válidas y _weights
    const validPoints = points.filter(p => {
      if (!p) return false;
      // Verificar que tenga _weights para poder recalcular
      if (!p._weights || !Array.isArray(p._weights) || p._weights.length !== features.length) {
        return false;
      }
      // Verificar que las coordenadas iniciales sean válidas
      if (p.x == null || isNaN(p.x) || p.y == null || isNaN(p.y)) {
        return false;
      }
      return true;
    });
    
    if (validPoints.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay puntos válidos para Star Coordinates</strong><br/>' +
        '<small>Los puntos deben tener _weights con ' + features.length + ' valores normalizados y coordenadas válidas</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Star Coordinates: No hay puntos válidos', { points: points.slice(0, 3), spec });
      return;
    }
    
    const dims = getChartDimensions(container, spec, 520, 380);
    let width = dims.width;
    let height = dims.height;
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 40, right: 40, bottom: 40, left: 40 }  // Márgenes reducidos para dashboards grandes
      : { top: 60, right: 60, bottom: 60, left: 60 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Calcular dimensiones respetando límites del contenedor
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const minChartWidth = 300;
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // Asegurar que no exceda el contenedor
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, 200);
      }
    }
    
    const minChartHeight = 300;
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    }
    
    // Verificar dimensiones válidas
    if (chartWidth <= 0 || chartHeight <= 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #d32f2f;">Error: Dimensiones del gráfico muy pequeñas</div>';
      return;
    }
    
    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Calcular centro del área del gráfico
    const centerX = chartWidth / 2;
    const centerY = chartHeight / 2;
    // IMPORTANTE: Usar un radio inicial para posicionar los nodos en un círculo al inicio
    // Pero los nodos pueden moverse libremente por toda el área del gráfico
    const initialRadius = Math.min(chartWidth, chartHeight) / 2 - 60;
    
    // IMPORTANTE: Los features ya vienen ordenados alfabéticamente desde Python
    // No es necesario ordenarlos de nuevo, solo usarlos directamente
    // Esto asegura que los nodos estén en el mismo orden que los weights en los puntos
    
    // Inicializar posiciones de nodos (features) distribuidas uniformemente en un círculo
    // Los nodos pueden moverse, pero se mantendrán dentro del área del círculo máximo
    const anchorPos = features.map((f, i) => {
      const ang = 2 * Math.PI * i / features.length - Math.PI / 2;
      return {
        x: centerX + initialRadius * Math.cos(ang),
        y: centerY + initialRadius * Math.sin(ang),
        name: String(f),
        index: i
      };
    });
    
    // IMPORTANTE: Usar escalas fijas basadas en coordenadas normalizadas [-1, 1]
    // Esto asegura que los puntos siempre estén dentro del área visible
    // Las coordenadas de los puntos están normalizadas a [-1, 1] en Python
    const scaleFactor = Math.min(chartWidth, chartHeight) / 2 - 50; // Factor de escala para el círculo
    let toX = d3.scaleLinear()
      .domain([-1, 1])
      .range([centerX - scaleFactor, centerX + scaleFactor]);
    let toY = d3.scaleLinear()
      .domain([-1, 1])
      .range([centerY + scaleFactor, centerY - scaleFactor]); // Invertir Y para que -1 esté abajo
    
    // Función para actualizar escalas basadas en posiciones de nodos
    // IMPORTANTE: Usar escalas dinámicas que se ajustan a las posiciones de los nodos
    // Esto permite que los puntos estén visibles sin importar dónde estén los nodos
    function updateScales() {
      // Calcular el bounding box de los nodos
      const nodeX = anchorPos.map(n => n.x);
      const nodeY = anchorPos.map(n => n.y);
      
      if (nodeX.length === 0) {
        // Si no hay nodos, usar escalas por defecto centradas en el gráfico
        const defaultRadius = Math.min(chartWidth, chartHeight) / 2 - 50;
        toX = d3.scaleLinear()
          .domain([-1, 1])
          .range([centerX - defaultRadius, centerX + defaultRadius]);
        toY = d3.scaleLinear()
          .domain([-1, 1])
          .range([centerY + defaultRadius, centerY - defaultRadius]);
        return;
      }
      
      // Calcular el centro de los nodos (no necesariamente el centro del gráfico)
      const minX = Math.min(...nodeX);
      const maxX = Math.max(...nodeX);
      const minY = Math.min(...nodeY);
      const maxY = Math.max(...nodeY);
      
      const nodeCenterX = (minX + maxX) / 2;
      const nodeCenterY = (minY + maxY) / 2;
      
      // Calcular el radio máximo desde el centro de los nodos
      const nodeRadius = Math.max(
        ...anchorPos.map(n => {
          const dx = n.x - nodeCenterX;
          const dy = n.y - nodeCenterY;
          return Math.sqrt(dx * dx + dy * dy);
        })
      ) || initialRadius;
      
      // IMPORTANTE: Calcular el radio disponible para los puntos
      // Los puntos están normalizados a [-1, 1] en coordenadas relativas al centro de los nodos
      // Necesitamos un radio suficiente para que estén visibles
      const margin = 30; // Margen desde los bordes
      const availableWidth = chartWidth - margin * 2;
      const availableHeight = chartHeight - margin * 2;
      const maxAvailableRadius = Math.min(availableWidth, availableHeight) / 2;
      
      // Usar el máximo entre el radio de los nodos (con margen) y un radio mínimo
      // Esto asegura que los puntos siempre estén visibles
      const actualRadius = Math.max(
        nodeRadius * 1.3, // Permitir un 30% más de espacio basado en nodos
        Math.min(availableWidth, availableHeight) / 3 // O usar al menos 1/3 del área disponible
      );
      
      // Limitar el radio al máximo disponible para mantener los puntos visibles
      const finalRadius = Math.min(actualRadius, maxAvailableRadius);
      
      // IMPORTANTE: Actualizar escalas para que los puntos estén centrados en el centro de los nodos
      // Esto permite que los puntos sigan las posiciones de los nodos
      toX = d3.scaleLinear()
        .domain([-1, 1])
        .range([nodeCenterX - finalRadius, nodeCenterX + finalRadius]);
      toY = d3.scaleLinear()
        .domain([-1, 1])
        .range([nodeCenterY + finalRadius, nodeCenterY - finalRadius]); // Invertir Y para que -1 esté abajo
    }
    
    // Flag para evitar actualizaciones múltiples simultáneas
    let isUpdating = false;
    
    // Función para recalcular posiciones de puntos cuando se mueven los nodos
    function recalculateStarPoints() {
      if (isUpdating) return; // Evitar actualizaciones múltiples
      isUpdating = true;
      
      try {
        // Primero, actualizar escalas basadas en posiciones de nodos
        updateScales();
        
        // IMPORTANTE: Normalizar posiciones de nodos a coordenadas relativas al centro de los nodos
        // Convertir coordenadas de pantalla a coordenadas normalizadas
        // Esto permite que los nodos se muevan libremente mientras los puntos siguen siendo visibles
        
        // Calcular el bounding box de los nodos
        const nodeX = anchorPos.map(n => n.x);
        const nodeY = anchorPos.map(n => n.y);
        
        if (nodeX.length === 0) {
          // Si no hay nodos, no hacer nada
          return;
        }
        
        // Calcular el centro de los nodos (no necesariamente el centro del gráfico)
        const minX = Math.min(...nodeX);
        const maxX = Math.max(...nodeX);
        const minY = Math.min(...nodeY);
        const maxY = Math.max(...nodeY);
        
        const nodeCenterX = (minX + maxX) / 2;
        const nodeCenterY = (minY + maxY) / 2;
        
        // Calcular el radio máximo desde el centro de los nodos
        const nodeDistances = anchorPos.map(n => {
          const dx = n.x - nodeCenterX;
          const dy = n.y - nodeCenterY;
          return Math.sqrt(dx * dx + dy * dy);
        });
        const maxNodeDistance = Math.max(...nodeDistances, 1) || initialRadius;
        
        // IMPORTANTE: Usar el radio máximo de los nodos como scale para normalizar
        // Esto asegura que las coordenadas normalizadas de los nodos estén dentro de [-1, 1]
        // cuando los nodos están alrededor del centro de los nodos
        // Usar un mínimo para evitar divisiones por cero o escalas muy pequeñas
        const nodeScale = Math.max(maxNodeDistance, initialRadius * 0.5);
        
        // Normalizar posiciones de nodos a coordenadas relativas al centro de los nodos
        // IMPORTANTE: Los weights están en el mismo orden que los features (orden alfabético)
        const normalizedNodes = anchorPos.map(n => {
          const nx = (n.x - nodeCenterX) / nodeScale;
          const ny = (n.y - nodeCenterY) / nodeScale;
          // IMPORTANTE: No limitar las coordenadas normalizadas aquí
          // Permitir que estén fuera de [-1, 1] para reflejar las posiciones reales de los nodos
          // La normalización de los puntos se hará después para mantenerlos visibles
          return {
            x: nx,
            y: ny
          };
        });
        
        g.selectAll('.scpt').each(function(d) {
          try {
            // Verificar que el punto tenga _weights válidos
            // IMPORTANTE: Los weights están en el mismo orden que los features (orden alfabético)
            if (!d._weights || !Array.isArray(d._weights) || d._weights.length !== features.length) {
              console.warn('Star Coordinates: Punto sin _weights válidos', d);
              return;
            }
            
            const weights = d._weights;
            const s = d3.sum(weights) || 1.0;
            
            // IMPORTANTE: Calcular posición ponderada usando nodos normalizados
            // Los weights y los nodos están en el mismo orden (alfabético)
            let newX = 0;
            let newY = 0;
            
            for (let i = 0; i < normalizedNodes.length && i < weights.length; i++) {
              const node = normalizedNodes[i];
              const weight = weights[i];
              
              if (!isNaN(weight) && isFinite(weight)) {
                newX += weight * node.x;
                newY += weight * node.y;
              }
            }
            
            newX = newX / s;
            newY = newY / s;
            
            // IMPORTANTE: Normalizar para que los puntos estén dentro de [-1, 1]
            // Esto asegura que los puntos siempre estén dentro del área visible
            const distance = Math.sqrt(newX * newX + newY * newY);
            if (distance > 1.0) {
              newX = newX / distance;
              newY = newY / distance;
            }
            
            // Asegurar que las coordenadas estén en [-1, 1]
            newX = Math.max(-1.0, Math.min(1.0, newX));
            newY = Math.max(-1.0, Math.min(1.0, newY));
            
            // Validar que las nuevas coordenadas sean válidas
            if (isNaN(newX) || !isFinite(newX) || isNaN(newY) || !isFinite(newY)) {
              console.warn('Star Coordinates: Coordenadas inválidas después del cálculo', { newX, newY, weights });
              return;
            }
            
            // Actualizar posición del punto en los datos (en coordenadas normalizadas)
            d.x = newX;
            d.y = newY;
            
            // Actualizar visualmente usando las escalas
            const element = d3.select(this);
            if (!element.empty()) {
              element
            .transition()
                .duration(200)
                .attr('cx', toX(newX))
                .attr('cy', toY(newY));
            }
          } catch (err) {
            console.error('Star Coordinates: Error recalculando punto', err, d);
          }
        });
      } catch (err) {
        console.error('Star Coordinates: Error en recalculateStarPoints', err);
      } finally {
        isUpdating = false;
      }
    }
    
    // Inicializar escalas
    updateScales();
    
    // IMPORTANTE: Los nodos pueden moverse libremente por toda el área del gráfico
    // Esta es la ventaja principal de Star Coordinates sobre RadViz
    // Sin embargo, dibujamos líneas desde el centro para tener un punto de referencia visual
    
    // Dibujar líneas desde el centro del gráfico hasta los nodos (para referencia visual)
    const anchorLines = g.selectAll('.anchor-line')
      .data(anchorPos)
      .enter()
      .append('line')
      .attr('class', (d, i) => `anchor-line anchor-line-${i}`)
      .attr('x1', centerX)
      .attr('y1', centerY)
      .attr('x2', d => d.x)
      .attr('y2', d => d.y)
      .attr('stroke', '#ddd')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '2,2')
      .style('pointer-events', 'none')
      .lower();
    
    // Dibujar nodos (arrastrables libremente por toda el área)
    const anchorCircles = g.selectAll('.anchor')
      .data(anchorPos)
      .enter()
      .append('circle')
      .attr('class', (d, i) => `anchor anchor-${i}`)
      .attr('r', 8)
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('fill', '#555')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'move')
      .style('pointer-events', 'all')
      .call(d3.drag()
        .on('start', function(event, d) {
          event.sourceEvent.stopPropagation();
          d3.select(this).attr('fill', '#ff6b35').attr('r', 10);
        })
        .on('drag', function(event, d) {
          event.sourceEvent.stopPropagation();
          
          try {
            // Obtener posición del mouse relativa al grupo g
            const [mx, my] = d3.pointer(event, g.node());
            
            // Validar coordenadas del mouse
            if (isNaN(mx) || isNaN(my) || !isFinite(mx) || !isFinite(my)) {
              return;
            }
            
            // IMPORTANTE: Permitir movimiento libre de los nodos por toda el área del gráfico
            // Esta es la ventaja principal de Star Coordinates sobre RadViz
            // Los nodos pueden moverse libremente, solo limitados por el área del gráfico
            const padding = 10; // Margen mínimo desde los bordes
            
            // Permitir movimiento libre dentro del área del gráfico
            d.x = Math.max(padding, Math.min(chartWidth - padding, mx));
            d.y = Math.max(padding, Math.min(chartHeight - padding, my));
            
            // Validar nuevas coordenadas
            if (isNaN(d.x) || isNaN(d.y) || !isFinite(d.x) || !isFinite(d.y)) {
              return;
            }
            
            // Actualizar círculo
            d3.select(this)
              .attr('cx', d.x)
              .attr('cy', d.y);
            
            // Actualizar línea desde el centro hasta el nodo (para referencia visual)
            const line = g.select(`.anchor-line-${d.index}`);
            if (!line.empty()) {
              line
                .attr('x2', d.x)
                .attr('y2', d.y);
            }
            
            // Actualizar etiqueta
            const label = g.select(`.alabel-${d.index}`);
            if (!label.empty()) {
              label
                .attr('x', d.x)
                .attr('y', d.y - 15);
            }
            
            // Recalcular posiciones de todos los puntos
            recalculateStarPoints();
          } catch (err) {
            console.error('Star Coordinates: Error en drag', err);
          }
        })
        .on('end', function(event, d) {
          event.sourceEvent.stopPropagation();
          d3.select(this).attr('fill', '#555').attr('r', 8);
        })
      );
    
    // Etiquetas de los nodos
    const anchorLabels = g.selectAll('.alabel')
      .data(anchorPos)
      .enter()
      .append('text')
      .attr('class', (d, i) => `alabel alabel-${i}`)
      .attr('x', d => d.x)
      .attr('y', d => d.y - 15)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '11px')
      .style('fill', '#333')
      .style('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(d => d.name);
    
    // Obtener categorías únicas
    const categories = [...new Set(validPoints.map(p => p.category).filter(c => c != null && c !== ''))];
    const color = d3.scaleOrdinal(d3.schemeCategory10).domain(categories.length > 0 ? categories : ['default']);
    
    // Dibujar puntos (después de inicializar escalas)
    g.selectAll('.scpt')
      .data(validPoints)
      .enter()
      .append('circle')
      .attr('class', 'scpt')
      .attr('cx', d => {
        try {
          if (d.x == null || isNaN(d.x) || !isFinite(d.x)) return centerX;
          return toX(d.x);
        } catch (err) {
          console.error('Star Coordinates: Error calculando cx', err, d);
          return centerX;
        }
      })
      .attr('cy', d => {
        try {
          if (d.y == null || isNaN(d.y) || !isFinite(d.y)) return centerY;
          return toY(d.y);
        } catch (err) {
          console.error('Star Coordinates: Error calculando cy', err, d);
          return centerY;
        }
      })
      .attr('r', 3)
      .attr('fill', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('opacity', 0.6)
      .attr('stroke', d => d.category && categories.includes(d.category) ? color(d.category) : '#4a90e2')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .style('pointer-events', 'all')
      .on('mouseenter', function(event, d) {
        event.stopPropagation();
        d3.select(this)
          .attr('r', 5)
          .attr('opacity', 1);
      })
      .on('mouseleave', function(event) {
        event.stopPropagation();
        d3.select(this)
          .attr('r', 3)
          .attr('opacity', 0.6);
      });
    
    // Si el spec tiene interactive=true, agregar brush selection
    if (spec.interactive) {
      // Crear brush para selección (en coordenadas del grupo g)
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer')
        .style('pointer-events', 'all');
      
      const brush = d3.brush()
        .extent([[0, 0], [chartWidth, chartHeight]])
        .on('start', function(event) {
          // Durante el brush, desactivar eventos de puntos temporalmente
          g.selectAll('.scpt')
            .style('pointer-events', 'none');
        })
        .on('brush', function(event) {
          if (!event.selection) {
            // Si no hay selección, mostrar todos los puntos normalmente
            g.selectAll('.scpt')
              .attr('opacity', 0.6)
              .attr('r', 3);
            return;
          }
          
          // Obtener selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Resaltar puntos dentro de la selección durante el brush
          g.selectAll('.scpt').each(function(d) {
            try {
              // Obtener coordenadas transformadas del punto
              const px = toX(d.x);
              const py = toY(d.y);
              
              // Validar coordenadas
              if (isNaN(px) || isNaN(py) || !isFinite(px) || !isFinite(py)) {
                return;
              }
              
              // Verificar si el punto está dentro de la selección
              const isInBrush = px >= Math.min(x0, x1) && px <= Math.max(x0, x1) &&
                                py >= Math.min(y0, y1) && py <= Math.max(y0, y1);
              
              const dot = d3.select(this);
              if (isInBrush) {
                // Resaltar puntos dentro del brush
                dot
                  .attr('r', 5)
                  .attr('opacity', 1);
              } else {
                // Atenuar puntos fuera del brush
                dot
                  .attr('r', 3)
                  .attr('opacity', 0.2);
              }
            } catch (err) {
              // Ignorar errores
            }
          });
        })
        .on('end', function(event) {
          // Restaurar eventos de puntos
          g.selectAll('.scpt')
            .style('pointer-events', 'all');
          
          if (!event.selection) {
            // Si no hay selección, restaurar visualización y enviar todos los puntos
            g.selectAll('.scpt')
              .attr('opacity', 0.6)
              .attr('r', 3);
            
            const allItems = validPoints.map((p, i) => {
              const item = {
                ...p,
                index: i
              };
              // Preservar _original_row si existe
              if (p._original_row) {
                item._original_row = p._original_row;
              }
              return item;
            });
            sendEvent(divId, 'select', {
              type: 'select',
              items: allItems,
              count: allItems.length
            });
            return;
          }
          
          // Obtener selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Filtrar puntos dentro de la selección
          const selected = validPoints.filter((p, i) => {
            try {
              // Obtener coordenadas transformadas del punto
              const px = toX(p.x);
              const py = toY(p.y);
              
              // Validar coordenadas
              if (isNaN(px) || isNaN(py) || !isFinite(px) || !isFinite(py)) {
                return false;
              }
              
              // Verificar si el punto está dentro de la selección
              return px >= Math.min(x0, x1) && px <= Math.max(x0, x1) &&
                     py >= Math.min(y0, y1) && py <= Math.max(y0, y1);
            } catch (err) {
              console.warn('Star Coordinates: Error verificando selección para punto', p, err);
              return false;
            }
          }).map((p, i) => {
            // Agregar datos originales si están disponibles
            const item = {
              ...p,
              index: validPoints.indexOf(p)
            };
            // Preservar _original_row si existe
            if (p._original_row) {
              item._original_row = p._original_row;
            }
            return item;
          });
          
          // Restaurar visualización de puntos
          g.selectAll('.scpt')
            .attr('opacity', 0.6)
            .attr('r', 3);
          
          // Resaltar puntos seleccionados
          g.selectAll('.scpt').filter((d, i) => selected.some(s => s.index === i))
            .attr('r', 5)
            .attr('opacity', 1)
            .attr('stroke-width', 2);
          
          // Enviar evento de selección
          sendEvent(divId, 'select', {
            type: 'select',
            items: selected,
            count: selected.length
          });
        });
      
      // Agregar brush al grupo (después de dibujar puntos)
      brushGroup.call(brush);
      
      // Asegurar que el overlay del brush capture eventos
      brushGroup.selectAll('.overlay')
        .style('pointer-events', 'all')
        .style('cursor', 'crosshair');
    }
  }
  
  /**
   * Parallel Coordinates Plot con D3.js
   * Ejes paralelos que pueden moverse y reordenarse
   */
  function renderParallelCoordinatesD3(container, spec, d3, divId) {
    // Limpiar contenedor
    container.innerHTML = '';
    
    const data = spec.data || [];
    const dimensions = spec.dimensions || [];
    
    // Validar datos
    if (!data || data.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay datos para Parallel Coordinates</strong><br/>' +
        '<small>El spec debe contener data con puntos</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Parallel Coordinates: No hay datos', { spec });
      return;
    }
    
    if (!dimensions || dimensions.length < 2) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: Se requieren al menos 2 dimensiones para Parallel Coordinates</strong><br/>' +
        '<small>Dimensiones disponibles: ' + (dimensions ? dimensions.length : 0) + '</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Parallel Coordinates: Dimensiones insuficientes', { dimensions });
        return;
      }
      
    // Validar que los datos tengan al menos una dimensión válida
    const validData = data.filter(d => {
      if (!d) return false;
      // Verificar que al menos una dimensión tenga valor válido
      return dimensions.some(dim => {
        const val = d[dim];
        return val != null && !isNaN(val) && isFinite(val);
      });
    });
    
    if (validData.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay datos válidos para Parallel Coordinates</strong><br/>' +
        '<small>Los datos deben tener valores válidos para al menos una dimensión</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('Parallel Coordinates: No hay datos válidos', { data: data.slice(0, 3), spec });
      return;
    }
    
    const dims = getChartDimensions(container, spec, 600, 400);
    let width = dims.width;
    let height = dims.height;
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 15, bottom: 25, left: 15 }  // Márgenes reducidos para dashboards grandes
      : { top: 30, right: 20, bottom: 30, left: 20 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que las dimensiones respeten el contenedor
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Asegurar que no exceda el contenedor
    const maxAvailableWidth = container.clientWidth || width;
    const maxAvailableHeight = container.clientHeight || height;
    if (width > maxAvailableWidth) {
      width = maxAvailableWidth;
      chartWidth = Math.max(width - margin.left - margin.right, 200);
    }
    if (height > maxAvailableHeight) {
      height = maxAvailableHeight;
      chartHeight = Math.max(height - margin.top - margin.bottom, 150);
    }
    
    const minChartWidth = 400;
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
    
    // Verificar dimensiones válidas
    if (chartWidth <= 0 || chartHeight <= 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: #d32f2f;">Error: Dimensiones del gráfico muy pequeñas</div>';
      return;
    }
    
    // 🔒 MEJORA ESTÉTICA: SVG debe ocupar 100% del contenedor
    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Calcular escalas para cada dimensión
    const scales = {};
    const axisPositions = [];
    
    dimensions.forEach((dim, i) => {
      try {
        // Calcular dominio de valores para esta dimensión
        const values = validData.map(d => {
          const val = d[dim];
          if (val == null || isNaN(val) || !isFinite(val)) return null;
          return parseFloat(val);
        }).filter(v => v != null && isFinite(v));
        
        if (values.length === 0) {
          // Si no hay valores válidos, usar dominio por defecto
          scales[dim] = d3.scaleLinear().domain([0, 1]).range([chartHeight, 0]);
        } else {
          const minVal = d3.min(values);
          const maxVal = d3.max(values);
          
          // Validar que min y max sean válidos
          if (isNaN(minVal) || isNaN(maxVal) || !isFinite(minVal) || !isFinite(maxVal)) {
            scales[dim] = d3.scaleLinear().domain([0, 1]).range([chartHeight, 0]);
          } else {
            // Si min === max, agregar un pequeño margen
            if (minVal === maxVal) {
              scales[dim] = d3.scaleLinear()
                .domain([minVal - 1, maxVal + 1])
                .range([chartHeight, 0]);
            } else {
              scales[dim] = d3.scaleLinear()
                .domain([minVal, maxVal])
                .range([chartHeight, 0])
                .nice();
            }
          }
        }
        
        // Posición inicial del eje (distribuidos uniformemente)
        axisPositions.push({
          name: dim,
          x: dimensions.length > 1 ? (chartWidth / (dimensions.length - 1)) * i : chartWidth / 2,
          index: i,
          originalIndex: i  // Guardar índice original para referencia
        });
      } catch (err) {
        console.error('Parallel Coordinates: Error calculando escala para dimensión', dim, err);
        // Usar escala por defecto en caso de error
        scales[dim] = d3.scaleLinear().domain([0, 1]).range([chartHeight, 0]);
        axisPositions.push({
          name: dim,
          x: dimensions.length > 1 ? (chartWidth / (dimensions.length - 1)) * i : chartWidth / 2,
          index: i,
          originalIndex: i  // Guardar índice original para referencia
        });
      }
    });
    
    // Crear tooltip una sola vez (fuera de drawDataLines)
    const tooltip = d3.select(container).append('div')
        .attr('class', 'parallel-coords-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)');
    
    // Flag para evitar redibujados múltiples simultáneos
    let isRedrawing = false;
    
    // Estado de selección de líneas (compartido entre redibujados)
    let selectedLineIndices = new Set();
    
    // Función para dibujar líneas de datos
    function drawDataLines() {
      if (isRedrawing) return; // Evitar redibujados múltiples
      isRedrawing = true;
      
      try {
        // Guardar selección actual antes de limpiar
        const savedSelection = new Set(selectedLineIndices);
        
        // Limpiar líneas anteriores
        g.selectAll('.pcline').remove();
        
        // Obtener categorías para colorear
        const categoryCol = spec.category_col || null;
        const categories = categoryCol ? [...new Set(validData.map(d => d[categoryCol]).filter(c => c != null && c !== ''))] : [];
        const color = categories.length > 0 
          ? d3.scaleOrdinal(d3.schemeCategory10).domain(categories)
          : () => '#4a90e2';
        
        // Ordenar axisPositions por x para asegurar orden correcto al dibujar
        const sortedAxisPositions = [...axisPositions].sort((a, b) => a.x - b.x);
        
        // Función para generar puntos ordenados según posición X de los ejes (líneas rectas)
        function generateSortedLinePoints(d) {
          const points = [];
          // Ordenar dimensiones según posición X de sus ejes
          const sortedDims = sortedAxisPositions.map(axis => {
            return { dim: axis.name, axis: axis, scale: scales[axis.name] };
          });
          
          for (const { dim, axis, scale } of sortedDims) {
            if (!axis || !scale) continue;
            
            try {
              const val = d[dim];
              let y;
              
              if (val == null || isNaN(val) || !isFinite(val)) {
                y = chartHeight / 2;
              } else {
                y = scale(parseFloat(val));
                if (isNaN(y) || !isFinite(y)) {
                  y = chartHeight / 2;
                }
              }
              
              points.push([axis.x, y]);
            } catch (err) {
              points.push([axis.x, chartHeight / 2]);
            }
          }
          return points;
        }
        
        // Dibujar líneas RECTAS (sin curvas)
        const lineGenerator = d3.line()
          .x(d => d[0])
          .y(d => d[1])
          .curve(d3.curveLinear)  // Líneas rectas, no curvas
          .defined(d => d != null && !isNaN(d[0]) && !isNaN(d[1]) && isFinite(d[0]) && isFinite(d[1]));
        
        // Restaurar selección guardada
        selectedLineIndices = savedSelection;
        
        // Función para actualizar visualización de líneas según selección
        function updateLineVisualization() {
          g.selectAll('.pcline').each(function(d, i) {
            const line = d3.select(this);
            const isSelected = selectedLineIndices.has(i);
            const baseStrokeWidth = 1.5;
            const baseOpacity = 0.6;
            
            if (isSelected) {
              // Línea seleccionada: más gruesa, opacidad completa, color destacado
              line
                .attr('stroke-width', 4)
                .attr('opacity', 1)
                .attr('stroke', '#ff6b35'); // Color naranja para selección
            } else {
              // Línea no seleccionada: color normal según categoría
              const lineColor = (() => {
                try {
                  if (categoryCol && d[categoryCol] && categories.includes(d[categoryCol])) {
                    return color(d[categoryCol]);
                  }
                  return '#4a90e2';
                } catch (err) {
                  return '#4a90e2';
                }
              })();
              
              line
                .attr('stroke-width', baseStrokeWidth)
                .attr('opacity', baseOpacity)
                .attr('stroke', lineColor);
            }
          });
        }
        
        g.selectAll('.pcline')
          .data(validData)
          .enter()
          .append('path')
          .attr('class', 'pcline')
          .attr('data-index', (d, i) => i)  // Guardar índice para selección
          .attr('d', d => {
            try {
              const points = generateSortedLinePoints(d);
              if (points.length < 2) {
                return ''; // No dibujar si no hay suficientes puntos
              }
              return lineGenerator(points);
            } catch (err) {
              console.error('Parallel Coordinates: Error generando línea', err, d);
              return '';
            }
          })
          .attr('fill', 'none')
          .attr('stroke', d => {
            try {
              if (categoryCol && d[categoryCol] && categories.includes(d[categoryCol])) {
                return color(d[categoryCol]);
              }
              return '#4a90e2';
            } catch (err) {
              return '#4a90e2';
            }
          })
          .attr('stroke-width', 1.5)
          .attr('opacity', 0.6)
          .style('cursor', 'pointer')
          .style('pointer-events', 'stroke')  // Solo detectar eventos en el trazo, no en el área
          .on('mouseenter', function(event, d) {
            event.stopPropagation();
            const line = d3.select(this);
            const index = parseInt(line.attr('data-index'));
            
            // Solo resaltar si no está seleccionada
            if (!selectedLineIndices.has(index)) {
              line
                .attr('stroke-width', 3)
                .attr('opacity', 1);
            }
            
            // Mostrar tooltip con información de la línea
            const mouseX = event.pageX || event.clientX || 0;
            const mouseY = event.pageY || event.clientY || 0;
            
            let tooltipContent = '<strong>Datos:</strong><br/>';
            dimensions.forEach(dim => {
              try {
                const val = d[dim];
                if (val != null && !isNaN(val) && isFinite(val)) {
                  tooltipContent += `${dim}: ${parseFloat(val).toFixed(2)}<br/>`;
                }
              } catch (err) {
                // Ignorar errores al mostrar valores
              }
            });
            if (categoryCol && d[categoryCol]) {
              tooltipContent += `<br/><strong>Categoría:</strong> ${d[categoryCol]}`;
            }
            
            tooltip
              .style('left', (mouseX + 10) + 'px')
              .style('top', (mouseY - 10) + 'px')
              .style('display', 'block')
              .html(tooltipContent)
              .transition()
              .duration(200)
              .style('opacity', 1);
          })
          .on('mousemove', function(event) {
            event.stopPropagation();
            const mouseX = event.pageX || event.clientX || 0;
            const mouseY = event.pageY || event.clientY || 0;
            tooltip
              .style('left', (mouseX + 10) + 'px')
              .style('top', (mouseY - 10) + 'px');
          })
          .on('mouseleave', function(event) {
            event.stopPropagation();
            const line = d3.select(this);
            const index = parseInt(line.attr('data-index'));
            
            // Solo restaurar si no está seleccionada
            if (!selectedLineIndices.has(index)) {
              line
                .attr('stroke-width', 1.5)
                .attr('opacity', 0.6);
            }
            
            tooltip
              .transition()
              .duration(200)
              .style('opacity', 0)
              .on('end', function() {
                tooltip.style('display', 'none');
              });
          })
          .on('click', function(event, d) {
            event.stopPropagation();
            const line = d3.select(this);
            const index = parseInt(line.attr('data-index'));
            
            // Toggle selección: si está seleccionada, deseleccionar; si no, seleccionar
            if (selectedLineIndices.has(index)) {
              selectedLineIndices.delete(index);
            } else {
              // Si se presiona Ctrl/Cmd, agregar a selección; si no, reemplazar
              const ctrlKey = event.ctrlKey || event.metaKey;
              if (!ctrlKey) {
                selectedLineIndices.clear();
              }
              selectedLineIndices.add(index);
            }
            
            // Actualizar visualización
            updateLineVisualization();
            
            // 🔒 CORRECCIÓN: Enviar evento de selección con identificador de vista
            const selected = Array.from(selectedLineIndices).map(i => {
              const item = {
                ...validData[i],
                index: i
              };
              // Preservar _original_row si existe
              if (validData[i]._original_row) {
                item._original_row = validData[i]._original_row;
              }
              return item;
            });
            
            // 🔒 Obtener letra de la vista desde el spec o el contenedor
            let viewLetter = spec.__view_letter__ || null;
            if (!viewLetter && container) {
              const letterAttr = container.getAttribute('data-letter');
              if (letterAttr) {
                viewLetter = letterAttr;
              }
            }
            
            sendEvent(divId, 'select', {
              type: 'select',
              items: selected,
              count: selected.length,
              __view_letter__: viewLetter,  // 🔒 Incluir identificador de vista
              __is_primary_view__: spec.__is_primary_view__ || false
            });
          });
        
        // Inicializar visualización
        updateLineVisualization();
      } catch (err) {
        console.error('Parallel Coordinates: Error en drawDataLines', err);
      } finally {
        isRedrawing = false;
      }
    }
    
    // Calcular posiciones uniformes fijas (no cambian, solo se intercambian)
    const uniformPositions = [];
    for (let i = 0; i < dimensions.length; i++) {
      uniformPositions.push(dimensions.length > 1 ? (chartWidth / (dimensions.length - 1)) * i : chartWidth / 2);
    }
    
    // Asignar posiciones uniformes a cada eje según su índice
    axisPositions.forEach((ax, idx) => {
      ax.x = uniformPositions[idx];
      ax.targetX = uniformPositions[idx];  // Posición objetivo (uniforme)
    });
    
    // Función para actualizar posiciones visuales de todos los ejes
    function updateAxisPositions() {
      axisPositions.forEach((ax) => {
        const axisGroup = g.select(`[data-dimension="${ax.name}"]`);
        if (!axisGroup.empty()) {
          axisGroup.attr('transform', `translate(${ax.x}, 0)`);
        }
      });
    }
    
    // Dibujar ejes (arrastrables para intercambiar posiciones)
    // Usar nombre de dimensión como identificador único (más estable que índice)
    const axisGroups = g.selectAll('.axis-group')
      .data(axisPositions)
      .enter()
      .append('g')
      .attr('class', d => `axis-group axis-group-${d.name.replace(/[^a-zA-Z0-9]/g, '_')}`)
      .attr('data-dimension', d => d.name)  // Guardar nombre de dimensión como atributo
      .attr('transform', d => `translate(${d.x}, 0)`)
      .style('cursor', 'move')
      .style('pointer-events', 'all');
    
    // Agregar área invisible más grande para facilitar el drag
    axisGroups.append('rect')
      .attr('class', 'axis-drag-area')
      .attr('x', -30)  // Área de arrastre más ancha (60px total)
      .attr('y', -10)
      .attr('width', 60)
      .attr('height', chartHeight + 20)
      .attr('fill', 'transparent')
      .style('cursor', 'move')
      .style('pointer-events', 'all');
    
    // Variable para rastrear qué eje se está arrastrando y con cuál se puede intercambiar
    let draggingAxis = null;
    let swapCandidate = null;
    
    // Aplicar drag a los grupos de ejes (sistema de intercambio)
    axisGroups.call(d3.drag()
        .on('start', function(event, d) {
          event.sourceEvent.stopPropagation();
          try {
            draggingAxis = d;
            swapCandidate = null;
            
            // Resaltar el eje que se está arrastrando
            d3.select(this).select('.axis-line').attr('stroke', '#ff6b35').attr('stroke-width', 3);
            // Elevar el eje que se está arrastrando
            d3.select(this).raise();
            
            // Guardar posición original
            d.originalX = d.x;
          } catch (err) {
            console.error('Parallel Coordinates: Error en start drag', err);
          }
        })
        .on('drag', function(event, d) {
          event.sourceEvent.stopPropagation();
          
          try {
            const [mx] = d3.pointer(event, g.node());
            
            // Validar coordenadas del mouse
            if (isNaN(mx) || !isFinite(mx)) {
              return;
            }
            
            // Limitar movimiento horizontal dentro del área
            const padding = 20;
            let dragX = Math.max(padding, Math.min(chartWidth - padding, mx));
            
            // Buscar la posición uniforme más cercana al mouse
            let closestPosition = uniformPositions[0];
            let closestIndex = 0;
            let minDistance = Math.abs(dragX - uniformPositions[0]);
            
            for (let i = 1; i < uniformPositions.length; i++) {
              const distance = Math.abs(dragX - uniformPositions[i]);
              if (distance < minDistance) {
                minDistance = distance;
                closestPosition = uniformPositions[i];
                closestIndex = i;
              }
            }
            
            // Buscar qué eje está actualmente en la posición más cercana (candidato para intercambio)
            const threshold = 80; // Distancia máxima para considerar intercambio (más generoso)
            const newCandidate = axisPositions.find(ax => 
              ax !== d && Math.abs(ax.x - closestPosition) < 10
            );
            
            // Si hay un candidato válido y está cerca
            if (newCandidate && minDistance < threshold) {
              // Si es un candidato diferente, actualizar
              if (newCandidate !== swapCandidate) {
                // Restaurar visualización anterior si había otro candidato
                if (swapCandidate) {
                  const prevCandidateGroup = g.select(`[data-dimension="${swapCandidate.name}"]`);
                  if (!prevCandidateGroup.empty()) {
                    prevCandidateGroup.select('.axis-line')
                      .attr('stroke', '#333')
                      .attr('stroke-width', 2);
                  }
                }
                
                // Actualizar candidato
                swapCandidate = newCandidate;
                
                // Resaltar el nuevo candidato
                const candidateGroup = g.select(`[data-dimension="${swapCandidate.name}"]`);
                if (!candidateGroup.empty()) {
                  candidateGroup.select('.axis-line')
                    .attr('stroke', '#4a90e2')  // Azul para indicar que se puede intercambiar
                    .attr('stroke-width', 3);   // Más grueso para indicar intercambio
                }
              }
            } else {
              // No hay candidato cercano válido
              if (swapCandidate) {
                // Restaurar visualización del candidato anterior
                const prevCandidateGroup = g.select(`[data-dimension="${swapCandidate.name}"]`);
                if (!prevCandidateGroup.empty()) {
                  prevCandidateGroup.select('.axis-line')
                    .attr('stroke', '#333')
                    .attr('stroke-width', 2);
                }
                swapCandidate = null;
              }
            }
            
            // Mover visualmente el eje que se está arrastrando a la posición del mouse
            d3.select(this).attr('transform', `translate(${dragX}, 0)`);
          } catch (err) {
            console.error('Parallel Coordinates: Error en drag', err);
          }
        })
        .on('end', function(event, d) {
          event.sourceEvent.stopPropagation();
          
          try {
            // Restaurar visualización de todos los ejes (color normal)
            g.selectAll('.axis-group').select('.axis-line')
              .attr('stroke', '#333')
              .attr('stroke-width', 2);
            
            if (swapCandidate && swapCandidate !== d) {
              // Intercambiar posiciones X de los ejes (intercambiar las posiciones uniformes)
              const tempX = d.x;
              const tempTargetX = d.targetX;
              
              d.x = swapCandidate.x;
              d.targetX = swapCandidate.targetX;
              
              swapCandidate.x = tempX;
              swapCandidate.targetX = tempTargetX;
              
              // Actualizar posiciones visuales de ambos ejes con transición suave
              const draggedGroup = g.select(`[data-dimension="${d.name}"]`);
              const swappedGroup = g.select(`[data-dimension="${swapCandidate.name}"]`);
              
              if (!draggedGroup.empty()) {
                draggedGroup
                  .transition()
                  .duration(300)
                  .ease(d3.easeCubicOut)
                  .attr('transform', `translate(${d.x}, 0)`);
              }
              
              if (!swappedGroup.empty()) {
                swappedGroup
                  .transition()
                  .duration(300)
                  .ease(d3.easeCubicOut)
                  .attr('transform', `translate(${swapCandidate.x}, 0)`);
              }
              
              // Redibujar líneas después de la transición para reflejar el nuevo orden
        setTimeout(() => {
                if (!isRedrawing) {
                  drawDataLines();
                }
              }, 320);
            } else {
              // No hay intercambio, restaurar posición original del eje arrastrado
              if (d.originalX !== undefined) {
                d3.select(this)
                  .transition()
                  .duration(200)
                  .ease(d3.easeCubicOut)
                  .attr('transform', `translate(${d.originalX}, 0)`);
                // Restaurar también la posición X en el objeto
                d.x = d.originalX;
              }
            }
            
            // Limpiar referencias
            draggingAxis = null;
            swapCandidate = null;
            delete d.originalX;
          } catch (err) {
            console.error('Parallel Coordinates: Error en end drag', err);
            // En caso de error, restaurar posición original
            if (draggingAxis && draggingAxis.originalX !== undefined) {
              const axisGroup = g.select(`[data-dimension="${draggingAxis.name}"]`);
              if (!axisGroup.empty()) {
                axisGroup
                  .transition()
                  .duration(200)
                  .attr('transform', `translate(${draggingAxis.originalX}, 0)`);
                draggingAxis.x = draggingAxis.originalX;
              }
            }
            // Restaurar visualización de todos los ejes
            g.selectAll('.axis-group').select('.axis-line')
              .attr('stroke', '#333')
              .attr('stroke-width', 2);
            draggingAxis = null;
            swapCandidate = null;
          }
        })
      );
    
    // Línea del eje
    axisGroups.append('line')
      .attr('class', 'axis-line')
      .attr('x1', 0)
      .attr('x2', 0)
      .attr('y1', 0)
      .attr('y2', chartHeight)
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .style('cursor', 'move')
      .style('pointer-events', 'all');
    
    // Etiquetas y ticks del eje
    axisGroups.each(function(d) {
      try {
        const axisG = d3.select(this);
        const dim = d.name;
        const scale = scales[dim];
        
        if (!scale) {
          console.warn('Parallel Coordinates: No hay escala para dimensión', dim);
          return;
        }
        
        // Ticks del eje Y (vertical) con números visibles
        const axis = d3.axisLeft(scale)
          .ticks(5)
          .tickFormat(d3.format('.2f'));
        
        const axisTicks = axisG.append('g')
          .attr('class', 'axis-ticks');
        
        try {
          axisTicks.call(axis);
        } catch (err) {
          console.error('Parallel Coordinates: Error dibujando ticks para', dim, err);
        }
        
        // Asegurar que los números sean visibles
        axisTicks.selectAll('text')
          .style('font-size', '10px')
          .style('fill', '#333')
          .style('font-weight', 'normal')
          .style('pointer-events', 'none');
        
        axisTicks.selectAll('line, path')
          .style('stroke', '#666')
          .style('stroke-width', 1)
          .style('pointer-events', 'none');
        
        // Etiqueta del eje
        axisG.append('text')
          .attr('class', 'axis-label')
          .attr('x', 0)
          .attr('y', -10)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .style('font-size', '12px')
          .style('font-weight', 'bold')
          .style('fill', '#333')
          .style('pointer-events', 'none')
          .text(dim);
      } catch (err) {
        console.error('Parallel Coordinates: Error dibujando eje', d.name, err);
      }
    });
    
    // Dibujar líneas de datos iniciales
    drawDataLines();
    
    // Si el spec tiene interactive=true, agregar brush selection en el área del gráfico
    if (spec.interactive) {
      // Crear brush para selección rectangular (puede seleccionar líneas que pasan por un rango)
      // Nota: Para Parallel Coordinates, la selección es más compleja porque las líneas cruzan múltiples ejes
      // Por ahora, permitimos selección rectangular que selecciona líneas que pasan por esa área
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer')
        .style('pointer-events', 'all');
      
      const brush = d3.brush()
        .extent([[0, 0], [chartWidth, chartHeight]])
        .on('start', function(event) {
          // Durante el brush, desactivar eventos de líneas temporalmente
          g.selectAll('.pcline')
            .style('pointer-events', 'none');
        })
        .on('brush', function(event) {
          if (!event.selection) {
            // Si no hay selección, mostrar todas las líneas normalmente
            g.selectAll('.pcline')
              .attr('opacity', 0.6)
              .attr('stroke-width', 1.5);
            return;
          }
          
          // Obtener selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Resaltar líneas que pasan por la selección durante el brush
          g.selectAll('.pcline').each(function(d) {
            try {
              // Verificar si algún punto de la línea está dentro de la selección
              let isInBrush = false;
              for (let j = 0; j < dimensions.length; j++) {
                try {
                  const dim = dimensions[j];
                  const axis = axisPositions[j];
                  const scale = scales[dim];
                  
                  if (!axis || !scale) continue;
                  
                  const val = d[dim];
                  if (val == null || isNaN(val) || !isFinite(val)) continue;
                  
                  const y = scale(parseFloat(val));
                  if (isNaN(y) || !isFinite(y)) continue;
                  
                  // Verificar si el punto está dentro de la selección
                  if (axis.x >= Math.min(x0, x1) && axis.x <= Math.max(x0, x1) &&
                      y >= Math.min(y0, y1) && y <= Math.max(y0, y1)) {
                    isInBrush = true;
                    break;
                  }
                } catch (err) {
                  // Ignorar errores en puntos individuales
                  continue;
                }
              }
              
              const line = d3.select(this);
              if (isInBrush) {
                // Resaltar líneas dentro del brush
                line
                  .attr('stroke-width', 3)
                  .attr('opacity', 1);
              } else {
                // Atenuar líneas fuera del brush
                line
                  .attr('stroke-width', 1.5)
                  .attr('opacity', 0.15);
              }
            } catch (err) {
              // Ignorar errores
            }
          });
        })
        .on('end', function(event) {
          // Restaurar eventos de líneas
          g.selectAll('.pcline')
            .style('pointer-events', 'all');
          
          if (!event.selection) {
            // Si no hay selección, restaurar visualización y enviar todos los datos
            g.selectAll('.pcline')
              .attr('opacity', 0.6)
              .attr('stroke-width', 1.5);
            
            const allItems = validData.map((d, i) => {
              const item = {
                ...d,
                index: i
              };
              // Preservar _original_row si existe
              if (d._original_row) {
                item._original_row = d._original_row;
              }
              return item;
            });
            sendEvent(divId, 'select', {
              type: 'select',
              items: allItems,
              count: allItems.length
            });
            return;
          }
          
          // Obtener selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Filtrar líneas que pasan por la selección
          // Una línea se considera seleccionada si al menos un punto está dentro de la selección
          const selected = validData.filter((d, i) => {
            try {
              // Generar puntos de la línea y verificar si alguno está en la selección
              for (let j = 0; j < dimensions.length; j++) {
                try {
                  const dim = dimensions[j];
                  const axis = axisPositions[j];
                  const scale = scales[dim];
                  
                  if (!axis || !scale) continue;
                  
                  const val = d[dim];
                  if (val == null || isNaN(val) || !isFinite(val)) continue;
                  
                  const y = scale(parseFloat(val));
                  if (isNaN(y) || !isFinite(y)) continue;
                  
                  // Verificar si el punto está dentro de la selección
                  if (axis.x >= Math.min(x0, x1) && axis.x <= Math.max(x0, x1) &&
                      y >= Math.min(y0, y1) && y <= Math.max(y0, y1)) {
                    return true; // Al menos un punto está dentro de la selección
                  }
                } catch (err) {
                  // Ignorar errores en puntos individuales
                  continue;
                }
              }
              return false;
            } catch (err) {
              console.warn('Parallel Coordinates: Error verificando selección para línea', d, err);
              return false;
            }
          }).map((d, i) => {
            // Agregar datos originales si están disponibles
            const item = {
              ...d,
              index: validData.indexOf(d)
            };
            // Preservar _original_row si existe
            if (d._original_row) {
              item._original_row = d._original_row;
            }
            return item;
          });
          
          // Restaurar visualización de líneas
          g.selectAll('.pcline')
            .attr('opacity', 0.6)
            .attr('stroke-width', 1.5);
          
          // Resaltar líneas seleccionadas
          const selectedIndices = new Set(selected.map(s => s.index));
          g.selectAll('.pcline').filter((d, i) => selectedIndices.has(i))
            .attr('stroke-width', 3)
            .attr('opacity', 1);
          
          // Enviar evento de selección
          sendEvent(divId, 'select', {
            type: 'select',
            items: selected,
            count: selected.length
          });
        });
      
      // Agregar brush al grupo (después de dibujar todo)
      brushGroup.call(brush);
      
      // Asegurar que el overlay del brush capture eventos
      brushGroup.selectAll('.overlay')
        .style('pointer-events', 'all')
        .style('cursor', 'crosshair');
    }
    
    // Renderizar etiquetas de ejes si están especificadas
    if (spec.xLabel || spec.yLabel) {
      try {
        renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
      } catch (err) {
        console.error('Parallel Coordinates: Error renderizando etiquetas de ejes', err);
      }
    }
  }
  
  /**
   * Boxplot con D3.js
   */
  function renderBoxplotD3(container, spec, d3, divId) {
    const styles = getUnifiedStyles();
    const data = spec.data || [];
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 15, bottom: 30, left: 35 }  // Márgenes reducidos para dashboards grandes
      : { top: 20, right: 20, bottom: 40, left: 50 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que las dimensiones respeten el contenedor
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Asegurar que no exceda el contenedor
    const maxAvailableWidth = container.clientWidth || width;
    const maxAvailableHeight = container.clientHeight || height;
    if (width > maxAvailableWidth) {
      width = maxAvailableWidth;
      chartWidth = Math.max(width - margin.left - margin.right, 200);
    }
    if (height > maxAvailableHeight) {
      height = maxAvailableHeight;
      chartHeight = Math.max(height - margin.top - margin.bottom, 150);
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
      .domain([d3.min(data, d => d.lower), d3.max(data, d => d.upper)])
      .nice()
      .range([chartHeight, 0]);
    
    // Crear tooltip para boxplot
    const tooltipId = `boxplot-tooltip-${divId}`;
    let tooltip = d3.select(`#${tooltipId}`);
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div')
        .attr('id', tooltipId)
        .attr('class', 'boxplot-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '10px 12px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
        .style('font-family', 'Arial, sans-serif');
    }
    
    const yLabel = spec.yLabel || 'Value';
    
    // Crear grupo para cada boxplot (para poder agregar eventos)
    const boxGroups = g.selectAll('.boxplot-group')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'boxplot-group')
      .style('cursor', 'pointer')
      .on('mouseenter', function(event, d) {
        // Mostrar tooltip con información detallada
        const mouseX = event.pageX || event.clientX || 0;
        const mouseY = event.pageY || event.clientY || 0;
        
        const iqr = d.q3 - d.q1;
        const minVal = d.min !== undefined ? d.min : d.lower;
        const maxVal = d.max !== undefined ? d.max : d.upper;
        
        tooltip
          .style('left', (mouseX + 10) + 'px')
          .style('top', (mouseY - 10) + 'px')
          .style('display', 'block')
          .html(`
            <strong>${d.category}</strong><br/>
            <strong>${yLabel}:</strong><br/>
            &nbsp;&nbsp;Mínimo: ${minVal.toFixed(2)}<br/>
            &nbsp;&nbsp;Q1 (25%): ${d.q1.toFixed(2)}<br/>
            &nbsp;&nbsp;Mediana: ${d.median.toFixed(2)}<br/>
            &nbsp;&nbsp;Q3 (75%): ${d.q3.toFixed(2)}<br/>
            &nbsp;&nbsp;Máximo: ${maxVal.toFixed(2)}<br/>
            &nbsp;&nbsp;IQR: ${iqr.toFixed(2)}
          `)
          .transition()
          .duration(200)
          .style('opacity', 1);
        
        // Resaltar boxplot
        d3.select(this).selectAll('rect, line')
          .attr('opacity', 0.7);
      })
      .on('mouseleave', function(event, d) {
        // Ocultar tooltip
        tooltip.transition()
          .duration(200)
          .style('opacity', 0)
          .on('end', function() {
            tooltip.style('display', 'none');
          });
        
        // Restaurar opacidad
        d3.select(this).selectAll('rect, line')
          .attr('opacity', 1);
      });
    
    // Dibujar boxplot para cada categoría dentro del grupo
    boxGroups.each(function(d) {
      const group = d3.select(this);
      const xPos = x(d.category);
      const boxWidth = x.bandwidth();
      const centerX = xPos + boxWidth / 2;
      
      // Bigotes (whiskers)
      group.append('line')
        .attr('x1', centerX)
        .attr('x2', centerX)
        .attr('y1', y(d.lower))
        .attr('y2', y(d.q1))
        .attr('stroke', '#000')
        .attr('stroke-width', 2);
      
      group.append('line')
        .attr('x1', centerX)
        .attr('x2', centerX)
        .attr('y1', y(d.q3))
        .attr('y2', y(d.upper))
        .attr('stroke', '#000')
        .attr('stroke-width', 2);
      
      // Caja (box)
      group.append('rect')
        .attr('x', xPos)
        .attr('y', y(d.q3))
        .attr('width', boxWidth)
        .attr('height', y(d.q1) - y(d.q3))
        .attr('fill', spec.color || styles.primaryColor)
        .attr('stroke', styles.textColor)
        .attr('stroke-width', styles.axisWidth)
        .attr('class', 'bestlib-box');
      
      // Mediana (median line)
      group.append('line')
        .attr('x1', xPos)
        .attr('x2', xPos + boxWidth)
        .attr('y1', y(d.median))
        .attr('y2', y(d.median))
        .attr('stroke', styles.selectionColor)
        .attr('stroke-width', styles.lineWidthThick)
        .attr('class', 'bestlib-median');
    });
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5));
      
      applyUnifiedAxisStyles(yAxis);
      
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
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 15, bottom: 30, left: 35 }  // Márgenes reducidos para dashboards grandes
      : { top: 20, right: 20, bottom: 40, left: 50 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, minChartWidth);
      }
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      const maxAvailableHeight = container.clientHeight || height;
      if (height > maxAvailableHeight) {
        height = maxAvailableHeight;
        chartHeight = Math.max(height - margin.top - margin.bottom, minChartHeight);
      }
    }
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('overflow', 'visible');  // Permitir que el contenido se muestre fuera del área del SVG
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3 - Usar scaleLinear para histograma (los bins son valores numéricos continuos)
    const binValues = data.map(d => d.bin).sort((a, b) => a - b);
    const minBin = binValues[0];
    const maxBin = binValues[binValues.length - 1];
    // Calcular el ancho de cada bin basado en la diferencia entre bins consecutivos
    // Si hay múltiples bins, usar la diferencia promedio; si no, calcular basado en el rango
    let binSpacing;
    if (binValues.length > 1) {
      // Calcular diferencias entre bins consecutivos y usar el promedio
      const diffs = [];
      for (let i = 1; i < binValues.length; i++) {
        diffs.push(binValues[i] - binValues[i-1]);
      }
      binSpacing = diffs.reduce((a, b) => a + b, 0) / diffs.length;
    } else {
      binSpacing = (maxBin - minBin) / Math.max(data.length, 1) || 1;
    }
    
    const x = d3.scaleLinear()
      .domain([minBin - binSpacing / 2, maxBin + binSpacing / 2])
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.count) || 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Calcular el ancho de cada barra en píxeles
    // Usar el 90% del espaciado para dejar un pequeño gap entre barras
    const barWidthPixels = x(minBin + binSpacing) - x(minBin);
    const barWidth = Math.max(barWidthPixels * 0.9, 1); // 90% del ancho para dejar espacio
    
    // Crear tooltip para histograma
    const tooltipId = `histogram-tooltip-${divId}`;
    let tooltip = d3.select(`#${tooltipId}`);
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div')
        .attr('id', tooltipId)
        .attr('class', 'histogram-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '10px 12px')
        .style('border-radius', '6px')
      .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
        .style('font-family', 'Arial, sans-serif');
    }
    
    const xLabel = spec.xLabel || 'Bin';
    const yLabel = spec.yLabel || 'Frequency';
    
    // Barras del histograma
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.bin) - barWidth / 2)
      .attr('y', chartHeight)
      .attr('width', barWidth)
      .attr('height', 0)
      .attr('fill', spec.color || '#4a90e2')
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (spec.interactive) {
          // Obtener letra de la vista (para vistas principales)
          let viewLetter = spec.__view_letter__ || null;
          if (!viewLetter && container) {
            const letterAttr = container.getAttribute('data-letter');
            if (letterAttr) {
              viewLetter = letterAttr;
            }
          }
          
          // IMPORTANTE: Enviar todas las filas originales que corresponden a este bin
          // El bin tiene _original_rows que contiene todas las filas del DataFrame que caen en este bin
          const originalRows = d._original_rows || d._original_row || (d._original_row ? [d._original_row] : null) || [];
          
          // Asegurar que originalRows sea un array
          const items = Array.isArray(originalRows) && originalRows.length > 0 ? originalRows : [];
          
          // Si no hay filas originales, intentar enviar al menos información del bin
          // (esto puede pasar si los datos no se prepararon correctamente)
          if (items.length === 0) {
            console.warn(`[Histogram] No se encontraron filas originales para el bin ${d.bin}. Asegúrese de que los datos se prepararon correctamente.`);
            // Enviar información del bin como fallback
            items.push({ bin: d.bin, count: d.count });
          }
          
          sendEvent(divId, 'select', {
            type: 'select',
            items: items,  // Enviar todas las filas originales de este bin
            indices: [],
            original_items: [d],
            _original_rows: items,  // También incluir como _original_rows para compatibilidad
            __view_letter__: viewLetter,
            __is_primary_view__: spec.__is_primary_view__ || false
          });
        }
      })
      .on('mouseenter', function(event, d) {
        // Resaltar barra
        d3.select(this)
          .attr('opacity', 0.8);
        
        // Mostrar tooltip
        const mouseX = event.pageX || event.clientX || 0;
        const mouseY = event.pageY || event.clientY || 0;
        
        const binValue = typeof d.bin === 'number' ? d.bin.toFixed(2) : d.bin;
        tooltip
          .style('left', (mouseX + 10) + 'px')
          .style('top', (mouseY - 10) + 'px')
          .style('display', 'block')
          .html(`<strong>${xLabel}:</strong> ${binValue}<br/><strong>${yLabel}:</strong> ${d.count}`)
          .transition()
          .duration(200)
          .style('opacity', 1);
      })
      .on('mouseleave', function(event, d) {
        // Restaurar opacidad
        d3.select(this)
          .attr('opacity', 1);
        
        // Ocultar tooltip
        tooltip.transition()
          .duration(200)
          .style('opacity', 0)
          .on('end', function() {
            tooltip.style('display', 'none');
          });
      })
      .transition()
      .duration(800)
      .attr('y', d => y(d.count))
      .attr('height', d => chartHeight - y(d.count));

    // 🔒 CORRECCIÓN: Ejes - Asegurar que se muestren correctamente con valores visibles
    if (spec.axes !== false) {
      // Detectar si necesitamos rotar etiquetas del eje X
      const numBins = data.length;
      const maxBinLabelLength = Math.max(...data.map(d => String(d.bin).length), 0);
      const needsRotation = spec._autoRotateXTicks || numBins > 8 || maxBinLabelLength > 8;
      const rotationAngle = needsRotation ? -45 : 0;
      
      // 🔒 CORRECCIÓN: Eje X - Asegurar que se muestre con valores y formato correcto
      const xAxis = g.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${chartHeight})`);
      
      // Calcular número de ticks apropiado (máximo 10 para no saturar)
      const numXTicks = Math.min(numBins, 10);
      const xAxisGenerator = d3.axisBottom(x)
        .ticks(numXTicks)
        .tickFormat(d => {
          // Formato más corto para números largos
          if (typeof d === 'number') {
            if (d % 1 === 0) return d.toString();
            return d.toFixed(maxBinLabelLength > 6 ? 1 : 2);
          }
          return String(d);
        });
      
      xAxis.call(xAxisGenerator);
      
      // Estilizar etiquetas del eje X
      xAxis.selectAll('text')
        .style('font-size', needsRotation ? '10px' : '11px')
        .style('font-weight', '600')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif')
        .attr('transform', rotationAngle !== 0 ? `rotate(${rotationAngle})` : null)
        .style('text-anchor', rotationAngle !== 0 ? 'end' : 'middle')
        .attr('dx', rotationAngle !== 0 ? '-0.5em' : '0')
        .attr('dy', rotationAngle !== 0 ? '0.5em' : '0.7em')
        .style('opacity', 1);  // Asegurar que sean visibles
      
      applyUnifiedAxisStyles(xAxis);
      
      // 🔒 CORRECCIÓN: Eje Y - Asegurar que se muestre con valores y formato correcto
      const yAxis = g.append('g')
        .attr('class', 'y-axis');
      
      const yAxisGenerator = d3.axisLeft(y)
        .ticks(5)
        .tickFormat(d3.format('d'));  // Formato numérico para el eje Y
      
      yAxis.call(yAxisGenerator);
      
      applyUnifiedAxisStyles(yAxis);
      
      // Renderizar etiquetas de ejes usando función helper
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
    
    // CRÍTICO: Renderizar título del gráfico si está especificado
    if (spec.title) {
      const titleFontSize = spec.titleFontSize || 16;
      const titleY = margin.top - 10;
      const titleX = chartWidth / 2;
      
      svg.append('text')
        .attr('x', titleX + margin.left)
        .attr('y', titleY)
        .attr('text-anchor', 'middle')
        .style('font-size', `${titleFontSize}px`)
        .style('font-weight', '700')
        .style('fill', '#000000')
        .style('font-family', 'Arial, sans-serif')
        .text(spec.title);
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
    
    // 🔒 OPTIMIZACIÓN: Reducir márgenes para dashboards grandes
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 15, bottom: 30, left: 35 }  // Márgenes reducidos para dashboards grandes
      : { top: 20, right: 20, bottom: 40, left: 50 }; // Márgenes normales
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200;
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // Asegurar que no exceda el contenedor
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, minChartWidth);
      }
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200;
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    } else {
      // Asegurar que no exceda el contenedor
      const maxAvailableHeight = container.clientHeight || height;
      if (height > maxAvailableHeight) {
        height = maxAvailableHeight;
        chartHeight = Math.max(height - margin.top - margin.bottom, minChartHeight);
      }
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

    // Crear tooltip para grouped bar chart
    const tooltipId = `grouped-bar-tooltip-${divId}`;
    let tooltip = d3.select(`#${tooltipId}`);
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div')
        .attr('id', tooltipId)
        .attr('class', 'grouped-bar-chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '10px 12px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
        .style('font-family', 'Arial, sans-serif');
    }
    
    const xLabel = spec.xLabel || 'Group';
    const yLabel = spec.yLabel || 'Value';
    
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
        
        // Obtener letra de la vista (para vistas principales)
        let viewLetter = spec.__view_letter__ || null;
        if (!viewLetter && container) {
          const letterAttr = container.getAttribute('data-letter');
          if (letterAttr) {
            viewLetter = letterAttr;
          }
        }
        
          sendEvent(divId, 'select', { 
          type: 'select',
          items: [{ group: d.group, series: d.series }],
            indices: [], 
          original_items: [d],
          __view_letter__: viewLetter,
          __is_primary_view__: spec.__is_primary_view__ || false
        });
      })
      .on('mouseenter', function(event, d) {
        // Resaltar barra
        d3.select(this)
          .attr('opacity', 0.9);
        
        // Mostrar tooltip
        const mouseX = event.pageX || event.clientX || 0;
        const mouseY = event.pageY || event.clientY || 0;
        
        const value = typeof d.value === 'number' ? d.value.toFixed(2) : d.value;
        tooltip
          .style('left', (mouseX + 10) + 'px')
          .style('top', (mouseY - 10) + 'px')
          .style('display', 'block')
          .html(`<strong>${xLabel}:</strong> ${d.group}<br/><strong>Series:</strong> ${d.series}<br/><strong>${yLabel}:</strong> ${value}`)
          .transition()
          .duration(200)
          .style('opacity', 1);
      })
      .on('mouseleave', function(event, d) {
        // Restaurar opacidad
        d3.select(this)
          .attr('opacity', 1);
        
        // Ocultar tooltip
        tooltip.transition()
          .duration(200)
          .style('opacity', 0)
          .on('end', function() {
            tooltip.style('display', 'none');
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
    // Crear tooltip para bar chart
    const tooltipId = `bar-tooltip-${divId}`;
    let tooltip = d3.select(`#${tooltipId}`);
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div')
        .attr('id', tooltipId)
        .attr('class', 'bar-chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.85)')
        .style('color', '#fff')
        .style('padding', '10px 12px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('z-index', 10000)
        .style('display', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
        .style('font-family', 'Arial, sans-serif');
    }
    
    const xLabel = spec.xLabel || 'Category';
    const yLabel = spec.yLabel || 'Value';
    
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.category))
      .attr('y', chartHeight)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', d => d.color || spec.color || '#4a90e2')
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (spec.interactive) {
          const index = data.indexOf(d);
          
          // Obtener todas las filas originales de esta categoría
          // El bar chart tiene _original_rows (plural) que contiene todas las filas de esa categoría
          const originalRows = d._original_rows || d._original_row || (d._original_row ? [d._original_row] : null) || [d];
          
          // Asegurar que originalRows sea un array
          const items = Array.isArray(originalRows) ? originalRows : [originalRows];
          
          // Obtener letra de la vista (para vistas principales)
          let viewLetter = spec.__view_letter__ || null;
          if (!viewLetter && container) {
            const letterAttr = container.getAttribute('data-letter');
            if (letterAttr) {
              viewLetter = letterAttr;
            } else {
              // Intentar extraer del ID del contenedor
              const idMatch = container.id && container.id.match(/-cell-([A-Z])-/);
              if (idMatch) {
                viewLetter = idMatch[1];
            }
          }
          }

        sendEvent(divId, 'select', { 
            type: 'select',
            items: items,  // Enviar todas las filas originales de esta categoría
            indices: [index],
            original_items: [d],
            _original_rows: items,  // También incluir como _original_rows para compatibilidad
            __view_letter__: viewLetter,
            __is_primary_view__: spec.__is_primary_view__ || false
          });
        }
      })
      .on('mouseenter', function(event, d) {
        // Resaltar barra
        d3.select(this)
          .attr('fill', d => d.color || spec.hoverColor || '#357abd')
          .attr('opacity', 0.9);
        
        // Mostrar tooltip
        const mouseX = event.pageX || event.clientX || 0;
        const mouseY = event.pageY || event.clientY || 0;
        
        const value = typeof d.value === 'number' ? d.value.toFixed(2) : d.value;
        tooltip
          .style('left', (mouseX + 10) + 'px')
          .style('top', (mouseY - 10) + 'px')
          .style('display', 'block')
          .html(`<strong>${xLabel}:</strong> ${d.category}<br/><strong>${yLabel}:</strong> ${value}`)
          .transition()
          .duration(200)
          .style('opacity', 1);
      })
      .on('mouseleave', function(event, d) {
        // Restaurar color
        d3.select(this)
          .attr('fill', d => d.color || spec.color || '#4a90e2')
          .attr('opacity', 1);
        
        // Ocultar tooltip
        tooltip.transition()
          .duration(200)
          .style('opacity', 0)
          .on('end', function() {
            tooltip.style('display', 'none');
          });
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
    let data = spec.data || [];
    
    // OPTIMIZACIÓN: Sampling automático para datasets grandes (>2000 puntos)
    // Si no se especifica maxPoints y hay más de 2000 puntos, aplicar sampling automático
    const maxPoints = spec.maxPoints;
    const AUTO_SAMPLE_THRESHOLD = 2000;
    const AUTO_SAMPLE_SIZE = 2000;
    
    if (!maxPoints && data.length > AUTO_SAMPLE_THRESHOLD) {
      // Sampling uniforme para mantener distribución
      const step = Math.ceil(data.length / AUTO_SAMPLE_SIZE);
      data = data.filter((d, i) => i % step === 0);
      console.log(`[BESTLIB] Aplicado sampling automático: ${spec.data.length} → ${data.length} puntos`);
    } else if (maxPoints && data.length > maxPoints) {
      // Sampling según maxPoints especificado
      const step = Math.ceil(data.length / maxPoints);
      data = data.filter((d, i) => i % step === 0);
    }
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    // 🔒 CORRECCIÓN: Márgenes equilibrados para centrado visual del scatter plot
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    // Ajustar márgenes para centrado visual: equilibrar izquierda/derecha y arriba/abajo
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }  // Márgenes equilibrados para dashboards grandes
      : { top: 25, right: 25, bottom: 45, left: 55 }; // Márgenes equilibrados normales (más espacio izquierdo para eje Y)
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    // 🔒 Asegurar que los márgenes estén equilibrados para centrado visual
    // Balancear márgenes horizontales y verticales
    const horizontalBalance = Math.abs(margin.left - margin.right);
    const verticalBalance = Math.abs(margin.top - margin.bottom);
    // Si hay desbalance significativo (>10px), ajustar para equilibrar
    if (horizontalBalance > 10) {
      const avgHorizontal = (margin.left + margin.right) / 2;
      margin.left = avgHorizontal;
      margin.right = avgHorizontal;
    }
    if (verticalBalance > 15) {
      const avgVertical = (margin.top + margin.bottom) / 2;
      margin.top = avgVertical;
      margin.bottom = avgVertical;
    }
    
    // 🔒 MEJORA ESTÉTICA: Asegurar que el SVG tenga suficiente espacio para las etiquetas de ejes
    // Calcular dimensiones del gráfico después de calcular márgenes
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    // Verificar que el ancho sea suficiente (ajustar si es necesario)
    const minChartWidth = 200; // Ancho mínimo para el área del gráfico
    const minWidth = margin.left + margin.right + minChartWidth;
    if (width < minWidth) {
      width = minWidth;
      chartWidth = width - margin.left - margin.right;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      const maxAvailableWidth = container.clientWidth || width;
      if (width > maxAvailableWidth) {
        width = maxAvailableWidth;
        chartWidth = Math.max(width - margin.left - margin.right, minChartWidth);
      }
    }
    
    // Verificar que la altura sea suficiente
    const minChartHeight = 200; // Altura mínima para el área del gráfico
    const minHeight = margin.top + margin.bottom + minChartHeight;
    if (height < minHeight) {
      height = minHeight;
      chartHeight = height - margin.top - margin.bottom;
    } else {
      // 🔒 MEJORA ESTÉTICA: Asegurar que el gráfico no exceda el contenedor
      const maxAvailableHeight = container.clientHeight || height;
      if (height > maxAvailableHeight) {
        height = maxAvailableHeight;
        chartHeight = Math.max(height - margin.top - margin.bottom, minChartHeight);
      }
    }
    
    // 🔒 CORRECCIÓN: Crear SVG con viewBox para mejor centrado y escalado responsivo
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
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
      return spec.pointRadius || styles.pointRadius;
    };

    // Estado de selección persistente
    // Mantener un conjunto de índices de puntos seleccionados
    let selectedIndices = new Set();
    let isBrushing = false;
    
    // Obtener estilos unificados
    const styles = getUnifiedStyles();
    
    // Función para obtener el color base de un punto
    const getBaseColor = (d) => {
      if (d.color) return d.color;
      if (spec.colorMap && d.category) {
        return spec.colorMap[d.category] || spec.color || styles.primaryColor;
      }
      return spec.color || styles.primaryColor;
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
            .attr('class', 'dot bestlib-point bestlib-point-selected')
            .attr('r', baseRadius * 1.5)
            .attr('fill', baseColor)
            .attr('stroke', styles.selectionColor)
            .attr('stroke-width', 2)
            .attr('opacity', styles.opacitySelected);
        } else if (isHighlighting) {
          // Durante el brush: puntos no seleccionados más tenues
          dot
            .attr('class', 'dot bestlib-point')
            .attr('r', baseRadius)
            .attr('fill', baseColor)
            .attr('stroke', 'none')
            .attr('stroke-width', 0)
            .attr('opacity', styles.opacityUnselected);
        } else {
          // Estado normal: puntos no seleccionados
          dot
            .attr('class', 'dot bestlib-point')
            .attr('r', baseRadius)
            .attr('fill', baseColor)
            .attr('stroke', '#ffffff')
            .attr('stroke-width', styles.pointStrokeWidth)
            .attr('opacity', 0.6);
        }
      });
    };
    
    // Función para enviar evento de selección
    // OPTIMIZACIÓN: Limitar tamaño del payload para datasets grandes
    const sendSelectionEvent = (indices) => {
      const MAX_PAYLOAD_ITEMS = 1000; // Límite de items a enviar
      
      // OPTIMIZACIÓN: Si hay muchos índices, solo procesar los primeros N
      const indicesArray = Array.from(indices);
      const limitedIndices = indicesArray.length > MAX_PAYLOAD_ITEMS 
        ? indicesArray.slice(0, MAX_PAYLOAD_ITEMS)
        : indicesArray;
      
      const selected = limitedIndices.map(i => data[i]).filter(d => d !== undefined);
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
        count: indices.size, // Contar total, no solo los enviados
        indices: limitedIndices,
        totalCount: indices.size, // Total real de seleccionados
        __scatter_letter__: scatterLetter
      });
      
      // Advertencia si se limitó el payload
      if (indices.size > MAX_PAYLOAD_ITEMS) {
        console.warn(`[BESTLIB] Selección grande (${indices.size} items). Enviando solo los primeros ${MAX_PAYLOAD_ITEMS} para optimizar rendimiento.`);
      }
    };
    
    // Puntos con D3 (renderizar PRIMERO)
    const dots = g.selectAll('.dot')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'dot bestlib-point')
      .attr('cx', d => x(d.x))
      .attr('cy', d => y(d.y))
      .attr('r', d => getRadius(d))
      .attr('fill', d => getBaseColor(d))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', styles.pointStrokeWidth)
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
          
          // OPTIMIZACIÓN: Usar coordenadas de datos directamente en lugar de convertir cada punto
          const xMin = Math.min(x0, x1);
          const xMax = Math.max(x0, x1);
          const yMin = Math.min(y0, y1);
          const yMax = Math.max(y0, y1);
          
          // OPTIMIZACIÓN: Convertir coordenadas de píxeles a datos una sola vez
          const xDataMin = x.invert(xMin);
          const xDataMax = x.invert(xMax);
          const yDataMin = y.invert(yMax); // Invertir porque y escala está invertida
          const yDataMax = y.invert(yMin);
          
          // OPTIMIZACIÓN: Identificar puntos dentro del área de brush usando comparación directa
          const brushedIndices = new Set();
          for (let i = 0; i < data.length; i++) {
            const d = data[i];
            if (d.x >= xDataMin && d.x <= xDataMax && 
                d.y >= yDataMin && d.y <= yDataMax) {
              brushedIndices.add(i);
            }
          }
          
          // OPTIMIZACIÓN: Actualizar visualización solo de puntos que cambiaron
          // En lugar de iterar sobre todos, usar D3's data binding más eficientemente
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
      const styles = getUnifiedStyles();
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x).ticks(6));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(6));
      
      applyUnifiedAxisStyles(yAxis);
      
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

  /**
   * Line Plot completo con D3.js
   * Versión mejorada del line chart con más opciones
   */
  function renderLinePlotD3(container, spec, d3, divId) {
    // line_plot usa 'series' directamente en el spec, no 'data'
    const series = spec.series || {};
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Calcular dominios
    let xMin = Infinity, xMax = -Infinity;
    let yMin = Infinity, yMax = -Infinity;
    
    Object.values(series).forEach(serie => {
      serie.forEach(point => {
        if (point.x != null && !isNaN(point.x)) {
          xMin = Math.min(xMin, point.x);
          xMax = Math.max(xMax, point.x);
        }
        if (point.y != null && !isNaN(point.y)) {
          yMin = Math.min(yMin, point.y);
          yMax = Math.max(yMax, point.y);
        }
      });
    });
    
    if (xMin === Infinity) xMin = 0;
    if (xMax === -Infinity) xMax = 100;
    if (yMin === Infinity) yMin = 0;
    if (yMax === -Infinity) yMax = 100;
    
    const x = d3.scaleLinear()
      .domain([xMin, xMax])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([yMin, yMax])
      .nice()
      .range([chartHeight, 0]);
    
    // Líneas
    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveLinear);
    
    // Validar que haya series
    const seriesNames = Object.keys(series);
    if (seriesNames.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay series para mostrar</strong><br/>' +
        '<small>Verifica que los datos contengan valores válidos</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('renderLinePlotD3: No hay series', { spec, series });
      return;
    }
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const strokeWidth = options.strokeWidth || spec.strokeWidth || 2;
    const markers = options.markers !== undefined ? options.markers : (spec.markers !== undefined ? spec.markers : false);
    const colorMap = options.colorMap || spec.colorMap;
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    const colorScale = d3.scaleOrdinal()
      .domain(seriesNames)
      .range(colorMap ? Object.values(colorMap) : d3.schemeCategory10);
    
    seriesNames.forEach((name, idx) => {
      const serieData = series[name];
      if (!serieData || serieData.length === 0) return;
      
      const sortedData = [...serieData].sort((a, b) => a.x - b.x);
      
      g.append('path')
        .datum(sortedData)
        .attr('fill', 'none')
        .attr('stroke', colorScale(name))
        .attr('stroke-width', strokeWidth)
        .attr('d', line);
      
      // Marcadores opcionales
      if (markers) {
        g.selectAll(`.marker-${idx}`)
          .data(sortedData)
          .enter()
          .append('circle')
          .attr('class', `marker-${idx}`)
          .attr('cx', d => x(d.x))
          .attr('cy', d => y(d.y))
          .attr('r', 3)
          .attr('fill', colorScale(name));
      }
    });
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * Horizontal Bar Chart con D3.js
   */
  function renderHorizontalBarD3(container, spec, d3, divId) {
    const data = spec.data || [];
    
    // Validar datos
    if (!data || data.length === 0) {
      const errorMsg = '<div style="padding: 20px; text-align: center; color: #d32f2f; background: #ffebee; border: 2px solid #d32f2f; border-radius: 4px; margin: 10px;">' +
        '<strong>Error: No hay datos para mostrar</strong><br/>' +
        '<small>Verifica que los datos contengan valores válidos</small>' +
        '</div>';
      container.innerHTML = errorMsg;
      console.error('renderHorizontalBarD3: No hay datos', { spec, data });
      return;
    }
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 15, right: 15, bottom: 30, left: 100 }  // Más espacio izquierdo para labels
      : { top: 20, right: 20, bottom: 40, left: 120 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    // Escalas (invertidas para horizontal)
    const y = d3.scaleBand()
      .domain(data.map(d => d.category))
      .range([0, chartHeight])
      .padding(0.2);
    
    const x = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) || 100])
      .nice()
      .range([0, chartWidth]);
    
    // Barras
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', 0)
      .attr('y', d => y(d.category))
      .attr('width', 0)
      .attr('height', y.bandwidth())
      .attr('fill', color)
      .transition()
      .duration(500)
      .attr('width', d => x(d.value));
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * Hexbin Chart con D3.js
   * Visualización de densidad usando hexágonos
   */
  function renderHexbinD3(container, spec, d3, divId) {
    const data = spec.data || [];
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain(d3.extent(data, d => d.y) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const bins = options.bins !== undefined ? options.bins : (spec.bins !== undefined ? spec.bins : 20);
    const colorScale = options.colorScale || spec.colorScale || 'Blues';
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    // Hexbin - Implementación manual (D3 v7 no incluye hexbin por defecto)
    const hexRadius = Math.min(chartWidth, chartHeight) / (bins * 2);
    
    // Función para crear path de hexágono
    function hexagonPath(radius) {
      const points = [];
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i;
        points.push([radius * Math.cos(angle), radius * Math.sin(angle)]);
      }
      return 'M' + points.map(p => p.join(',')).join('L') + 'Z';
    }
    
    // Crear grid hexagonal y contar puntos
    const hexMap = new Map();
    data.forEach(d => {
      const xPos = x(d.x);
      const yPos = y(d.y);
      
      // Calcular coordenadas hexagonales
      const q = Math.round((2/3 * xPos) / hexRadius);
      const r = Math.round((-1/3 * xPos + Math.sqrt(3)/3 * yPos) / hexRadius);
      
      const key = `${q},${r}`;
      if (!hexMap.has(key)) {
        hexMap.set(key, { q, r, count: 0, points: [] });
      }
      hexMap.get(key).count++;
      hexMap.get(key).points.push(d);
    });
    
    const bins_data = Array.from(hexMap.values());
    const counts = bins_data.map(b => b.count);
    const maxCount = d3.max(counts) || 1;
    
    // Convertir coordenadas hexagonales a píxeles
    bins_data.forEach(bin => {
      bin.x = hexRadius * (3/2 * bin.q);
      bin.y = hexRadius * (Math.sqrt(3) * (bin.q/2 + bin.r));
    });
    
    let color;
    if (colorScale === 'Blues') {
      color = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, maxCount]);
    } else if (colorScale === 'Reds') {
      color = d3.scaleSequential(d3.interpolateReds)
        .domain([0, maxCount]);
    } else {
      color = d3.scaleSequential(d3.interpolateViridis)
        .domain([0, maxCount]);
    }
    
    // Dibujar hexágonos
    g.selectAll('.hexagon')
      .data(bins_data)
      .enter()
      .append('path')
      .attr('class', 'hexagon')
      .attr('d', hexagonPath(hexRadius))
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .attr('fill', d => color(d.count))
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.5);
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * Errorbars Chart con D3.js
   */
  function renderErrorbarsD3(container, spec, d3, divId) {
    const data = spec.data || [];
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const yExtent = d3.extent(data, d => {
        const yVal = d.y || 0;
        const yErr = d.yerr || 0;
        return [yVal - yErr, yVal + yErr];
      }).flat();
    const y = d3.scaleLinear()
      .domain(d3.extent(yExtent) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const capSize = options.capSize || spec.capSize || 5;
    const strokeWidth = options.strokeWidth || spec.strokeWidth || 2;
    const color = options.color || spec.color || '#333';
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    // Dibujar errorbars
    data.forEach(d => {
      const xPos = x(d.x);
      const yPos = y(d.y);
      
      // Error en Y
      if (d.yerr) {
        const yErr = y(d.yerr);
        const yTop = y(d.y - d.yerr);
        const yBottom = y(d.y + d.yerr);
        
        // Línea vertical
        g.append('line')
          .attr('x1', xPos)
          .attr('x2', xPos)
          .attr('y1', yTop)
          .attr('y2', yBottom)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
        
        // Caps superiores e inferiores
        g.append('line')
          .attr('x1', xPos - capSize)
          .attr('x2', xPos + capSize)
          .attr('y1', yTop)
          .attr('y2', yTop)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
        
        g.append('line')
          .attr('x1', xPos - capSize)
          .attr('x2', xPos + capSize)
          .attr('y1', yBottom)
          .attr('y2', yBottom)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
      }
      
      // Error en X
      if (d.xerr) {
        const xErr = x(d.xerr);
        const xLeft = x(d.x - d.xerr);
        const xRight = x(d.x + d.xerr);
        
        // Línea horizontal
        g.append('line')
          .attr('x1', xLeft)
          .attr('x2', xRight)
          .attr('y1', yPos)
          .attr('y2', yPos)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
        
        // Caps izquierdos y derechos
        g.append('line')
          .attr('x1', xLeft)
          .attr('x2', xLeft)
          .attr('y1', yPos - capSize)
          .attr('y2', yPos + capSize)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
        
        g.append('line')
          .attr('x1', xRight)
          .attr('x2', xRight)
          .attr('y1', yPos - capSize)
          .attr('y2', yPos + capSize)
          .attr('stroke', color)
          .attr('stroke-width', strokeWidth);
      }
      
      // Punto central
      g.append('circle')
        .attr('cx', xPos)
        .attr('cy', yPos)
        .attr('r', 3)
        .attr('fill', color);
    });
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * Fill Between Chart con D3.js
   * Área entre dos líneas
   */
  function renderFillBetweenD3(container, spec, d3, divId) {
    const data = spec.data || [];
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Ordenar datos por x
    const sortedData = [...data].sort((a, b) => a.x - b.x);
    
    // Escalas
    const x = d3.scaleLinear()
      .domain(d3.extent(sortedData, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const yMin = d3.min(sortedData, d => Math.min(d.y1 || d.y, d.y2 || d.y)) || 0;
    const yMax = d3.max(sortedData, d => Math.max(d.y1 || d.y, d.y2 || d.y)) || 100;
    const y = d3.scaleLinear()
      .domain([yMin, yMax])
      .nice()
      .range([chartHeight, 0]);
    
    // Crear área
    const area = d3.area()
      .x(d => x(d.x))
      .y0(d => y(d.y1 || d.y))
      .y1(d => y(d.y2 || d.y))
      .curve(d3.curveLinear);
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const opacity = options.opacity !== undefined ? options.opacity : (spec.opacity !== undefined ? spec.opacity : 0.3);
    const showLines = options.showLines !== undefined ? options.showLines : (spec.showLines !== undefined ? spec.showLines : true);
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    // Dibujar área
    g.append('path')
      .datum(sortedData)
      .attr('fill', color)
      .attr('opacity', opacity)
      .attr('d', area);
    
    // Dibujar líneas opcionales
    if (showLines !== false) {
      const line1 = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y1 || d.y))
        .curve(d3.curveLinear);
      
      const line2 = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y2 || d.y))
        .curve(d3.curveLinear);
      
      g.append('path')
        .datum(sortedData)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('d', line1);
      
      g.append('path')
        .datum(sortedData)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('d', line2);
    }
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * Step Plot Chart con D3.js
   * Líneas escalonadas
   */
  function renderStepPlotD3(container, spec, d3, divId) {
    const data = spec.data || [];
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Ordenar datos por x
    const sortedData = [...data].sort((a, b) => a.x - b.x);
    
    // Escalas
    const x = d3.scaleLinear()
      .domain(d3.extent(sortedData, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain(d3.extent(sortedData, d => d.y) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Obtener opciones del spec (pueden estar en spec.options o directamente en spec)
    const options = spec.options || {};
    const stepType = options.stepType || spec.stepType || 'step';
    const color = options.color || spec.color || '#4a90e2';
    const strokeWidth = options.strokeWidth || spec.strokeWidth || 2;
    const axes = options.axes !== undefined ? options.axes : (spec.axes !== undefined ? spec.axes : true);
    const xLabel = options.xLabel || spec.xLabel;
    const yLabel = options.yLabel || spec.yLabel;
    
    // Crear línea escalonada
    let line;
    
    if (stepType === 'stepBefore') {
      line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveStepBefore);
    } else if (stepType === 'stepAfter') {
      line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveStepAfter);
    } else {
      // 'step' por defecto
      line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveStep);
    }
    
    // Dibujar línea
    g.append('path')
      .datum(sortedData)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', strokeWidth)
      .attr('d', line);
    
    // Ejes
    if (axes !== false) {
      const xAxis = d3.axisBottom(x);
      const yAxis = d3.axisLeft(y);
      
      g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .style('opacity', 1);
      
      g.append('g')
        .call(yAxis)
        .style('opacity', 1);
      
      // Etiquetas
      if (xLabel) {
        g.append('text')
          .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 5})`)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(xLabel);
      }
      
      if (yLabel) {
        g.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('y', -margin.left + 15)
          .attr('x', -chartHeight / 2)
          .style('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(yLabel);
      }
    }
  }

  /**
   * KDE (Kernel Density Estimation) con D3.js
   */
  function renderKdeD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderKdeD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        dataValue: spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para KDE</div>';
      return;
    }
    
    // Validar estructura de datos
    if (!Array.isArray(data) || data.length === 0 || !data[0] || (!data[0].hasOwnProperty('x') || !data[0].hasOwnProperty('y'))) {
      console.error('[BESTLIB] renderKdeD3: Estructura de datos inválida', { 
        dataLength: data.length,
        firstItem: data[0],
        dataType: Array.isArray(data) ? 'array' : typeof data
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: Estructura de datos inválida para KDE (esperado: [{x, y}, ...])</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Unificar lectura de opciones con fallback para compatibilidad
    const opt = spec.options || {};
    const color = opt.color || spec.color || '#4a90e2';
    const fill = opt.fill !== undefined ? opt.fill : true;
    const opacity = opt.opacity || 0.3;
    const strokeWidth = opt.strokeWidth || spec.strokeWidth || 2;
    const xLabel = opt.xLabel || spec.xLabel;
    const yLabel = opt.yLabel || spec.yLabel;
    
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.y) || 1])
      .nice()
      .range([chartHeight, 0]);
    
    // Área rellena
    if (fill) {
      const area = d3.area()
        .x(d => x(d.x))
        .y0(chartHeight)
        .y1(d => y(d.y))
        .curve(d3.curveMonotoneX);
      
      g.append('path')
        .datum(data)
        .attr('fill', color)
        .attr('fill-opacity', opacity)
        .attr('d', area);
    }
    
    // Línea
    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveMonotoneX);
    
    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', strokeWidth)
      .attr('d', line)
      .attr('class', 'bestlib-line');
    
    // Ejes usando funciones reutilizables
    if (spec.axes !== false) {
      renderXAxis(g, x, chartHeight, chartWidth, margin, xLabel, svg);
      renderYAxis(g, y, chartWidth, chartHeight, margin, yLabel, svg);
    }
  }
  
  /**
   * Distribution Plot (histograma + KDE) con D3.js
   */
  function renderDistplotD3(container, spec, d3, divId) {
    const data = spec.data || {};
    const histogram = data.histogram || [];
    const kde = data.kde || [];
    const rug = data.rug || [];
    
    if (!histogram || histogram.length === 0) {
      console.error('[BESTLIB] renderDistplotD3: No hay datos de histograma', { 
        spec,
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        dataKeys: spec.data ? Object.keys(spec.data) : [],
        histogramLength: histogram.length
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos de histograma para Distplot</div>';
      return;
    }
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const kdeColor = options.kdeColor || '#e24a4a';
    const rugColor = options.rugColor || '#4a90e2';
    
    // Combinar todos los datos para calcular dominios
    const allData = [...(histogram || []), ...(kde || [])];
    const xDomain = allData.length > 0 
      ? d3.extent(allData, d => d.x) 
      : [0, 100];
    const yMax = allData.length > 0 
      ? d3.max(allData, d => d.y) 
      : 1;
    
    const x = d3.scaleLinear()
      .domain(xDomain)
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, yMax])
      .nice()
      .range([chartHeight, 0]);
    
    // Histograma
    if (histogram.length > 0) {
      g.selectAll('.bar')
        .data(histogram)
        .enter()
        .append('rect')
        .attr('class', 'bestlib-bar')
        .attr('x', d => x(d.bin_start))
        .attr('width', d => x(d.bin_end) - x(d.bin_start))
        .attr('y', d => y(d.y))
        .attr('height', d => chartHeight - y(d.y))
        .attr('fill', color)
        .attr('opacity', 0.6);
    }
    
    // KDE
    if (kde.length > 0) {
      const kdeLine = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveMonotoneX);
      
      g.append('path')
        .datum(kde)
        .attr('fill', 'none')
        .attr('stroke', kdeColor)
        .attr('stroke-width', 2)
        .attr('d', kdeLine)
        .attr('class', 'bestlib-line');
    }
    
    // Rug
    if (rug.length > 0) {
      g.selectAll('.rug')
        .data(rug)
        .enter()
        .append('line')
        .attr('class', 'bestlib-point')
        .attr('x1', d => x(d.x))
        .attr('x2', d => x(d.x))
        .attr('y1', chartHeight)
        .attr('y2', chartHeight + 5)
        .attr('stroke', rugColor)
        .attr('stroke-width', 1)
        .attr('opacity', 0.6);
    }
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y));
      
      applyUnifiedAxisStyles(yAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Rug Plot con D3.js
   */
  function renderRugD3(container, spec, d3, divId) {
    console.log("[BESTLIB] renderRugD3()", spec);
    
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderRugD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para Rug</div>';
      return;
    }
    
    // Validar estructura de datos - Rug espera [{x: value}, ...]
    if (!Array.isArray(data) || data.length === 0 || !data[0] || !data[0].hasOwnProperty('x')) {
      console.error('[BESTLIB] renderRugD3: Estructura de datos inválida', { 
        dataLength: data.length,
        firstItem: data[0],
        dataType: Array.isArray(data) ? 'array' : typeof data
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: Estructura de datos inválida para Rug (esperado: [{x: value}, ...])</div>';
      return;
    }
    
    console.log("[BESTLIB] renderRugD3 DATA LENGTH", data.length);
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    // Márgenes estándar
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Unificar lectura de opciones con fallback para compatibilidad
    const opt = spec.options || {};
    const axis = opt.axis || 'x';
    const color = opt.color || spec.color || '#4a90e2';
    const size = opt.size || 2;
    const opacity = opt.opacity || 0.6;
    const strokeWidth = opt.strokeWidth || spec.strokeWidth || size;
    const tickHeight = opt.height || 3; // Altura de los ticks del rug
    const padding = opt.padding || 0; // Padding adicional
    
    // Obtener labels desde options o spec
    const xLabel = opt.xLabel || spec.xLabel;
    const yLabel = opt.yLabel || spec.yLabel;
    
    if (axis === 'x') {
      // Calcular dominio correctamente
      const xValues = data.map(d => d.x).filter(v => v != null && !isNaN(v));
      const xDomain = xValues.length > 0 ? d3.extent(xValues) : [0, 100];
      
      const x = d3.scaleLinear()
        .domain(xDomain)
        .nice()
        .range([0, chartWidth]);
      
      // Dibujar ticks del rug (líneas verticales pequeñas en la base del eje)
      g.selectAll('.rug-tick')
        .data(data)
        .enter()
        .append('line')
        .attr('class', 'bestlib-point')
        .attr('x1', d => x(d.x))
        .attr('x2', d => x(d.x))
        .attr('y1', chartHeight + padding)
        .attr('y2', chartHeight + padding + tickHeight * size)
        .attr('stroke', color)
        .attr('stroke-width', strokeWidth)
        .attr('opacity', opacity);
      
      if (spec.axes !== false) {
        renderXAxis(g, x, chartHeight, chartWidth, margin, xLabel, svg);
      }
    } else {
      // Calcular dominio correctamente para eje Y
      const yValues = data.map(d => d.x).filter(v => v != null && !isNaN(v));
      const yDomain = yValues.length > 0 ? d3.extent(yValues) : [0, 100];
      
      const y = d3.scaleLinear()
        .domain(yDomain)
        .nice()
        .range([chartHeight, 0]);
      
      // Dibujar ticks del rug en el eje Y (líneas horizontales pequeñas)
      g.selectAll('.rug-tick')
        .data(data)
        .enter()
        .append('line')
        .attr('class', 'bestlib-point')
        .attr('x1', -padding - tickHeight * size)
        .attr('x2', -padding)
        .attr('y1', d => y(d.x))
        .attr('y2', d => y(d.x))
        .attr('stroke', color)
        .attr('stroke-width', strokeWidth)
        .attr('opacity', opacity);
      
      if (spec.axes !== false) {
        renderYAxis(g, y, chartWidth, chartHeight, margin, yLabel, svg);
      }
    }
    
    console.log("[BESTLIB] renderRugD3 SPEC OK");
  }
  
  /**
   * Q-Q Plot con D3.js
   */
  function renderQqplotD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderQqplotD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para Q-Q Plot</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const strokeWidth = options.strokeWidth || spec.strokeWidth || 2;
    const showLine = options.showLine !== undefined ? options.showLine : true;
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain(d3.extent(data, d => d.y) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Línea de referencia (y = x)
    if (showLine) {
      const minVal = Math.min(d3.min(data, d => d.x), d3.min(data, d => d.y));
      const maxVal = Math.max(d3.max(data, d => d.x), d3.max(data, d => d.y));
      g.append('line')
        .attr('x1', x(minVal))
        .attr('x2', x(maxVal))
        .attr('y1', y(minVal))
        .attr('y2', y(maxVal))
        .attr('stroke', '#999')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '3,3')
        .attr('opacity', 0.5);
    }
    
    // Puntos
    g.selectAll('.point')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'bestlib-point')
      .attr('cx', d => x(d.x))
      .attr('cy', d => y(d.y))
      .attr('r', 3)
      .attr('fill', color)
      .attr('opacity', 0.6);
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y));
      
      applyUnifiedAxisStyles(yAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * ECDF (Empirical Cumulative Distribution Function) con D3.js
   */
  function renderEcdfD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderEcdfD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para ECDF</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const strokeWidth = options.strokeWidth || spec.strokeWidth || 2;
    const step = options.step !== undefined ? options.step : true;
    
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, 1])
      .range([chartHeight, 0]);
    
    // Línea ECDF
    let line;
    if (step) {
      line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveStepBefore);
    } else {
      line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveMonotoneX);
    }
    
    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', strokeWidth)
      .attr('d', line)
      .attr('class', 'bestlib-line');
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('.2f')));
      
      applyUnifiedAxisStyles(yAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Ridgeline Plot con D3.js
   */
  function renderRidgelineD3(container, spec, d3, divId) {
    const series = spec.series || {};
    if (!series || Object.keys(series).length === 0) {
      console.error('[BESTLIB] renderRidgelineD3: No hay series', { 
        spec, 
        hasSeries: 'series' in spec,
        seriesType: typeof spec.series,
        specKeys: Object.keys(spec),
        hasData: 'data' in spec
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay series para Ridgeline</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const overlap = options.overlap || 0.5;
    const opacity = options.opacity || 0.7;
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    const colorMap = options.colorMap || spec.colorMap || {};
    
    const categories = Object.keys(series);
    const numCategories = categories.length;
    const spacing = chartHeight / (numCategories + (numCategories - 1) * overlap);
    
    // Calcular dominios
    let xMin = Infinity, xMax = -Infinity, yMax = -Infinity;
    Object.values(series).forEach(serie => {
      serie.forEach(d => {
        xMin = Math.min(xMin, d.x);
        xMax = Math.max(xMax, d.x);
        yMax = Math.max(yMax, d.y);
      });
    });
    
    const x = d3.scaleLinear()
      .domain([xMin, xMax])
      .nice()
      .range([0, chartWidth]);
    
    const colorScale = d3.scaleOrdinal()
      .domain(categories)
      .range(d3.schemeCategory10);
    
    // Dibujar cada serie
    categories.forEach((cat, idx) => {
      const serie = series[cat];
      const yOffset = idx * spacing * (1 + overlap);
      const yScale = d3.scaleLinear()
        .domain([0, yMax])
        .range([spacing, 0]);
      
      const area = d3.area()
        .x(d => x(d.x))
        .y0(spacing)
        .y1(d => yScale(d.y))
        .curve(d3.curveMonotoneX);
      
      const line = d3.line()
        .x(d => x(d.x))
        .y(d => yScale(d.y))
        .curve(d3.curveMonotoneX);
      
      const gSeries = g.append('g')
        .attr('transform', `translate(0,${yOffset})`);
      
      const color = colorMap[cat] || colorScale(cat);
      
      // Área
      gSeries.append('path')
        .datum(serie)
        .attr('fill', color)
        .attr('fill-opacity', opacity)
        .attr('d', area);
      
      // Línea
      gSeries.append('path')
        .datum(serie)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('d', line)
        .attr('class', 'bestlib-line');
      
      // Etiqueta de categoría
      gSeries.append('text')
        .attr('x', -5)
        .attr('y', spacing / 2)
        .attr('text-anchor', 'end')
        .attr('alignment-baseline', 'middle')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .text(cat);
    });
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Ribbon Plot con D3.js
   */
  function renderRibbonD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.warn('[BESTLIB] renderRibbonD3: No hay datos', { spec });
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const color1 = options.color1 || '#4a90e2';
    const color2 = options.color2 || '#e24a4a';
    const opacity = options.opacity || 0.4;
    const showLines = options.showLines !== undefined ? options.showLines : true;
    const gradient = options.gradient !== undefined ? options.gradient : true;
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    
    const x = d3.scaleLinear()
      .domain(data.length > 0 ? d3.extent(data, d => d.x) : [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    // Calcular dominio Y para ribbon (y1 e y2)
    const y1Values = data.map(d => d.y1).filter(v => v != null);
    const y2Values = data.map(d => d.y2).filter(v => v != null);
    const allYValues = [...y1Values, ...y2Values];
    const yDomain = allYValues.length > 0
      ? [Math.min(...allYValues), Math.max(...allYValues)]
      : [0, 100];
    
    const y = d3.scaleLinear()
      .domain(yDomain)
      .nice()
      .range([chartHeight, 0]);
    
    // Gradiente si está habilitado
    if (gradient) {
      const gradientId = `ribbon-gradient-${divId}`;
      const grad = svg.append('defs')
        .append('linearGradient')
        .attr('id', gradientId)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%');
      
      grad.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', color1)
        .attr('stop-opacity', opacity);
      
      grad.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', color2)
        .attr('stop-opacity', opacity);
      
      // Área con gradiente
      const area = d3.area()
        .x(d => x(d.x))
        .y0(d => y(d.y1))
        .y1(d => y(d.y2))
        .curve(d3.curveMonotoneX);
      
      g.append('path')
        .datum(data)
        .attr('fill', `url(#${gradientId})`)
        .attr('d', area);
    } else {
      // Área sólida
      const area = d3.area()
        .x(d => x(d.x))
        .y0(d => y(d.y1))
        .y1(d => y(d.y2))
        .curve(d3.curveMonotoneX);
      
      g.append('path')
        .datum(data)
        .attr('fill', color1)
        .attr('fill-opacity', opacity)
        .attr('d', area)
        .attr('class', 'bestlib-area');
    }
    
    // Líneas opcionales
    if (showLines) {
      const line1 = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y1))
        .curve(d3.curveMonotoneX);
      
      const line2 = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y2))
        .curve(d3.curveMonotoneX);
      
      g.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', color1)
        .attr('stroke-width', 2)
        .attr('d', line1)
        .attr('class', 'bestlib-line');
      
      g.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', color2)
        .attr('stroke-width', 2)
        .attr('d', line2)
        .attr('class', 'bestlib-line');
    }
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y));
      
      applyUnifiedAxisStyles(yAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * 2D Histogram con D3.js
   */
  function renderHist2dD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderHist2dD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para Hist2D</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const colorScale = options.colorScale || 'Blues';
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.x) || [0, 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain(d3.extent(data, d => d.y) || [0, 100])
      .nice()
      .range([chartHeight, 0]);
    
    const maxValue = d3.max(data, d => d.value) || 1;
    const color = d3.scaleSequential(d3.interpolateBlues)
      .domain([0, maxValue]);
    
    // Celdas del heatmap
    g.selectAll('.cell')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bestlib-heatmap-cell')
      .attr('x', d => x(d.x_bin_start))
      .attr('y', d => y(d.y_bin_end))
      .attr('width', d => x(d.x_bin_end) - x(d.x_bin_start))
      .attr('height', d => y(d.y_bin_start) - y(d.y_bin_end))
      .attr('fill', d => color(d.value))
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.5);
    
    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      
      applyUnifiedAxisStyles(xAxis);
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y));
      
      applyUnifiedAxisStyles(yAxis);
      
      renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
    }
  }
  
  /**
   * Polar Plot con D3.js
   */
  function renderPolarD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderPolarD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para Polar</div>';
      return;
    }
    
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const size = Math.min(width, height);
    const radius = Math.min(size - 40, size - 40) / 2;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${size} ${size}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${size/2},${size/2})`);
    
    const options = spec.options || {};
    const color = options.color || spec.color || '#4a90e2';
    const showGrid = options.showGrid !== undefined ? options.showGrid : true;
    const showLabels = options.showLabels !== undefined ? options.showLabels : true;
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels (Polar usa labels especiales)
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    
    // Calcular coordenadas polares desde angle y radius (no usar x, y pre-calculados)
    const maxRadius = d3.max(data, d => (d.radius !== undefined ? d.radius : Math.sqrt(d.x*d.x + d.y*d.y))) || 1;
    const r = d3.scaleLinear()
      .domain([0, maxRadius])
      .range([0, radius]);
    
    // Grid circular
    if (showGrid) {
      const gridCircles = [0.25, 0.5, 0.75, 1.0];
      gridCircles.forEach(frac => {
        g.append('circle')
          .attr('r', radius * frac)
          .attr('fill', 'none')
          .attr('stroke', '#e0e0e0')
          .attr('stroke-width', 1)
          .attr('opacity', 0.5)
          .attr('class', 'bestlib-grid');
      });
      
      // Líneas radiales
      const numLines = 8;
      for (let i = 0; i < numLines; i++) {
        const angle = (i / numLines) * 2 * Math.PI;
        g.append('line')
          .attr('x1', 0)
          .attr('y1', 0)
          .attr('x2', radius * Math.cos(angle))
          .attr('y2', radius * Math.sin(angle))
          .attr('stroke', '#e0e0e0')
          .attr('stroke-width', 1)
          .attr('opacity', 0.5)
          .attr('class', 'bestlib-grid');
      }
    }
    
    // Puntos - recalcular coordenadas desde angle y radius
    g.selectAll('.point')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'bestlib-point')
      .attr('cx', d => {
        const angle = d.angle !== undefined ? d.angle : Math.atan2(d.y, d.x);
        const rad = d.radius !== undefined ? d.radius : Math.sqrt(d.x*d.x + d.y*d.y);
        return r(rad) * Math.cos(angle);
      })
      .attr('cy', d => {
        const angle = d.angle !== undefined ? d.angle : Math.atan2(d.y, d.x);
        const rad = d.radius !== undefined ? d.radius : Math.sqrt(d.x*d.x + d.y*d.y);
        return r(rad) * Math.sin(angle);
      })
      .attr('r', 3)
      .attr('fill', color)
      .attr('opacity', 0.6);
    
    // Líneas desde el centro
    g.selectAll('.line')
      .data(data)
      .enter()
      .append('line')
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', d => {
        const angle = d.angle !== undefined ? d.angle : Math.atan2(d.y, d.x);
        const rad = d.radius !== undefined ? d.radius : Math.sqrt(d.x*d.x + d.y*d.y);
        return r(rad) * Math.cos(angle);
      })
      .attr('y2', d => {
        const angle = d.angle !== undefined ? d.angle : Math.atan2(d.y, d.x);
        const rad = d.radius !== undefined ? d.radius : Math.sqrt(d.x*d.x + d.y*d.y);
        return r(rad) * Math.sin(angle);
      })
      .attr('stroke', color)
      .attr('stroke-width', 1)
      .attr('opacity', 0.3);
  }
  
  /**
   * Funnel Plot con D3.js
   */
  function renderFunnelD3(container, spec, d3, divId) {
    const data = spec.data || [];
    if (!data || data.length === 0) {
      console.error('[BESTLIB] renderFunnelD3: No hay datos', { 
        spec, 
        hasData: 'data' in spec,
        dataType: typeof spec.data,
        specKeys: Object.keys(spec)
      });
      container.innerHTML = '<div style="padding: 10px; color: #d32f2f; border: 1px solid #d32f2f;">Error: No hay datos para Funnel</div>';
      return;
    }
    const dims = getChartDimensions(container, spec, 400, 350);
    let width = dims.width;
    let height = dims.height;
    
    const isLargeDashboard = container.closest('.matrix-layout') && 
                             container.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
    const defaultMargin = isLargeDashboard 
      ? { top: 20, right: 20, bottom: 35, left: 40 }
      : { top: 25, right: 25, bottom: 45, left: 55 };
    const margin = calculateAxisMargins(spec, defaultMargin, width, height);
    
    let chartWidth = width - margin.left - margin.right;
    let chartHeight = height - margin.top - margin.bottom;
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('overflow', 'visible');
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const options = spec.options || {};
    const orientation = options.orientation || 'vertical';
    const color = options.color || spec.color || '#4a90e2';
    const opacity = options.opacity || 0.7;
    
    // Copiar xLabel/yLabel desde options al spec para renderAxisLabels
    if (options.xLabel && !spec.xLabel) {
      spec.xLabel = options.xLabel;
    }
    if (options.yLabel && !spec.yLabel) {
      spec.yLabel = options.yLabel;
    }
    
    const maxValue = d3.max(data, d => d.value) || 1;
    const numStages = data.length;
    const stageHeight = chartHeight / numStages;
    const maxWidth = chartWidth * 0.8;
    
    if (orientation === 'vertical') {
      const x = d3.scaleLinear()
        .domain([0, maxValue])
        .range([0, maxWidth]);
      
      data.forEach((d, i) => {
        const yPos = i * stageHeight;
        const barWidth = x(d.value);
        const centerX = chartWidth / 2;
        
        // Trapecio (funnel shape)
        const points = [
          [centerX - barWidth/2, yPos],
          [centerX + barWidth/2, yPos],
          [centerX + (i < numStages - 1 ? x(data[i+1].value)/2 : 0), yPos + stageHeight],
          [centerX - (i < numStages - 1 ? x(data[i+1].value)/2 : 0), yPos + stageHeight]
        ];
        
        g.append('polygon')
          .attr('points', points.map(p => p.join(',')).join(' '))
          .attr('fill', color)
          .attr('fill-opacity', opacity)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1)
          .attr('class', 'bestlib-bar');
        
        // Etiqueta
        g.append('text')
          .attr('x', centerX)
          .attr('y', yPos + stageHeight / 2)
          .attr('text-anchor', 'middle')
          .attr('alignment-baseline', 'middle')
          .style('font-size', '11px')
          .style('font-weight', '600')
          .text(d.stage);
      });
      
      if (spec.axes !== false) {
        const xAxis = d3.scaleLinear()
          .domain([0, maxValue])
          .range([0, maxWidth]);
        
        const axisG = g.append('g')
          .attr('transform', `translate(${chartWidth/2 - maxWidth/2},${chartHeight})`)
          .call(d3.axisBottom(x));
        
        applyUnifiedAxisStyles(axisG);
        renderAxisLabels(g, spec, chartWidth, chartHeight, margin, svg);
      }
    } else {
      // Horizontal (similar pero rotado)
      const y = d3.scaleLinear()
        .domain([0, maxValue])
        .range([0, maxWidth]);
      
      const stageWidth = chartWidth / numStages;
      
      data.forEach((d, i) => {
        const xPos = i * stageWidth;
        const barHeight = y(d.value);
        const centerY = chartHeight / 2;
        
        const points = [
          [xPos, centerY - barHeight/2],
          [xPos, centerY + barHeight/2],
          [xPos + stageWidth, centerY + (i < numStages - 1 ? y(data[i+1].value)/2 : 0)],
          [xPos + stageWidth, centerY - (i < numStages - 1 ? y(data[i+1].value)/2 : 0)]
        ];
        
        g.append('polygon')
          .attr('points', points.map(p => p.join(',')).join(' '))
          .attr('fill', color)
          .attr('fill-opacity', opacity)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1)
          .attr('class', 'bestlib-bar');
        
        g.append('text')
          .attr('x', xPos + stageWidth / 2)
          .attr('y', centerY)
          .attr('text-anchor', 'middle')
          .attr('alignment-baseline', 'middle')
          .style('font-size', '11px')
          .style('font-weight', '600')
          .text(d.stage);
      });
    }
  }

  // Exponer funciones globalmente
  global.render = render;
  global.getChartDimensions = getChartDimensions; // Exponer para uso en updates de gráficos enlazados
})(window);