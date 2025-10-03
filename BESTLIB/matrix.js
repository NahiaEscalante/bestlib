(function (global) {
  function render(divId, asciiLayout, mapping) {
    const container = document.getElementById(divId);
    if (!container) return;

    const rows = asciiLayout.trim().split("\n");
    container.style.display = "grid";
    container.style.gridTemplateColumns = `repeat(${rows[0].length}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${rows.length}, 140px)`;
    container.style.gap = "8px";

    const safeHtml = mapping.__safe_html__ !== false;

    function isD3Spec(value) {
      return value && typeof value === 'object' && (value.type === 'bar');
    }

    rows.forEach(row => {
      row.split("").forEach(letter => {
        const spec = mapping[letter];
        const cell = document.createElement("div");
        cell.className = "matrix-cell";

        if (isD3Spec(spec)) {
          ensureD3().then(d3 => renderD3(cell, spec, d3));
        } else if (safeHtml) {
          cell.innerHTML = spec || letter;
        } else {
          cell.textContent = (typeof spec === 'string') ? spec : letter;
        }

        container.appendChild(cell);
      });
    });
  }

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

  function renderD3(container, spec, d3) {
    if (spec.type === 'bar') {
      const data = Array.isArray(spec.data) ? spec.data : [];
      const width = container.clientWidth || 200;
      const height = container.clientHeight || 120;
      const margin = { top: 10, right: 10, bottom: 20, left: 25 };
      const innerW = Math.max(10, width - margin.left - margin.right);
      const innerH = Math.max(10, height - margin.top - margin.bottom);

      const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      const x = d3.scaleBand()
        .domain(data.map((d, i) => d.category ?? i))
        .range([0, innerW])
        .padding(0.2);

      const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value ?? 0) || 0])
        .range([innerH, 0]);

      svg.selectAll('rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', (d, i) => x(d.category ?? i))
        .attr('y', d => y(d.value ?? 0))
        .attr('width', x.bandwidth())
        .attr('height', d => innerH - y(d.value ?? 0));

      if (spec.axes !== false) {
        const xAxis = d3.axisBottom(x).tickSizeOuter(0);
        const yAxis = d3.axisLeft(y).ticks(4).tickSizeOuter(0);
        svg.append('g').attr('transform', `translate(0,${innerH})`).call(xAxis);
        svg.append('g').call(yAxis);
      }
    }
  }

  // expón la función
  global.render = render;
})(window);



// export function render(divId, asciiLayout, mapping) {
//     const container = document.getElementById(divId);
//     if (!container) return;

//     const rows = asciiLayout.trim().split("\n");
//     container.style.display = "grid";
//     container.style.gridTemplateColumns = `repeat(${rows[0].length}, 1fr)`;
//     container.style.gridTemplateRows = `repeat(${rows.length}, 140px)`;
//     container.style.gap = "8px";

//     const safeHtml = mapping.__safe_html__ !== false;

//     // Simple D3 support: if the mapping value is an object with type & data, render via d3
//     // Allowed types: 'bar'
//     function isD3Spec(value) {
//         return value && typeof value === 'object' && (value.type === 'bar');
//     }

//     rows.forEach(row => {
//         row.split("").forEach(letter => {
//             const spec = mapping[letter];
//             const cell = document.createElement("div");
//             cell.className = "matrix-cell";

//             if (isD3Spec(spec)) {
//                 // Lazy-load D3 if needed
//                 ensureD3().then(d3 => {
//                     renderD3(cell, spec, d3);
//                 });
//             } else if (safeHtml) {
//                 cell.innerHTML = spec || letter;
//             } else {
//                 cell.textContent = (typeof spec === 'string') ? spec : letter;
//             }

//             container.appendChild(cell);
//         });
//     });
// }

// function ensureD3() {
//     if (window.d3) return Promise.resolve(window.d3);
//     return new Promise((resolve, reject) => {
//         const script = document.createElement('script');
//         script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
//         script.onload = () => resolve(window.d3);
//         script.onerror = () => reject(new Error('No se pudo cargar D3'));
//         document.head.appendChild(script);
//     });
// }

// function renderD3(container, spec, d3) {
//     if (spec.type === 'bar') {
//         const data = Array.isArray(spec.data) ? spec.data : [];
//         const width = container.clientWidth || 200;
//         const height = container.clientHeight || 120;
//         const margin = { top: 10, right: 10, bottom: 20, left: 25 };
//         const innerW = Math.max(10, width - margin.left - margin.right);
//         const innerH = Math.max(10, height - margin.top - margin.bottom);

//         const svg = d3.select(container)
//             .append('svg')
//             .attr('width', width)
//             .attr('height', height)
//             .append('g')
//             .attr('transform', `translate(${margin.left},${margin.top})`);

//         const x = d3.scaleBand()
//             .domain(data.map((d, i) => d.category ?? i))
//             .range([0, innerW])
//             .padding(0.2);

//         const y = d3.scaleLinear()
//             .domain([0, d3.max(data, d => d.value ?? 0) || 0])
//             .range([innerH, 0]);

//         svg.selectAll('rect')
//             .data(data)
//             .enter()
//             .append('rect')
//             .attr('x', (d, i) => x(d.category ?? i))
//             .attr('y', d => y(d.value ?? 0))
//             .attr('width', x.bandwidth())
//             .attr('height', d => innerH - y(d.value ?? 0))
//             .attr('fill', spec.color || '#4e79a7');

//         if (spec.axes !== false) {
//             const xAxis = d3.axisBottom(x).tickSizeOuter(0);
//             const yAxis = d3.axisLeft(y).ticks(4).tickSizeOuter(0);
//             svg.append('g')
//                 .attr('transform', `translate(0,${innerH})`)
//                 .call(xAxis);
//             svg.append('g').call(yAxis);
//         }
//     }
// }
