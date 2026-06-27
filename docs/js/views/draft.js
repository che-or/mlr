import { state } from '../state.js';
import { loadDraftHistory } from '../data.js';
import { getFranchiseKey, getMlrLogoPair, makeLogoImg } from '../utils.js';

export async function renderDraftHistory() {
    const container = document.getElementById('draft-view');

    try {
        await loadDraftHistory();
    } catch (_) {
        container.innerHTML = '<p>Failed to load draft history.</p>';
        return;
    }

    const draftData = state.draftHistory;
    const seasons = Object.keys(draftData).map(Number).sort((a, b) => b - a);

    const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const paramSeason = parseInt(urlParams.get('season'));
    const selected = seasons.includes(paramSeason) ? paramSeason : seasons[0];

    const idx = seasons.indexOf(selected);
    const prev = idx < seasons.length - 1 ? seasons[idx + 1] : null;
    const next = idx > 0 ? seasons[idx - 1] : null;

    let html = `<div class="awards-header team-stats-header">
        <h2 class="section-title">Draft History —
            <select id="draft-season-select" class="title-season-select">
                ${seasons.map(s => `<option value="${s}" ${s === selected ? 'selected' : ''}>Season ${s}</option>`).join('')}
            </select>
        </h2>
        <div class="season-nav-buttons">
            ${prev ? `<a href="#/draft?season=${prev}" class="season-nav-button">&lt; Prev Season</a>` : ''}
            ${next ? `<a href="#/draft?season=${next}" class="season-nav-button">Next Season &gt;</a>` : ''}
        </div>
    </div>`;

    const seasonData = draftData[String(selected)];
    if (!seasonData) {
        container.innerHTML = html + '<p>No draft data for this season.</p>';
        return;
    }

    const rounds = Object.keys(seasonData).map(Number).sort((a, b) => a - b);
    const displaySeason = `S${selected}`;

    html += '<div class="draft-rounds-grid">';
    for (const round of rounds) {
        const picks = seasonData[String(round)];
        html += `<div class="draft-round-column">
            <h4>Round ${round}</h4>`;
        picks.forEach((pick, i) => {
            const pickNum = i + 1;
            const fk = getFranchiseKey(pick.team, displaySeason);
            const logoPair = getMlrLogoPair(fk, displaySeason);
            const logoHtml = logoPair
                ? makeLogoImg(logoPair.dark, logoPair.light, 'draft-pick-logo', pick.team)
                : `<span class="draft-pick-team-abbr">${pick.team}</span>`;

            let nameHtml;
            if (typeof pick.id === 'number') {
                const player = state.allPlayers.find(p => p.ID === pick.id);
                const name = player ? player.Name : `#${pick.id}`;
                nameHtml = `<a href="#/stats" class="player-link draft-pick-name" data-player-id="${pick.id}">${name}</a>`;
            } else {
                nameHtml = `<span class="draft-pick-name">${pick.id}</span>`;
            }

            html += `<div class="draft-pick">
                <span class="draft-pick-num">${pickNum}.</span>
                ${logoHtml}
                ${nameHtml}
            </div>`;
        });
        html += '</div>';
    }
    html += '</div>';

    container.innerHTML = html;

    container.querySelector('#draft-season-select').addEventListener('change', e => {
        window.location.hash = `#/draft?season=${e.target.value}`;
    });

    container.querySelectorAll('.player-link[data-player-id]').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            const id = parseInt(el.dataset.playerId);
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = '#/stats';
            });
        });
    });
}
