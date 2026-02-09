document.addEventListener('DOMContentLoaded', async () => {
    // [GLOBAL SYNC] Initialize based on global state
    const currentCountry = (typeof CountryState !== 'undefined') ? CountryState.get() : 'APAC';
    const selector = document.getElementById('gov-country-select');
    if (selector) {
        selector.value = currentCountry === 'APAC' ? 'ALL' : currentCountry;
    }

    await loadGovResults();
    await loadCountries();
    initGovMap();
    initHistoryChart();

    // [GLOBAL SYNC] Listen for region changes
    window.addEventListener('countryChanged', (e) => {
        const newCountry = e.detail.country;
        const localValue = newCountry === 'APAC' ? 'ALL' : newCountry;

        if (selector && selector.value !== localValue) {
            selector.value = localValue;
            renderGovMonitor();
            renderISPDistribution(localValue);
            updateFailurePanel(localValue);
            // Also refresh history chart for the new country context
            initHistoryChart();
        }
    });

    // Update global state if local selector changes
    if (selector) {
        selector.addEventListener('change', (e) => {
            const val = e.target.value === 'ALL' ? 'APAC' : e.target.value;
            if (typeof CountryState !== 'undefined') {
                CountryState.set(val);
            }
        });
    }
});

let globalResults = {};
let globalStats = null;
let mapInstance = null;
let geoJsonLayer = null;
let historyChart = null;
let currentAuthority = 'INTERNAL';
let benchmarkData = null;

async function handleGovSourceChange() {
    currentAuthority = document.getElementById('gov-data-source').value;
    console.log("Gov Auth Switch:", currentAuthority);

    if (currentAuthority !== 'INTERNAL') {
        try {
            const res = await fetch(`/api/analytics/benchmarks`);
            benchmarkData = await res.json();
        } catch (e) { console.error(e); }
    }

    // Refresh all visuals
    renderLeaderboard();
    if (geoJsonLayer) updateMapStyle();
    // Update Failure analysis labels if needed
}

