(function (global) {
  
  // ==========================================
  // Sistema de Comunicación (JS → Python)
  // ==========================================
  
  /**
   * Obtiene o crea un comm de Jupyter para comunicación con Python
   * Compatible con Jupyter Notebook clásico y Google Colab
   * @param {string} divId - ID del contenedor matrix
   * @returns {object|null} Comm de Jupyter o null si no está disponible
   */
  function getComm(divId) {
    // Cache global de comms por div_id
    if (!global._bestlibComms) {
      global._bestlibComms = {};
    }
    
    if (global._bestlibComms[divId]) {
      return global._bestlibComms[divId];
    }
    
    try {
      // Intentar primero con Jupyter clásico
      const J = global.Jupyter;
      if (J && J.notebook && J.notebook.kernel) {
        const comm = J.notebook.kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
        global._bestlibComms[divId] = comm;
        return comm;
      }
      
      // Si no funciona, intentar con Google Colab (retorna Promise)
      if (global.google && global.google.colab && global.google.colab.kernel) {
        const commPromise = global.google.colab.kernel.comms.open("bestlib_matrix", { div_id: divId });
        
        // Guardar la promesa y resolverla
        commPromise.then(comm => {
          global._bestlibComms[divId] = comm;
        }).catch(err => {
          console.error('Error al crear comm:', err);
        });
        
        return commPromise;
      }
      
      // Último intento: buscar kernel en window
      if (global.IPython && global.IPython.notebook && global.IPython.notebook.kernel) {
        const comm = global.IPython.notebook.kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
        global._bestlibComms[divId] = comm;
        return comm;
      }
      
      return null;
      
    } catch (e) {
      console.error('Error al crear comm:', e);
      return null;
    }
  }
  
  /**
   * Envía un evento desde JavaScript a Python
   * Compatible con Jupyter Notebook clásico y Google Colab
   * @param {string} divId - ID del contenedor matrix
   * @param {string} type - Tipo de evento (ej: 'select', 'click', 'brush')
   * @param {object} payload - Datos del evento
   */
  async function sendEvent(divId, type, payload) {
    try {
      const commOrPromise = getComm(divId);
      
      if (!commOrPromise) {
        return;
      }
      
      // Si es una promesa (Colab), esperar a que se resuelva
      const comm = (commOrPromise instanceof Promise) 
        ? await commOrPromise 
        : commOrPromise;
      
      if (!comm) {
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
      }
    } catch (e) {
      console.error('Error al enviar datos:', e);
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
    container.style.gridTemplateColumns = `repeat(${C}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${R}, 140px)`;
    container.style.gap = "8px";

    const safeHtml = mapping.__safe_html__ !== false;
    const divIdFromMapping = mapping.__div_id__ || divId;
    
    // Soporte para merge de celdas
    const mergeOpt = mapping.__merge__;
    const mergeAll = mergeOpt === true;
    const mergeSet = Array.isArray(mergeOpt) ? new Set(mergeOpt) : null;
    const shouldMerge = (letter) => {
      if (letter === '.') return false;
      return mergeAll || (mergeSet ? mergeSet.has(letter) : false);
    };

    function isD3Spec(value) {
      return value && typeof value === 'object' && (value.type === 'bar' || value.type === 'scatter');
    }
    
    function isSimpleViz(value) {
      if (!value || typeof value !== 'object') return false;
      const type = value.type || value.shape;
      return type === 'circle' || type === 'rect' || type === 'line';
    }

    // Sistema de merge: marcar celdas visitadas
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
        
        // Si debe hacer merge, calcular el área rectangular
        if (shouldMerge(letter)) {
          // Expandir horizontalmente
          while (c + width < C && !visited[r][c + width] && rows[r][c + width] === letter) {
            width++;
          }
          
          // Expandir verticalmente
          let canGrow = true;
          while (r + height < R && canGrow) {
            for (let cc = c; cc < c + width; cc++) {
              if (visited[r + height][cc] || rows[r + height][cc] !== letter) {
                canGrow = false;
                break;
              }
            }
            if (canGrow) height++;
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
        cell.style.gridRow = `${r + 1} / span ${height}`;
        cell.style.gridColumn = `${c + 1} / span ${width}`;

        if (isD3Spec(spec) || isSimpleViz(spec)) {
          // Cargar D3 y renderizar (para gráficos Y formas simples)
          ensureD3().then(d3 => {
            if (isD3Spec(spec)) {
              renderChartD3(cell, spec, d3, divIdFromMapping);
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
   * Renderiza gráficos con D3.js
   */
  function renderChartD3(container, spec, d3, divId) {
    if (spec.type === 'bar') {
      renderBarChartD3(container, spec, d3, divId);
    } else if (spec.type === 'scatter') {
      renderScatterPlotD3(container, spec, d3, divId);
    }
  }
  
  /**
   * Gráfico de barras con D3.js
   */
  function renderBarChartD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const width = container.clientWidth || 400;
    const height = 250;  // Altura fija más compacta
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
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
    
    // Barras con D3
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
          // Enviar fila original completa si existe
          const originalRow = d._original_row || d;
          sendEvent(divId, 'select', {
            type: 'select',
            items: [originalRow],
            indices: [index],
            original_items: [d]  // Mantener compatibilidad
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
    
    // Ejes con D3 - Texto NEGRO y visible
    if (spec.axes) {
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
    }
  }
  
  /**
   * Gráfico de dispersión con D3.js
   */
  function renderScatterPlotD3(container, spec, d3, divId) {
    const data = spec.data || [];
    const width = container.clientWidth || 400;
    const height = 250;  // Altura fija más compacta
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Crear SVG con D3
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Escalas D3
    const x = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.x) || 100])
      .nice()
      .range([0, chartWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.y) || 100])
      .nice()
      .range([chartHeight, 0]);
    
    // Puntos con D3
    g.selectAll('.dot')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', d => x(d.x))
      .attr('cy', d => y(d.y))
      .attr('r', spec.pointRadius || 4)
      .attr('fill', d => {
        if (spec.colorMap && d.category) {
          return spec.colorMap[d.category] || '#4a90e2';
        }
        return spec.color || '#4a90e2';
      })
      .attr('opacity', 0.7)
      .style('cursor', spec.interactive ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (spec.interactive) {
          const index = data.indexOf(d);
          // Incluir fila original completa
          const originalRow = d._original_row || d;
          sendEvent(divId, 'point_click', {
            type: 'point_click',
            point: originalRow,  // Fila original completa
            index: index,
            original_point: d  // Mantener compatibilidad
          });
        }
      })
      .on('mouseenter', function() {
        if (spec.interactive) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('r', (spec.pointRadius || 4) * 1.5)
            .attr('opacity', 1);
        }
      })
      .on('mouseleave', function() {
        if (spec.interactive) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('r', spec.pointRadius || 4)
            .attr('opacity', 0.7);
        }
      });
    
    // Ejes con texto NEGRO y visible
    if (spec.axes) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x).ticks(6));
      
      xAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')  // NEGRO
        .style('font-family', 'Arial, sans-serif');
      
      xAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(6));
      
      yAxis.selectAll('text')
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', '#000000')  // NEGRO
        .style('font-family', 'Arial, sans-serif');
      
      yAxis.selectAll('line, path')
        .style('stroke', '#000000')
        .style('stroke-width', '1.5px');
    }
    
    // BRUSH para selección de área (MEJORADO)
    if (spec.interactive) {
      const brushGroup = g.append('g')
        .attr('class', 'brush-layer');
      
      const brush = d3.brush()
        .extent([[0, 0], [chartWidth, chartHeight]])
        .on('start', function(event) {
          if (!event.sourceEvent) return;
          g.selectAll('.dot').style('opacity', 0.3);
        })
        .on('brush', function(event) {
          if (!event.selection) return;
          
          const [[x0, y0], [x1, y1]] = event.selection;
          
          g.selectAll('.dot')
            .style('opacity', d => {
              const px = x(d.x);
              const py = y(d.y);
              return (px >= x0 && px <= x1 && py >= y0 && py <= y1) ? 1 : 0.1;
            })
            .attr('r', d => {
              const px = x(d.x);
              const py = y(d.y);
              const inSelection = px >= x0 && px <= x1 && py >= y0 && py <= y1;
              return inSelection ? (spec.pointRadius || 4) * 1.5 : (spec.pointRadius || 4);
            });
        })
        .on('end', function(event) {
          // Si no hay selección, resetear y salir
          if (!event.selection) {
            g.selectAll('.dot')
              .style('opacity', 0.7)
              .attr('r', spec.pointRadius || 4);
            return;
          }
          
          // Obtener coordenadas de la selección
          const [[x0, y0], [x1, y1]] = event.selection;
          
          // Filtrar puntos dentro de la selección
          const selected = data.filter(d => {
            const px = x(d.x);
            const py = y(d.y);
            return px >= x0 && px <= x1 && py >= y0 && py <= y1;
          });
          
          // Extraer filas originales completas si existen
          const selectedItems = selected.map(d => {
            // Si tiene _original_row, devolverlo; si no, devolver el item completo
            return d._original_row || d;
          });
          
          // Enviar el evento de selección con filas originales
          sendEvent(divId, 'select', {
            type: 'select',
            items: selectedItems,  // Filas originales completas
            count: selected.length,
            original_items: selected  // Mantener compatibilidad con datos del gráfico
          });
          
          // Resetear visualización de puntos
          g.selectAll('.dot')
            .transition()
            .duration(300)
            .style('opacity', 0.7)
            .attr('r', spec.pointRadius || 4);
          
          // Limpiar el brush visual
          brushGroup.call(brush.move, null);
        });
      
      brushGroup.call(brush);
    }
  }

  // ==========================================
  // Carga de D3.js (Optimizado para Colab)
  // ==========================================
  
  function ensureD3() {
    if (global.d3) return Promise.resolve(global.d3);
    
    return new Promise((resolve, reject) => {
      const existing = document.querySelector('script[src*="d3"]');
      if (existing) {
        const checkD3 = setInterval(() => {
          if (global.d3) {
            clearInterval(checkD3);
            resolve(global.d3);
          }
        }, 100);
        setTimeout(() => {
          clearInterval(checkD3);
          if (global.d3) resolve(global.d3);
          else reject(new Error('Timeout D3'));
        }, 5000);
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
      script.onload = () => {
        setTimeout(() => {
          if (global.d3) resolve(global.d3);
          else reject(new Error('D3 no se inicializó'));
        }, 50);
      };
      script.onerror = () => reject(new Error('Error cargar D3'));
      document.head.appendChild(script);
    });
  }

  // ==========================================
  // Renderizado D3.js con Interactividad
  // ==========================================
  
  function renderD3(container, spec, d3, divId) {
    if (spec.type === 'bar') {
      renderBarChart(container, spec, d3, divId);
    } else if (spec.type === 'scatter') {
      renderScatterPlot(container, spec, d3, divId);
    }
  }
  
  /**
   * Renderiza un gráfico de barras interactivo con brush
   */
  function renderBarChart(container, spec, d3, divId) {
    const data = Array.isArray(spec.data) ? spec.data : [];
    const width = container.clientWidth || 260;
    const height = container.clientHeight || 160;
    const margin = { top: 10, right: 10, bottom: 30, left: 35 };
    const innerW = Math.max(10, width - margin.left - margin.right);
    const innerH = Math.max(10, height - margin.top - margin.bottom);

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Escalas
    const x = d3.scaleBand()
      .domain(data.map((d, i) => d.category ?? i))
      .range([0, innerW])
      .padding(0.2);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value ?? 0) || 0])
      .range([innerH, 0]);

    // Barras con transiciones
    const bars = g.selectAll('rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('x', (d, i) => x(d.category ?? i))
      .attr('y', innerH)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', spec.color || '#4a90e2')
      .attr('class', 'bar');

    // Animación de entrada
    bars.transition()
      .duration(800)
      .attr('y', d => y(d.value ?? 0))
      .attr('height', d => innerH - y(d.value ?? 0));

    // Tooltips
    const tooltip = d3.select(container)
      .append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.8)')
      .style('color', 'white')
      .style('padding', '5px 10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', '1000');

    bars.on('mouseover', function(event, d) {
      d3.select(this).attr('fill', spec.hoverColor || '#357abd');
      tooltip.style('opacity', 1)
        .html(`<strong>${d.category ?? ''}</strong><br/>Valor: ${d.value ?? 0}`);
    })
    .on('mousemove', function(event) {
      tooltip.style('left', (event.offsetX + 10) + 'px')
        .style('top', (event.offsetY - 25) + 'px');
    })
    .on('mouseout', function() {
      d3.select(this).attr('fill', spec.color || '#4a90e2');
      tooltip.style('opacity', 0);
    });

    // Ejes
    if (spec.axes !== false) {
      g.append('g')
        .attr('transform', `translate(0,${innerH})`)
        .call(d3.axisBottom(x).tickSizeOuter(0))
        .selectAll('text')
        .style('font-size', '10px');
      
      g.append('g')
        .call(d3.axisLeft(y).ticks(4).tickSizeOuter(0))
        .selectAll('text')
        .style('font-size', '10px');
    }

    // Brush para selección
    if (spec.interactive !== false) {
      const brush = d3.brushX()
        .extent([[0, 0], [innerW, innerH]])
        .on('end', brushed);

      g.append('g')
        .attr('class', 'brush')
        .call(brush);

      function brushed({ selection }) {
        if (!selection) {
          sendEvent(divId, 'select', { 
            type: 'bar',
            indices: [], 
            items: [] 
          });
          return;
        }
        
        const [x0, x1] = selection;
        const selectedIdx = [];
        const selectedItems = [];
        const originalRows = [];

        data.forEach((d, i) => {
          const cx = (x(d.category ?? i) ?? 0) + x.bandwidth() / 2;
          if (cx >= x0 && cx <= x1) {
            selectedIdx.push(i);
            selectedItems.push(d);
            // Extraer todas las filas originales de esta categoría
            if (d._original_rows && Array.isArray(d._original_rows)) {
              originalRows.push(...d._original_rows);
            } else {
              originalRows.push(d);
            }
          }
        });

        sendEvent(divId, 'select', { 
          type: 'bar',
          indices: selectedIdx, 
          items: originalRows,  // Filas originales completas
          original_items: selectedItems  // Mantener compatibilidad
        });
      }
    }
  }
  
  /**
   * Renderiza un scatter plot interactivo con zoom y selección
   */
  function renderScatterPlot(container, spec, d3, divId) {
    const data = Array.isArray(spec.data) ? spec.data : [];
    const width = container.clientWidth || 260;
    const height = container.clientHeight || 160;
    const margin = { top: 10, right: 10, bottom: 30, left: 35 };
    const innerW = Math.max(10, width - margin.left - margin.right);
    const innerH = Math.max(10, height - margin.top - margin.bottom);

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Escalas
    const xExtent = d3.extent(data, d => d.x ?? 0);
    const yExtent = d3.extent(data, d => d.y ?? 0);
    
    const x = d3.scaleLinear()
      .domain([xExtent[0] * 0.9, xExtent[1] * 1.1])
      .range([0, innerW]);

    const y = d3.scaleLinear()
      .domain([yExtent[0] * 0.9, yExtent[1] * 1.1])
      .range([innerH, 0]);

    // Clip path para zoom
    g.append('defs').append('clipPath')
      .attr('id', `clip-${divId}`)
      .append('rect')
      .attr('width', innerW)
      .attr('height', innerH);

    const pointsGroup = g.append('g')
      .attr('clip-path', `url(#clip-${divId})`);

    // Puntos
    const points = pointsGroup.selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr('cx', d => x(d.x ?? 0))
      .attr('cy', d => y(d.y ?? 0))
      .attr('r', 0)
      .attr('fill', d => d.color || spec.color || '#e24a4a')
      .attr('opacity', 0.7)
      .attr('class', 'scatter-point');

    // Animación de entrada
    points.transition()
      .duration(600)
      .attr('r', spec.pointRadius || 4);

    // Tooltips
    const tooltip = d3.select(container)
      .append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.8)')
      .style('color', 'white')
      .style('padding', '5px 10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', '1000');

    points.on('mouseover', function(event, d) {
      d3.select(this)
        .attr('r', (spec.pointRadius || 4) * 1.5)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
      
      tooltip.style('opacity', 1)
        .html(`${d.label || ''}<br/>X: ${(d.x ?? 0).toFixed(2)}<br/>Y: ${(d.y ?? 0).toFixed(2)}`);
    })
    .on('mousemove', function(event) {
      tooltip.style('left', (event.offsetX + 10) + 'px')
        .style('top', (event.offsetY - 25) + 'px');
    })
    .on('mouseout', function() {
      d3.select(this)
        .attr('r', spec.pointRadius || 4)
        .attr('stroke', 'none');
      tooltip.style('opacity', 0);
    })
    .on('click', function(event, d) {
      const idx = data.indexOf(d);
      sendEvent(divId, 'point_click', {
        type: 'scatter',
        index: idx,
        point: d
      });
    });

    // Ejes
    if (spec.axes !== false) {
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${innerH})`)
        .call(d3.axisBottom(x).ticks(5).tickSizeOuter(0));
      
      const yAxis = g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickSizeOuter(0));
      
      xAxis.selectAll('text').style('font-size', '10px');
      yAxis.selectAll('text').style('font-size', '10px');
    }

    // Zoom
    if (spec.zoom !== false) {
      const zoom = d3.zoom()
        .scaleExtent([0.5, 10])
        .on('zoom', zoomed);

      svg.call(zoom);

      function zoomed({ transform }) {
        const newX = transform.rescaleX(x);
        const newY = transform.rescaleY(y);
        
        points.attr('cx', d => newX(d.x ?? 0))
          .attr('cy', d => newY(d.y ?? 0));
        
        g.select('.x-axis').call(d3.axisBottom(newX));
        g.select('.y-axis').call(d3.axisLeft(newY));
      }
    }

    // Brush para selección múltiple
    if (spec.interactive !== false) {
      const brush = d3.brush()
        .extent([[0, 0], [innerW, innerH]])
        .on('end', brushed);

      g.append('g')
        .attr('class', 'brush')
        .call(brush);

        function brushed({ selection }) {
        if (!selection) {
          points.attr('opacity', 0.7);
          sendEvent(divId, 'select', {
            type: 'scatter',
            indices: [],
            items: []
          });
          return;
        }

        const [[x0, y0], [x1, y1]] = selection;
        const selectedIdx = [];
        const selectedItems = [];
        const originalRows = [];

        points.each(function(d, i) {
          const cx = x(d.x ?? 0);
          const cy = y(d.y ?? 0);
          const isSelected = cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1;
          
          d3.select(this).attr('opacity', isSelected ? 1 : 0.2);
          
          if (isSelected) {
            selectedIdx.push(i);
            selectedItems.push(d);
            // Extraer fila original completa si existe
            originalRows.push(d._original_row || d);
          }
        });

        sendEvent(divId, 'select', {
          type: 'scatter',
          indices: selectedIdx,
          items: originalRows,  // Filas originales completas
          original_items: selectedItems  // Mantener compatibilidad
        });
      }
    }
  }

  // Exponer funciones globalmente
  global.render = render;
})(window);