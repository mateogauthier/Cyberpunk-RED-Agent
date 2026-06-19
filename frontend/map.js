// Night City 2045 — District Registry
// Source: Cyberpunk RED core rulebook + Night City Atlas (R. Talsorian Games)
// danger: 'green' = corporate/secure  |  'yellow' = civilian  |  'red' = combat

const DISTRICTS = [
  {
    id: 'watson',
    name: 'WATSON',
    danger: 'yellow',
    summary: 'A recovering industrial district on Night City\'s northern peninsula. Once the commercial heart of the city before the DataKrash wiped it out, Watson is now a dense patchwork of megabuildings, ethnic enclaves, and corpo redevelopment projects clawing back market share. The money is coming back — it just hasn\'t reached the street level yet.',
    factions: ['Maelstrom', 'Tyger Claws'],
    notes: [
      'NCPD 4th Precinct is headquartered in Watson Development — expect heavier patrol density than the zone reputation suggests.',
      'Corporate investment is reshaping the northern waterfront. New construction crews are regularly hit. Nobody\'s been caught.',
    ],
    zones: [
      { code: 'N', name: 'WATSON DEVELOPMENT', danger: 'yellow' },
      { code: 'O', name: 'KABUKI',              danger: 'yellow' },
      { code: 'E', name: 'LITTLE CHINA',        danger: 'yellow' },
      { code: 'D', name: 'THE HOT ZONE',        danger: 'red'    },
    ],
  },
  {
    id: 'city-center',
    name: 'CITY CENTER',
    danger: 'green',
    summary: 'The corporate fortress at the heart of Night City. Megacorp towers dominate the skyline and private security details sweep every block below them. Walking in without credentials is noticed. Staying without a reason is answered.',
    factions: ['Militech', 'Petrochem', 'Night Corp'],
    notes: [
      'Trauma Team subscription rate approaches 100% — average response time under four minutes across all three zones.',
      'Street gangs don\'t operate here. The corps have their own version of the same thing.',
    ],
    zones: [
      { code: 'B', name: 'UPPER MARINA', danger: 'green' },
      { code: 'R', name: 'EXEC ZONE',    danger: 'green' },
      { code: 'C', name: 'DOWNTOWN',     danger: 'green' },
    ],
  },
  {
    id: 'westbrook',
    name: 'WESTBROOK',
    danger: 'yellow',
    summary: 'Night City\'s entertainment hub and the preferred address for the wealthy who don\'t live inside corpo towers. Japantown drives the cultural identity of the district; Charter Hill hosts the estates. Tyger Claws run the underground here — they keep it just dangerous enough to be exciting.',
    factions: ['Tyger Claws'],
    notes: [
      'Old Japantown is the beating heart of Night City\'s Japanese diaspora. Tyger Claws tolerate tourists; they do not tolerate disrespect.',
      'Charter Hill estate security is private, well-funded, and shoots first in the dark.',
    ],
    zones: [
      { code: 'A', name: 'LITTLE EUROPE',  danger: 'yellow' },
      { code: 'Q', name: 'CHARTER HILL',   danger: 'green'  },
      { code: 'P', name: 'NEW WESTBROOK',  danger: 'yellow' },
      { code: 'H', name: 'OLD JAPANTOWN',  danger: 'yellow' },
    ],
  },
  {
    id: 'heywood',
    name: 'HEYWOOD',
    danger: 'yellow',
    summary: 'Sprawling residential territory stretching south of City Center. Predominantly Latino, with deep community roots that predate the corporate era. The Valentinos hold cultural authority here — they\'re not just a gang, they\'re a social institution. The Glen is a corporate-adjacent enclave carved into their territory, and they remember it.',
    factions: ['Valentinos', '6th Street'],
    notes: [
      'The Glen\'s upscale veneer hides the same logic running underneath — just better dressed and better paid.',
      'Heywood Docks and the industrial zone see regular turf disputes. Bodies surface in the bay on a predictable schedule.',
    ],
    zones: [
      { code: 'F', name: 'UNIVERSITY DISTRICT',    danger: 'yellow' },
      { code: 'G', name: 'THE GLEN',               danger: 'yellow' },
      { code: 'T', name: 'NORTH HEYWOOD',          danger: 'yellow' },
      { code: 'S', name: 'HEYWOOD DOCKS',          danger: 'red'    },
      { code: 'U', name: 'HEYWOOD INDUSTRIAL ZONE',danger: 'red'    },
    ],
  },
  {
    id: 'pacifica',
    name: 'PACIFICA',
    danger: 'yellow',
    summary: 'In 2045, Pacifica is a developing coastal district — part resort destination, part open wound. The Playground draws eddies and tourists from across the city. Two kilometers west, the Old Combat Zone still bleeds from the 4th Corporate War. Both realities exist here simultaneously and neither acknowledges the other.',
    factions: ['Animals', 'Voodoo Boys (emerging)', 'Community militia'],
    notes: [
      'The Old Combat Zone is functionally ungoverned. NCPD entry is classified as a hostile incursion.',
      'Pacifica Playground\'s resort development is backed by anonymous corporate funding. Locals stopped asking where the money comes from.',
    ],
    zones: [
      { code: 'J', name: 'PORT OF NIGHT CITY',  danger: 'yellow' },
      { code: 'I', name: 'SOUTH NIGHT CITY',    danger: 'yellow' },
      { code: 'L', name: 'OLD COMBAT ZONE',     danger: 'red'    },
      { code: 'K', name: 'RECLAMATION ZONE',    danger: 'red'    },
      { code: 'W', name: 'PACIFICA PLAYGROUND', danger: 'yellow' },
    ],
  },
  {
    id: 'santo-domingo',
    name: 'SANTO DOMINGO',
    danger: 'yellow',
    summary: 'Night City\'s industrial backbone. Power plants, factories, and working-class neighborhoods that keep the rest of the city running. 6th Street holds most of the civilian turf — they frame themselves as the protectors of ordinary people, which is sometimes even true. The NorCal Military Base is a hard boundary everyone respects.',
    factions: ['6th Street', 'Maelstrom (industrial zones)'],
    notes: [
      'Rancho Coronado is a suburban island of relative normalcy — residents maintain the polite fiction that the city stops at the district line.',
      'The NorCal Military Base is a sovereignty zone. Corporate interference there ends careers. Gang interference ends lives.',
    ],
    zones: [
      { code: 'M', name: 'NORCAL MILITARY BASE', danger: 'green'  },
      { code: 'V', name: 'SANTO DOMINGO',         danger: 'yellow' },
      { code: 'X', name: 'RANCHO CORONADO',       danger: 'yellow' },
    ],
  },
];