async function loadCountries() {
    try {
        const response = await fetch('/lab/api/countries');
        const data = await response.json();
        const selector = document.getElementById('gov-country-select');

        if (data.apac_codes && selector) {
            // Keep "ALL"
            data.apac_codes.forEach(country => {
                const option = document.createElement('option');
                option.value = country.code;
                option.textContent = country.name;
                selector.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

async function loadGovResults() {
    const tbody = document.getElementById('gov-results-body');
    try {
        // Parallel fetch for results and detailed stats
        const [resResults, resStats] = await Promise.all([
            fetch('/gov-monitor/api/results'),
            fetch('/gov-monitor/api/stats')
        ]);

        globalResults = await resResults.json();
        globalStats = await resStats.json();

        renderGovMonitor();
        renderLeaderboard();
        renderISPDistribution('ALL');
        updateFailurePanel('ALL');

        // Update map colors if map exists
        if (geoJsonLayer) updateMapStyle();
    } catch (error) {
        console.error('Error fetching gov results:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="p-10 text-center text-red-400 font-bold">Failed to load data. Manual scan required?</td></tr>';
    }
}

function renderGovMonitor() {
    const selector = document.getElementById('gov-country-select');
    const filter = selector ? selector.value : 'ALL';
    renderISPDistribution(filter); // Refresh ISP chart
    updateFailurePanel(filter); // [NEW] Refresh Failure Landscape
    const tbody = document.getElementById('gov-results-body');
    const totalCount = document.getElementById('total-domains-count');

    tbody.innerHTML = '';

    let flatList = [];

    // Flatten stats
    if (filter === 'ALL') {
        Object.keys(globalResults).forEach(country => {
            flatList = flatList.concat(globalResults[country]);
        });
    } else if (globalResults[filter]) {
        flatList = globalResults[filter];
    }

    // Zoom map if specific country selected
    if (filter !== 'ALL' && mapInstance && geoJsonLayer) {
        const layer = geoJsonLayer.getLayers().find(l => {
            const code = l.feature.properties.ISO_A2 || iso3to2[l.feature.id] || iso3to2[l.feature.properties.ISO_A3];
            return code === filter;
        });
        if (layer) {
            mapInstance.fitBounds(layer.getBounds(), { padding: [50, 50], maxZoom: 5 });
            layer.setStyle({ weight: 3, color: '#2563eb' });
            setTimeout(() => geoJsonLayer.resetStyle(layer), 2000);
        }
    } else if (mapInstance) {
        mapInstance.setView([15, 105], 3);
    }

    if (flatList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="p-10 text-center text-slate-400">No data available for this selection.</td></tr>';
        updateStats([], 0);
        if (totalCount) totalCount.innerText = "0";
        return;
    }

    // Render Rows
    flatList.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition border-b border-gray-50 last:border-0";

        // Status determination
        let status = 'Not Ready';
        let statusColor = 'bg-slate-100 text-slate-500';
        let score = 0;
        if (item.ipv6_dns) score++;
        if (item.ipv6_web) score++;
        if (item.dnssec) score++;

        if (score >= 2 && item.ipv6_web) {
            status = 'Ready';
            statusColor = 'bg-green-100 text-green-700';
        } else if (score > 0) {
            status = 'Partial';
            statusColor = 'bg-amber-100 text-amber-700';
        }

        tr.innerHTML = `
            <td class="p-6 font-bold text-slate-900">${item.domain}</td>
            <td class="p-6">${renderBool(item.ipv6_dns)}</td>
            <td class="p-6">${renderBool(item.ipv6_web)}</td>
            <td class="p-6">${getServiceMatrixBadge(item.service_matrix)}</td>
            <td class="p-6">${getPerformanceBadge(item.ipv4_rtt_ms, item.ipv6_rtt_ms)}</td>
            <td class="p-6">${renderBool(item.dnssec)}</td>
            <td class="p-6 text-right">
                <span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${statusColor}">${status}</span>
            </td>
        `;
        tbody.appendChild(tr);
    });

    if (totalCount) {
        // [MODIFIED] Use Set for Unique Count
        const uniqueDomains = new Set(flatList.map(item => item.domain));
        totalCount.innerText = uniqueDomains.size.toLocaleString();
    }
    updateStats(flatList);

    // Pagination Logic
    renderPagination(flatList);
}

let currentPage = 1;
const ITEMS_PER_PAGE = 20;

function renderPagination(fullList) {
    const tbody = document.getElementById('gov-results-body');
    const totalPages = Math.ceil(fullList.length / ITEMS_PER_PAGE);

    // Safety check
    if (currentPage > totalPages) currentPage = 1;
    if (currentPage < 1) currentPage = 1;

    // Slice Data
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageData = fullList.slice(start, end);

    // Clear and Render Rows
    tbody.innerHTML = '';
    pageData.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition border-b border-gray-50 last:border-0";

        // Status determination
        let status = 'Not Ready';
        let statusColor = 'bg-slate-100 text-slate-500';
        let score = 0;
        if (item.ipv6_dns) score++;
        if (item.ipv6_web) score++;
        if (item.dnssec) score++;

        if (score >= 2 && item.ipv6_web) {
            status = 'Ready';
            statusColor = 'bg-green-100 text-green-700';
        } else if (score > 0) {
            status = 'Partial';
            statusColor = 'bg-amber-100 text-amber-700';
        }

        tr.innerHTML = `
            <td class="p-6 font-bold text-slate-900">${item.domain}</td>
            <td class="p-6">${renderBool(item.ipv6_dns)}</td>
            <td class="p-6">${renderBool(item.ipv6_web)}</td>
            <td class="p-6">${getServiceMatrixBadge(item.service_matrix)}</td>
            <td class="p-6">${getPerformanceBadge(item.ipv4_rtt_ms, item.ipv6_rtt_ms)}</td>
            <td class="p-6">${renderBool(item.dnssec)}</td>
            <td class="p-6 text-right">
                <span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${statusColor}">${status}</span>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Render Controls
    let controls = document.getElementById('pagination-controls');
    if (!controls) {
        controls = document.createElement('div');
        controls.id = 'pagination-controls';
        controls.className = "flex justify-center items-center gap-4 py-6 border-t border-gray-100";
        tbody.parentNode.parentNode.appendChild(controls); // Append after table container
    }

    controls.innerHTML = `
        <button onclick="changePage(-1)" ${currentPage === 1 ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition">Previous</button>
        <span class="text-xs font-black text-slate-500 uppercase tracking-widest">Page ${currentPage} of ${totalPages}</span>
        <button onclick="changePage(1)" ${currentPage === totalPages ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition">Next</button>
    `;
}

function changePage(delta) {
    currentPage += delta;
    renderGovMonitor();
    // Scroll to table top
    document.getElementById('gov-results-body').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderBool(val) {
    return val
        ? '<span class="flex items-center text-green-600 font-bold"><svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg> Active</span>'
        : '<span class="flex items-center text-slate-300 font-bold"><svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" /></svg> No</span>';
}

function getServiceMatrixBadge(matrix) {
    if (!matrix || matrix === 'Unknown' || matrix === 'No-IPv6') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-slate-100 text-slate-400">Dimmed</span>`;
    }

    if (matrix === 'Full-Stack') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-emerald-100 text-emerald-700 border border-emerald-200 shadow-sm shadow-emerald-100">Full Stack</span>`;
    }

    if (matrix === 'Shadow-IPv6') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-amber-100 text-amber-700 border border-amber-200">Shadow v6</span>`;
    }

    return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-blue-50 text-blue-600 border border-blue-100">${matrix}</span>`;
}

function getPerformanceBadge(v4, v6) {
    if (!v6) return `<span class="text-[10px] font-bold text-slate-300 uppercase tracking-widest">N/A</span>`;
    if (!v4) return `<span class="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">IPv6 Exclusive</span>`;

    const diff = v6 - v4;
    const isFaster = diff <= 0;
    const colorClass = isFaster ? 'text-emerald-500' : (diff < 50 ? 'text-amber-500' : 'text-rose-500');

    return `
        <div class="flex flex-col gap-0.5">
            <div class="flex justify-between items-center gap-4 w-24">
                <span class="text-[9px] font-bold text-slate-400">V6 RTT</span>
                <span class="text-[10px] font-black ${colorClass}">${v6}ms</span>
            </div>
            <div class="flex justify-between items-center gap-4 w-24">
                <span class="text-[9px] font-bold text-slate-400">V4 RTT</span>
                <span class="text-[10px] font-bold text-slate-500">${v4}ms</span>
            </div>
        </div>
    `;
}

function updateStats(list) {
    if (!list || list.length === 0) {
        document.getElementById('stat-v6-web').innerText = '--%';
        document.getElementById('stat-v6-dns').innerText = '--%';
        document.getElementById('stat-dnssec').innerText = '--%';
        return;
    }

    const v6Web = list.filter(i => i.ipv6_web).length;
    const v6Dns = list.filter(i => i.ipv6_dns).length;
    const dnssec = list.filter(i => i.dnssec).length;

    document.getElementById('stat-v6-web').innerText = Math.round((v6Web / list.length) * 100) + '%';
    document.getElementById('stat-v6-dns').innerText = Math.round((v6Dns / list.length) * 100) + '%';
    document.getElementById('stat-dnssec').innerText = Math.round((dnssec / list.length) * 100) + '%';
}

// --- Map Logic ---
async function initGovMap() {
    if (!document.getElementById('gov-map')) return;

    mapInstance = L.map('gov-map', {
        zoomControl: false,
        attributionControl: false,
        minZoom: 2,
        maxZoom: 6,
        dragging: false, // Optional: Lock view for dashboard feel? Let's leave dragging but restrict bounds
        scrollWheelZoom: false
    }).setView([15, 105], 3); // Centered on South China Sea/APAC

    // [MODIFIED] No TileLayer (Vector Only)
    // This creates the clean "White/Graph" background requested

    // Load GeoJSON
    try {
        const response = await fetch('/lab/api/map/countries.geo.json');
        const data = await response.json();

        geoJsonLayer = L.geoJson(data, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(mapInstance);

        addLegend(mapInstance);
    } catch (e) {
        console.error("Map load failed", e);
    }
}

function addLegend(map) {
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = `
            <div class="bg-white/95 backdrop-blur-sm p-4 rounded-2xl shadow-2xl border border-slate-100 text-[10px] font-bold text-slate-800">
                <div class="mb-3 border-b border-slate-100 pb-2 text-[11px] uppercase tracking-wider text-slate-400">Readiness Intensity</div>
                <div class="space-y-1.5">
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#15803d] mr-2"></span> Leader (90-100)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#22c55e] mr-2"></span> High (75-89)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#a3e635] mr-2"></span> Advancing (60-74)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#fbbf24] mr-2"></span> Moderate (45-59)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#f97316] mr-2"></span> Developing (30-44)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#ef4444] mr-2"></span> Low (15-29)</div>
                    <div class="flex items-center"><span class="w-2.5 h-2.5 rounded-sm bg-[#be123c] mr-2"></span> Critical (0-14)</div>
                    <div class="flex items-center mt-2 pt-2 border-t border-slate-50 text-slate-400">
                        <span class="w-2.5 h-2.5 rounded-sm bg-slate-100 border border-slate-200 mr-2"></span> No Data Source
                    </div>
                </div>
            </div>
        `;
        return div;
    };
    legend.addTo(map);
}

// Helper: Convert 3-letter to 2-letter ISO codes
const iso3to2 = {
    "AFG": "AF", "ASM": "AS", "AUS": "AU", "BGD": "BD", "BTN": "BT", "IOT": "IO", "BRN": "BN", "KHM": "KH", "CHN": "CN", "CXR": "CX",
    "CCK": "CC", "COK": "CK", "FJI": "FJ", "PYF": "PF", "ATF": "TF", "GUM": "GU", "HKG": "HK", "IND": "IN", "IDN": "ID", "JPN": "JP",
    "KIR": "KI", "PRK": "KP", "KOR": "KR", "LAO": "LA", "MAC": "MO", "MYS": "MY", "MDV": "MV", "MHL": "MH", "FSM": "FM", "MNG": "MN",
    "MMR": "MM", "NRU": "NR", "NPL": "NP", "NCL": "NC", "NZL": "NZ", "NIU": "NU", "NFK": "NF", "MNP": "MP", "PAK": "PK", "PLW": "PW",
    "PNG": "PG", "PHL": "PH", "PCN": "PN", "WSM": "WS", "SGP": "SG", "SLB": "SB", "LKA": "LK", "TWN": "TW", "THA": "TH", "TLS": "TL",
    "TKL": "TK", "TON": "TO", "TUV": "TV", "VUT": "VU", "VNM": "VN", "WLF": "WF", "KAZ": "KZ"
};

function styleFeature(feature) {
    // Try ISO_A2 first, fallback to ISO_A3 conversion
    const countryCode = feature.properties.ISO_A2 || iso3to2[feature.id] || iso3to2[feature.properties.ISO_A3];

    // Use new score logic if available
    let score = -1; // Default -1 for "No Data"

    if (currentAuthority === 'INTERNAL') {
        if (globalStats && globalStats.ranking && countryCode) {
            const c = globalStats.ranking.find(r => r.country === countryCode);
            if (c) score = c.score;
        }
    } else if (benchmarkData && benchmarkData[currentAuthority]) {
        score = benchmarkData[currentAuthority][countryCode] || -1;
    }

    let color = '#f1f5f9'; // default slate-100 (No Data)
    let fillOpacity = 0.5;

    if (score >= 0) {
        fillOpacity = 0.85;
        // High-Resolution 7-Step Gradient Scale
        if (score >= 90) color = '#15803d';      // Green 700 (Leader)
        else if (score >= 75) color = '#22c55e'; // Green 500 (High)
        else if (score >= 60) color = '#a3e635'; // Lime 400 (Advancing)
        else if (score >= 45) color = '#fbbf24'; // Amber 400 (Moderate)
        else if (score >= 30) color = '#f97316'; // Orange 500 (Developing)
        else if (score >= 15) color = '#ef4444'; // Red 500 (Low)
        else color = '#be123c';                 // Rose 700 (Critical)
    }

    return {
        fillColor: color,
        weight: 1,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: fillOpacity
    };
}

function getCountryStats(code) {
    const list = globalResults[code] || [];
    if (list.length === 0) return { total: 0, rate: 0 };

    const ready = list.filter(i => i.ipv6_web).length; // Strict: must have v6 web
    return {
        total: list.length,
        rate: Math.round((ready / list.length) * 100)
    };
}

function updateMapStyle() {
    if (geoJsonLayer) geoJsonLayer.setStyle(styleFeature);
}

function onEachFeature(feature, layer) {
    const code = feature.properties.ISO_A2 || iso3to2[feature.id] || iso3to2[feature.properties.ISO_A3];
    let tooltipContent = `<strong>${feature.properties.name || code}</strong>`;

    if (globalStats && globalStats.ranking) {
        const countryData = globalStats.ranking.find(r => r.country === code);
        if (countryData) {
            tooltipContent += `<br/>Score: ${countryData.score}`;
            tooltipContent += `<br/>Level: <span style="font-weight:bold">${countryData.level}</span>`;
        } else {
            tooltipContent += `<br/>No Data`;
        }
    }

    layer.bindTooltip(tooltipContent, {
        sticky: true,
        direction: 'top',
        className: 'map-tooltip'
    });

    layer.on({
        mouseover: (e) => {
            const layer = e.target;
            layer.setStyle({ weight: 2, color: '#3b82f6', fillOpacity: 0.95 });
            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
                layer.bringToFront();
            }
        },
        mouseout: (e) => {
            geoJsonLayer.resetStyle(e.target);
        },
        click: (e) => {
            const code = feature.properties.ISO_A2 || iso3to2[feature.id] || iso3to2[feature.properties.ISO_A3];
            const selector = document.getElementById('gov-country-select');
            if (selector) {
                selector.value = code;
                renderGovMonitor(); // Trigger table update
                renderISPDistribution(code); // Trigger ISP update
                updateFailurePanel(code); // [NEW] Trigger Failure Panel update
            }
        }
    });
}

function renderISPDistribution(filter) {
    const container = document.getElementById('isp-distribution-container');
    if (!container || !globalResults) return;

    let targetData = [];
    if (filter === 'ALL') {
        Object.values(globalResults).forEach(list => {
            targetData = targetData.concat(list);
        });
    } else {
        targetData = globalResults[filter] || [];
    }

    // Aggregate by ISP
    const ispCounts = {};
    targetData.forEach(item => {
        const isp = item.isp || "Unknown";
        if (isp !== 'Unknown') {
            ispCounts[isp] = (ispCounts[isp] || 0) + 1;
        }
    });

    const sortedISPs = Object.entries(ispCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10

    if (sortedISPs.length === 0) {
        container.innerHTML = '<div class="text-slate-300 text-[10px] font-bold italic">No identified ISP infrastructure in this selection.</div>';
        return;
    }

    container.innerHTML = '';
    sortedISPs.forEach(([name, count]) => {
        const pct = Math.round((count / targetData.length) * 100);
        const div = document.createElement('div');
        div.className = "flex-shrink-0 bg-slate-50 border border-slate-100 rounded-2xl p-4 min-w-[140px] group hover:bg-blue-50 transition-all cursor-default relative";
        div.setAttribute('title', `ASN Infrastructure: ${name} hosts ${count} government domains.`);
        div.innerHTML = `
            <div class="text-[9px] font-black text-slate-400 uppercase tracking-tighter mb-1 group-hover:text-blue-400 truncate w-24" title="${name}">${name}</div>
            <div class="flex items-end justify-between">
                <span class="text-xl font-black text-slate-900">${pct}%</span>
                <span class="text-[10px] font-bold text-slate-400 mb-0.5">Share</span>
            </div>
            <div class="h-1 bg-slate-200 rounded-full mt-2 overflow-hidden w-full">
                <div class="h-full bg-blue-500 w-0 transition-all duration-1000" style="width: ${pct}%"></div>
            </div>
        `;
        container.appendChild(div);
    });
}

// --- Chart Logic ---
async function initHistoryChart() {
    const ctx = document.getElementById('govHistoryChart');
    if (!ctx) return;

    try {
        const selector = document.getElementById('gov-country-select');
        const countryFilter = (selector && selector.value !== 'ALL') ? selector.value : null;

        let url = '/gov-monitor/api/history';
        if (countryFilter) url += `?country=${countryFilter}`;

        const res = await fetch(url);
        const history = await res.json();

        const labels = history.map(h => h.date);
        const data = history.map(h => h.rate);

        // [NEW] Destroy old chart if it exists
        if (historyChart) {
            historyChart.destroy();
        }

        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Readiness %',
                    data: data,
                    borderColor: '#2563eb', // blue-600
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#fff',
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: '#f8fafc' } },
                    x: { grid: { display: false } }
                }
            }
        });
    } catch (e) {
        console.error("Chart failed", e);
    }
}

