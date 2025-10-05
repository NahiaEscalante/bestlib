(function (global) {
  
  // ==========================================
  // Sistema de Comunicación (JS → Python)
  // ==========================================
  
  /**
   * Obtiene o crea un comm de Jupyter para comunicación con Python
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
      const J = global.Jupyter;
      const kernel = J && J.notebook && J.notebook.kernel;
      if (!kernel) {
        console.warn('[BESTLIB] Jupyter kernel no disponible');
        return null;
      }
      
      const comm = kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
      global._bestlibComms[divId] = comm;
      console.log(`[BESTLIB] Comm creado para ${divId}`);
      return comm;
    } catch (e) {
      console.warn('[BESTLIB] No se pudo crear comm:', e);
      return null;
    }
  }
  
  /**
   * Envía un evento desde JavaScript a Python
   * @param {string} divId - ID del contenedor matrix
   * @param {string} type - Tipo de evento (ej: 'select', 'click', 'brush')
   * @param {object} payload - Datos del evento
   */
  function sendEvent(divId, type, payload) {
    const comm = getComm(divId);
    if (comm) {
      comm.send({ 
        type: type, 
        div_id: divId, 
        payload: payload 
      });
      console.log(`[BESTLIB] Evento enviado: ${type}`, payload);
    } else {
      console.warn(`[BESTLIB] No se pudo enviar evento ${type}: comm no disponible`);
    }
  }
  
  // ==========================================
  // Renderizado Principal
  // ==========================================
  
  function render(divId, asciiLayout, mapping) {
    const container = document.getElementById(divId);
    if (!container) return;

    const rows = asciiLayout.trim().split("\n");
    container.style.display = "grid";
    container.style.gridTemplateColumns = `repeat(${rows[0].length}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${rows.length}, 140px)`;
    container.style.gap = "8px";

    const safeHtml = mapping.__safe_html__ !== false;
    const divIdFromMapping = mapping.__div_id__ || divId;

    function isD3Spec(value) {
      return value && typeof value === 'object' && (value.type === 'bar' || value.type === 'scatter');
    }

    rows.forEach(row => {
      row.split("").forEach(letter => {
        const spec = mapping[letter];
        const cell = document.createElement("div");
        cell.className = "matrix-cell";

        if (isD3Spec(spec)) {
          ensureD3().then(d3 => renderD3(cell, spec, d3, divIdFromMapping));
        } else if (safeHtml) {
          cell.innerHTML = spec || letter;
        } else {
          cell.textContent = (typeof spec === 'string') ? spec : letter;
        }

        container.appendChild(cell);
      });
    });
  }

  // ==========================================
  // Carga de D3.js
  // ==========================================
  
  function ensureD3() {
    if (global.d3) return Promise.resolve(global.d3);
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
      script.onload = () => resolve(global.d3);
      script.onerror = () => reject(new Error('No se pudo cargar D3'));
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

        data.forEach((d, i) => {
          const cx = (x(d.category ?? i) ?? 0) + x.bandwidth() / 2;
          if (cx >= x0 && cx <= x1) {
            selectedIdx.push(i);
            selectedItems.push(d);
          }
        });

        sendEvent(divId, 'select', { 
          type: 'bar',
          indices: selectedIdx, 
          items: selectedItems 
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

        points.each(function(d, i) {
          const cx = x(d.x ?? 0);
          const cy = y(d.y ?? 0);
          const isSelected = cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1;
          
          d3.select(this).attr('opacity', isSelected ? 1 : 0.2);
          
          if (isSelected) {
            selectedIdx.push(i);
            selectedItems.push(d);
          }
        });

        sendEvent(divId, 'select', {
          type: 'scatter',
          indices: selectedIdx,
          items: selectedItems
        });
      }
    }
  }

  // Exponer funciones globalmente
  global.render = render;
})(window);