// ── RENDER ────────────────────────────────────────────────────────────────────

const mapLegend = document.getElementById('map-legend');

function buildLocationList() {
  mapLegend.innerHTML = `<div class="legend-header">DISTRICT REGISTRY</div>`;

  DISTRICTS.forEach(district => {
    const card = document.createElement('div');
    card.className = 'district-card';

    const header = document.createElement('div');
    header.className = 'district-card-header';
    header.innerHTML = `
      <span class="danger-pip ${district.danger}"></span>
      <span class="district-name">◈ ${district.name}</span>
      <span class="district-chevron">▶</span>
    `;
    header.addEventListener('click', () => {
      const open = card.classList.toggle('open');
      header.querySelector('.district-chevron').textContent = open ? '▼' : '▶';
    });

    const body = document.createElement('div');
    body.className = 'district-card-body';

    // Summary
    const summary = document.createElement('p');
    summary.className = 'district-summary';
    summary.textContent = district.summary;
    body.appendChild(summary);

    // Factions
    const factions = document.createElement('div');
    factions.className = 'district-factions';
    factions.innerHTML = `<span class="field-label">FACTIONS</span>${district.factions.join(' · ')}`;
    body.appendChild(factions);

    // Zone list
    const zoneDiv = document.createElement('div');
    zoneDiv.className = 'district-zone-list';

    const zoneLabel = document.createElement('div');
    zoneLabel.className = 'field-label';
    zoneLabel.textContent = 'ZONES';
    zoneDiv.appendChild(zoneLabel);

    const ul = document.createElement('ul');
    ul.className = 'zone-list';
    district.zones.forEach(zone => {
      const li = document.createElement('li');
      li.className = 'zone-item';
      li.innerHTML = `
        <span class="zone-code">${zone.code}</span>
        <span class="danger-pip ${zone.danger} small"></span>
        <span>${zone.name}</span>
      `;
      ul.appendChild(li);
    });
    zoneDiv.appendChild(ul);
    body.appendChild(zoneDiv);

    // Notes
    if (district.notes?.length) {
      const notesDiv = document.createElement('div');
      notesDiv.className = 'district-notes';
      district.notes.forEach(note => {
        const p = document.createElement('p');
        p.innerHTML = `<span class="note-bullet">◈</span>${note}`;
        notesDiv.appendChild(p);
      });
      body.appendChild(notesDiv);
    }

    card.appendChild(header);
    card.appendChild(body);
    mapLegend.appendChild(card);
  });
}

buildLocationList();