async function refreshHistoryChart() {
    console.log("Refreshing graph data...");
    await initHistoryChart();
}
// --- Stats & Leaderboard Renderers ---
function renderLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    if (!tbody || !globalStats || !globalStats.ranking) return;

    tbody.innerHTML = '';

    let activeRanking = globalStats.ranking;

    // Pivot data source if authoritative benchmark is active
    if (currentAuthority !== 'INTERNAL' && benchmarkData && benchmarkData[currentAuthority]) {
        const sourceData = benchmarkData[currentAuthority];
        activeRanking = globalStats.ranking.map(item => {
            const officialScore = sourceData[item.country] || 0;
            let level = 'Low';
            if (officialScore >= 80) level = 'High';
            else if (officialScore >= 50) level = 'Moderate';

            return {
                ...item,
                score: officialScore,
                level: level,
                is_benchmark: true
            };
        }).sort((a, b) => b.score - a.score);
    }

    const top10 = activeRanking.slice(0, 10);

    top10.forEach((item, idx) => {
        let levelColor = 'text-red-500';
        if (item.level === 'High') levelColor = 'text-green-500';
        else if (item.level === 'Moderate') levelColor = 'text-amber-500';

        const tr = document.createElement('tr');
        tr.className = "border-b border-gray-50 last:border-0 hover:bg-slate-50 transition";
        tr.innerHTML = `
            <td class="py-3 pl-4 font-black text-slate-300">#${idx + 1}</td>
            <td class="py-3 font-bold text-slate-700 flex items-center">
                <img src="https://flagcdn.com/24x18/${item.country.toLowerCase()}.png" class="mr-2 rounded shadow-sm w-4 h-3">
                ${COUNTRY_NAMES[item.country] || item.country}
            </td>
            <td class="py-3 text-right font-black text-slate-900">${item.score}${item.is_benchmark ? '%' : ''}</td>
            <td class="py-3 text-right pr-4 text-xs font-bold uppercase tracking-wider ${levelColor}">${item.level}</td>
        `;
        tbody.appendChild(tr);
    });
}

