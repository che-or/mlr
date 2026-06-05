import { state } from '../state.js';

export function renderGlossary() {
    const content = document.getElementById('glossary-content');
    if (content.dataset.rendered) return;
    content.dataset.rendered = '1';

    document.getElementById('glossary-sidebar').innerHTML = '';

    const keys = Object.keys(state.glossary).sort((a, b) => a.localeCompare(b));
    const opts = ['<option value="">Choose a stat…</option>',
        ...keys.map(k => {
            const name = state.glossary[k]?.name || k;
            return `<option value="${k}">${k} — ${name}</option>`;
        })
    ].join('');

    content.innerHTML = `
        <div class="glossary-select-header">
            <select id="glossary-select">${opts}</select>
        </div>
        <div id="glossary-entry"></div>`;

    const select = content.querySelector('#glossary-select');
    const entry  = content.querySelector('#glossary-entry');

    const showPlaceholder = () => {
        entry.innerHTML = '<p class="glossary-placeholder">Select a stat from the dropdown above to view its definition.</p>';
    };

    const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const initial = params.get('stat');
    if (initial && state.glossary[initial]) {
        select.value = initial;
        renderEntry(select.value, entry);
    } else {
        showPlaceholder();
    }

    select.addEventListener('change', () => {
        if (select.value) renderEntry(select.value, entry);
        else showPlaceholder();
    });
}

function renderEntry(key, container) {
    const e = state.glossary[key];
    if (!e) { container.innerHTML = `<p>No entry for "${key}".</p>`; return; }

    let html = `<h2 class="glossary-entry-title"><span class="glossary-abbr">${key}</span> — ${e.name}</h2>`;

    if (e.details) html += `<p>${e.details}</p>`;

    if (Array.isArray(e.rules) && e.rules.length) {
        for (const rule of e.rules) {
            html += '<div class="glossary-rule">';
            if (rule.title) html += `<h4>${rule.title}</h4>`;
            if (Array.isArray(rule.conditions)) {
                html += '<ul>' + rule.conditions.map(c => `<li>${c}</li>`).join('') + '</ul>';
            }
            if (Array.isArray(rule.blocks)) {
                for (const b of rule.blocks) {
                    if (b.type === 'text')         html += `<p>${b.value}</p>`;
                    else if (b.type === 'equation') html += `<div class="equation">${b.value}</div>`;
                    else if (b.type === 'list')     html += '<ul>' + b.value.map(v => `<li>${v}</li>`).join('') + '</ul>';
                    else if (b.type === 'html')     html += b.value;
                }
            }
            html += '</div>';
        }
    }

    if (Array.isArray(e.sections)) {
        for (const s of e.sections) {
            html += `<h4>${s.title}</h4>`;
            if (Array.isArray(s.blocks)) {
                for (const b of s.blocks) {
                    if (b.type === 'text')     html += `<p>${b.value}</p>`;
                    else if (b.type === 'equation') html += `<div class="equation">${b.value}</div>`;
                    else if (b.type === 'list')     html += '<ul>' + b.value.map(v => `<li>${v}</li>`).join('') + '</ul>';
                    else if (b.type === 'html')     html += b.value;
                }
            } else if (typeof s.content === 'string') {
                html += s.content;
            }
        }
    }

    container.innerHTML = html;
}
