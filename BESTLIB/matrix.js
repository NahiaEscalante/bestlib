export function render(divId, asciiLayout, mapping) {
    const container = document.getElementById(divId);
    if (!container) return;

    const rows = asciiLayout.trim().split("\n");
    container.style.display = "grid";
    container.style.gridTemplateColumns = `repeat(${rows[0].length}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${rows.length}, 120px)`;
    container.style.gap = "8px";

    rows.forEach(row => {
        row.split("").forEach(letter => {
            const cell = document.createElement("div");
            cell.className = "matrix-cell";
            cell.innerHTML = mapping[letter] || letter;
            container.appendChild(cell);
        });
    });
}