function updateFailurePanel(countryCode) {
    if (!globalStats || !globalStats.ranking) return;

    let stats = null;
    let label = "Global Analysis";
    let insight = "Select a country on the map to see specific infrastructure gaps.";

    if (countryCode === 'ALL') {
        const globalAvg = {
            missing_dns_pct: 0,
            web_unreachable_pct: 0,
            missing_dnssec_pct: 0
        };
        // Compute average across all
        const count = globalStats.ranking.length;
        if (count > 0) {
            globalStats.ranking.forEach(r => {
                globalAvg.missing_dns_pct += r.breakdown.missing_dns_pct;
                globalAvg.web_unreachable_pct += r.breakdown.web_unreachable_pct;
                globalAvg.missing_dnssec_pct += r.breakdown.missing_dnssec_pct;
            });
            globalAvg.missing_dns_pct = Math.round(globalAvg.missing_dns_pct / count);
            globalAvg.web_unreachable_pct = Math.round(globalAvg.web_unreachable_pct / count);
            globalAvg.missing_dnssec_pct = Math.round(globalAvg.missing_dnssec_pct / count);
        }
        stats = globalAvg;
        label = "APAC Regional Average";
    } else {
        const countryData = globalStats.ranking.find(r => r.country === countryCode);
        if (countryData) {
            stats = countryData.breakdown;
            label = `${countryCode} Infrastructure Analysis`;

            // Generate dynamic insight
            if (stats.missing_dns_pct > 50) insight = "Critical Gap: Majority of domains lack basic IPv6 DNS records.";
            else if (stats.web_unreachable_pct > 30) insight = "Common Issue: IPv6 is advertised in DNS but web servers are unreachable (firewall/config issues).";
            else if (stats.missing_dnssec_pct > 80) insight = "Security Risk: DNSSEC adoption is extremely low, leaving domains vulnerable to spoofing.";
            else if (countryData.score > 80) insight = "Excellent Status: This country is a regional leader in IPv6 adoption.";
            else insight = "Moderate progress detected. Continued investment needed.";
        }
    }

    if (stats) {
        document.getElementById('failure-country-label').innerText = label;
        document.getElementById('failure-insight-text').innerText = insight;

        // Animate Bars
        setBar('bar-fail-dns', 'fail-dns-pct', stats.missing_dns_pct);
        setBar('bar-fail-web', 'fail-web-pct', stats.web_unreachable_pct);
        setBar('bar-fail-sec', 'fail-sec-pct', stats.missing_dnssec_pct);
    }
}

function setBar(barId, labelId, pct) {
    const el = document.getElementById(barId);
    if (el) el.style.width = pct + '%';
    const label = document.getElementById(labelId);
    if (label) label.innerText = pct + '%';
}

async function triggerGovScan() {
    const btn = document.querySelector('button[onclick="triggerGovScan()"]');
    btn.innerText = "Scanning Domains... (0%)";
    btn.disabled = true;

    try {
        const res = await fetch('/gov-monitor/api/scan', { method: 'POST' });
        const data = await res.json();

        btn.innerText = "Updating Interface...";

        // Reload all data
        await loadGovResults();
        await refreshHistoryChart(); // [NEW] Refresh chart immediately

        btn.innerText = "Scan Completed";
        setTimeout(() => {
            btn.disabled = false;
            btn.innerText = "Trigger Manual Refresh (Admin)";
        }, 3000);
    } catch (e) {
        console.error("Scan failed", e);
        btn.innerText = "Scan Failed";
        setTimeout(() => {
            btn.disabled = false;
            btn.innerText = "Trigger Manual Refresh (Admin)";
        }, 3000);
    }
}

async function generatePDFReport() {
    const btn = document.querySelector('button[onclick="generatePDFReport()"]');
    const originalContent = btn.innerHTML;

    // Loading State
    btn.innerHTML = `
        <svg class="w-8 h-8 animate-spin text-white mb-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="text-[9px] font-black uppercase tracking-widest text-white">Building...</span>
    `;
    btn.disabled = true;

    try {
        const response = await fetch('/api/analytics/report/generate', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            // Trigger Download
            const link = document.createElement('a');
            link.href = data.url;
            link.download = data.url.split('/').pop();
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            btn.innerHTML = `
                <svg class="w-8 h-8 text-green-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <span class="text-[9px] font-black uppercase tracking-widest text-green-400">Done</span>
            `;
        } else {
            console.error(data.message);
            btn.innerHTML = `<span class="text-[9px] text-red-400 font-bold">Error</span>`;
        }
    } catch (e) {
        console.error("PDF generation failed", e);
        btn.innerHTML = `<span class="text-[9px] text-red-400 font-bold">Failed</span>`;
    } finally {
        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }, 3000);
    }
}
