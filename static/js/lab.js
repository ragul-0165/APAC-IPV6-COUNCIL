// Global State
let mapInstance = null;
let apacDataCache = {};
let geoJsonLayer = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadCountries();

    // Use Global State for initialization
    const selector = document.getElementById('lab-country-select');
    const currentCountry = (typeof CountryState !== 'undefined') ? CountryState.get() : 'IN';

    if (selector) {
        selector.value = currentCountry;
        updateLabStats();
    }

    // Initialize Map
    initMap();

    // Set default learning level
    setLearningLevel('advanced');

    // Load Forecast
    loadForecast();

    // Render Charts
    renderHierarchyChart();

    // [GLOBAL SYNC] Handle external region changes
    window.addEventListener('countryChanged', (e) => {
        const newCountry = e.detail.country;
        if (selector && selector.value !== newCountry) {
            selector.value = newCountry;
            updateLabStats();
        }
    });

    // Update global state if local selector changes
    if (selector) {
        selector.addEventListener('change', (e) => {
            if (typeof CountryState !== 'undefined') {
                CountryState.set(e.target.value);
            }
        });
    }

    // Initialize Research Widgets
    loadAuthorityDelta();
    loadPerformanceTax();
    loadEqualityIndex();
    loadLedger();
});


// [NEW] Learning Level Logic
function setLearningLevel(level) {
    // Reset tabs
    ['beginner', 'intermediate', 'advanced'].forEach(l => {
        const btn = document.getElementById(`tab-${l}`);
        if (btn) {
            btn.className = l === level
                ? "px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all bg-white text-slate-900 shadow-sm ring-1 ring-slate-200"
                : "px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all text-slate-500 hover:text-slate-900";
        }
    });

    // Control visibility
    const mapSection = document.getElementById('apac-map').closest('section');
    const vizSection = document.getElementById('viz-section');
    const registrySection = document.getElementById('lab-lookup-results').closest('section');
    const economySection = document.getElementById('lab-stat-display').closest('section');

    if (level === 'beginner') {
        // Show Map + Economy only
        if (mapSection) mapSection.style.display = 'block';
        if (economySection) economySection.style.display = 'block';
        if (vizSection) vizSection.style.display = 'none';
        if (registrySection) registrySection.style.display = 'none';
    } else if (level === 'intermediate') {
        // Show Map + Economy + Visuals
        if (mapSection) mapSection.style.display = 'block';
        if (economySection) economySection.style.display = 'block';
        if (vizSection) vizSection.style.display = 'block';
        if (registrySection) registrySection.style.display = 'none';
    } else {
        // Advanced: Show All
        if (mapSection) mapSection.style.display = 'block';
        if (economySection) economySection.style.display = 'block';
        if (vizSection) vizSection.style.display = 'block';
        if (registrySection) registrySection.style.display = 'block';
    }
}

// [NEW] Interactive Map Logic
async function initMap() {
    const mapContainer = document.getElementById('apac-map');
    if (!mapContainer) return;

    // Center on APAC (approximate)
    // Center on APAC (approximate)
    mapInstance = L.map('apac-map', {
        zoomControl: false,
        attributionControl: false,
        dragging: false, // Lock view
        scrollWheelZoom: false,
        doubleClickZoom: false
    }).setView([15, 105], 3);

    // [MODIFIED] No TileLayer (Vector Only for offline support)

    // Fetch GeoJSON (using a simplified Asia/World dataset)
    // We will use a reliable public source for country shapes
    try {
        // Parallel Fetch: GeoJSON + Stats
        const [resGeo, resStats] = await Promise.all([
            fetch('/static/data/countries.geo.json'),
            fetch('/lab/api/apac/all_stats')
        ]);

        const geoData = await resGeo.json();
        const statsData = await resStats.json();

        // Cache stats globally for styling
        apacDataCache = statsData; // e.g. { "IN": { ipv6_adoption: 60.5 }, ... }

        geoJsonLayer = L.geoJSON(geoData, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(mapInstance);

        addLegend(mapInstance);

    } catch (e) {
        console.error("Map data load failed", e);
        mapContainer.innerHTML = `<div class="flex items-center justify-center h-full text-red-400 font-bold">Map Data Unavailable (${e.message})</div>`;
    }
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
    const code = feature.properties.ISO_A2 || iso3to2[feature.id] || iso3to2[feature.properties.ISO_A3];
    const stats = apacDataCache[code];

    let color = '#f1f5f9'; // default slate-100 (No Data)
    let opacity = 0.5;

    if (stats && stats.ipv6_adoption !== undefined) {
        const rate = stats.ipv6_adoption;
        opacity = 0.9;
        // Population Penetration Blue Scale
        if (rate > 50) color = '#1e3a8a'; // blue-900 (High)
        else if (rate > 30) color = '#2563eb'; // blue-600
        else if (rate > 10) color = '#60a5fa'; // blue-400
        else if (rate > 5) color = '#93c5fd'; // blue-300
        else color = '#dbeafe'; // blue-100 (Low)
    }

    return {
        fillColor: color,
        weight: 1,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: opacity
    };
}

function onEachFeature(feature, layer) {
    const code = feature.properties.ISO_A2 || iso3to2[feature.id] || iso3to2[feature.properties.ISO_A3];
    const stats = apacDataCache[code];
    let tooltipContent = `<strong>${feature.properties.name || code}</strong>`;

    if (stats && stats.ipv6_adoption !== undefined) {
        tooltipContent += `<br/>Adoption: ${stats.ipv6_adoption.toFixed(1)}%`;
    } else {
        tooltipContent += `<br/>No Data`;
    }

    layer.bindTooltip(tooltipContent, {
        sticky: true,
        direction: 'top',
        className: 'map-tooltip'
    });

    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
    });
}

function addLegend(map) {
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = `
            <div class="bg-white p-2 rounded shadow text-[10px] font-bold text-slate-600">
                <div class="mb-1">Population Adoption %</div>
                <div class="flex items-center"><span class="w-3 h-3 bg-blue-900 inline-block mr-1"></span> > 50%</div>
                <div class="flex items-center"><span class="w-3 h-3 bg-blue-600 inline-block mr-1"></span> 30-50%</div>
                <div class="flex items-center"><span class="w-3 h-3 bg-blue-400 inline-block mr-1"></span> 10-30%</div>
                <div class="flex items-center"><span class="w-3 h-3 bg-blue-100 inline-block mr-1"></span> < 10%</div>
            </div>
        `;
        return div;
    };
    legend.addTo(map);
}

function highlightFeature(e) {
    var layer = e.target;
    layer.setStyle({
        weight: 2,
        color: '#3b82f6',
        dashArray: '',
        fillOpacity: 0.9
    });
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

function resetHighlight(e) {
    geoJsonLayer.resetStyle(e.target);
}

function zoomToFeature(e) {
    mapInstance.fitBounds(e.target.getBounds());
    // Try to auto-select text
    const name = e.target.feature.properties.name;
    // Map name to select option text... rough match
    const select = document.getElementById('lab-country-select');
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].text.includes(name) || name.includes(select.options[i].text)) {
            select.selectedIndex = i;
            updateLabStats();
            break;
        }
    }
}


async function loadCountries() {
    try {
        const response = await fetch('/lab/api/countries');
        const data = await response.json();
        const selector = document.getElementById('lab-country-select');

        if (data.apac_codes && selector) {
            selector.innerHTML = '';
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

async function updateLabStats() {
    const selector = document.getElementById('lab-country-select');
    if (!selector) return;

    const location = selector.value;
    const rateDisplay = document.getElementById('lab-v6-rate');
    const progressBar = document.getElementById('lab-progress-bar');

    // [NEW] Auto-Navigate on Map
    if (geoJsonLayer && mapInstance) {
        geoJsonLayer.eachLayer(layer => {
            const code = layer.feature.properties.ISO_A2 || iso3to2[layer.feature.id] || iso3to2[layer.feature.properties.ISO_A3];
            if (code === location) {
                mapInstance.fitBounds(layer.getBounds(), { padding: [50, 50], maxZoom: 5 });
                layer.setStyle({ weight: 3, color: '#3b82f6' });
                setTimeout(() => geoJsonLayer.resetStyle(layer), 2000);
            }
        });
    }

    try {
        const response = await fetch(`/lab/api/apac/ipv6?location=${location}`);
        const data = await response.json();

        if (data.ipv6_adoption !== undefined) {
            const rate = data.ipv6_adoption.toFixed(1);
            rateDisplay.textContent = `${rate}%`;
            progressBar.style.width = `${rate}%`;

            // Add animation class
            rateDisplay.classList.remove('animate-pulse');
            void rateDisplay.offsetWidth; // Trigger reflow
            rateDisplay.classList.add('animate-in', 'fade-in', 'slide-in-from-bottom-1');

            // [NEW] Refresh Forecast for this specific country
            loadForecast(location);
            loadAuthorityDelta(location);
            loadPerformanceTax(location);
            loadEqualityIndex();
            loadLedger();
        } else {
            rateDisplay.textContent = 'N/A';
            progressBar.style.width = '0%';
            loadForecast(); // Fallback to regional
        }
    } catch (error) {
        console.error('Error fetching lab stats:', error);
        rateDisplay.textContent = 'ERR';
    }
}

async function performLabLookup() {
    // ... (Existing lookup logic) ...
    const query = document.getElementById('lab-query').value.trim();
    const resultsContainer = document.getElementById('lab-lookup-results');

    if (!query) return;

    resultsContainer.innerHTML = '<p class="text-xs text-slate-500 animate-pulse">Querying Registry...</p>';
    resultsContainer.classList.remove('hidden');

    try {
        const response = await fetch('/lab/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();

        if (data.error) {
            resultsContainer.innerHTML = `<div class="p-4 bg-red-50 text-red-600 rounded-xl text-xs font-bold border border-red-100">${data.error}</div>`;
        } else {
            resultsContainer.innerHTML = `
                <div class="space-y-3 animate-in fade-in slide-in-from-top-2">
                    <div class="flex justify-between text-[10px] font-bold">
                        <span class="text-slate-400">ORGANIZATION</span>
                        <span class="text-slate-900">${data.organization || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between text-[10px] font-bold">
                        <span class="text-slate-400">RESOURCE</span>
                        <span class="text-slate-900">${data.resource || data.query}</span>
                    </div>
                    <div class="flex justify-between text-[10px] font-bold">
                        <span class="text-slate-400">COUNTRY</span>
                        <span class="text-slate-900">${data.country || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between text-[10px] font-bold">
                        <span class="text-slate-400">STATUS</span>
                        <span class="text-blue-600">${data.status || 'Active'}</span>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        resultsContainer.innerHTML = '<div class="p-4 bg-red-50 text-red-600 rounded-xl text-xs font-bold border border-red-100">System lookup failed</div>';
    }
}

async function loadForecast(country = null) {
    try {
        let url = '/api/analytics/forecast/government';
        if (country) {
            url += `?country=${country}`;
        }
        const response = await fetch(url);
        const data = await response.json();

        const dateEl = document.getElementById('forecast-date');
        const daysEl = document.getElementById('forecast-days');
        const rateEl = document.getElementById('forecast-rate');
        const barEl = document.getElementById('forecast-bar');
        const confEl = document.getElementById('forecast-confidence');

        if (data.status === 'active') {
            dateEl.innerText = data.estimated_date;
            daysEl.innerText = `${data.days_remaining} days remaining`;
            rateEl.innerText = `+${data.growth_rate_daily} / day`;

            // Confidence Style
            if (data.confidence === 'high') {
                confEl.innerText = "High Confidence";
                confEl.className = "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-green-100 text-green-700";
            } else {
                confEl.innerText = "Low Confidence";
                confEl.className = "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-100 text-amber-700";
            }

            // Animate bar (Velocity visual)
            // Just a visual representation of "speed" relative to a baseline
            let speedPct = Math.min(data.growth_rate_daily * 500, 100);
            if (speedPct < 5) speedPct = 5;
            barEl.style.width = `${speedPct}%`;

        } else {
            dateEl.innerText = "Insufficient Data";
            daysEl.innerText = data.message;
            rateEl.innerText = "--";
            barEl.style.width = "0%";
        }

    } catch (e) {
        console.error("Forecast failed:", e);
    }
}

async function renderHierarchyChart() {
    const ctx = document.getElementById('hierarchyChart');
    if (!ctx) return;

    try {
        const response = await fetch('/lab/api/apac/all_stats');
        const data = await response.json();

        // Sort by adoption
        const sorted = Object.entries(data).sort(([, a], [, b]) => b.ipv6_adoption - a.ipv6_adoption).slice(0, 15);
        const labels = sorted.map(([k, v]) => v.country || k);
        const values = sorted.map(([k, v]) => v.ipv6_adoption);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'IPv6 Adoption %',
                    data: values,
                    backgroundColor: values.map(v => v > 50 ? '#1e3a8a' : v > 30 ? '#2563eb' : '#60a5fa'),
                    borderRadius: 6,
                    barThickness: 20
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
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { weight: 'bold' } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10, weight: 'bold' } }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Chart render failed", e);
    }
}
async function loadAuthorityDelta(country = null) {
    const valEl = document.getElementById('delta-value');
    const interpEl = document.getElementById('delta-interpretation');

    if (!valEl) return;

    try {
        const response = await fetch('/lab/api/delta');
        const data = await response.json();

        // Find specific country if provided, else show top discrepancy
        let target = country ? data.find(d => d.country === country) : data[0];

        if (target) {
            valEl.innerText = `${target.delta > 0 ? '+' : ''}${target.delta}%`;
            interpEl.innerText = target.interpretation;
            interpEl.className = `text-[10px] font-black uppercase px-2 py-1 rounded ${target.delta > 15 || target.delta < -15 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`;
        }
    } catch (e) {
        console.error("Delta load failed", e);
    }
}

async function loadPerformanceTax(country = null) {
    const pctEl = document.getElementById('tax-pct');
    const msEl = document.getElementById('tax-ms');
    const verdictEl = document.getElementById('tax-verdict');

    if (!pctEl) return;

    try {
        const response = await fetch('/lab/api/performance-tax?sector=gov');
        const data = await response.json();

        let target = country ? data.find(d => d.country === country) : data[0];

        if (target) {
            pctEl.innerText = `${target.avg_performance_tax_pct}%`;
            msEl.innerText = `${target.avg_ipv6_rtt_ms - target.avg_ipv4_rtt_ms}ms`;
            verdictEl.innerText = `${target.category} (${target.sample_count} samples)`;

            const isSlower = target.avg_performance_tax_pct > 0;
            pctEl.className = `text-3xl font-black ${isSlower ? 'text-rose-400' : 'text-emerald-400'}`;
        }
    } catch (e) {
        console.error("Tax load failed", e);
    }
}

async function loadEqualityIndex() {
    const giniEl = document.getElementById('equality-gini');
    const levelEl = document.getElementById('equality-level');
    const avgEl = document.getElementById('equality-avg');
    const barEl = document.getElementById('equality-bar');

    if (!giniEl) return;

    try {
        const response = await fetch('/lab/api/equality-index?sector=gov');
        const data = await response.json();

        if (data.gini_coefficient !== undefined) {
            giniEl.innerText = data.gini_coefficient;
            levelEl.innerText = data.inequality_level;
            avgEl.innerText = `${data.avg_adoption_rate}%`;
            barEl.style.width = `${data.avg_adoption_rate}%`;

            // Color based on inequality level
            giniEl.className = `text-5xl font-black tracking-tighter ${data.gini_coefficient < 0.3 ? 'text-emerald-600' : (data.gini_coefficient < 0.5 ? 'text-indigo-600' : 'text-rose-600')}`;
        }
    } catch (e) {
        console.error("Equality load failed", e);
    }
}

async function loadLedger() {
    const widget = document.getElementById('ledger-widget');
    const content = document.getElementById('ledger-content');
    if (!widget || !content) return;

    // Simulate technical provenance log
    const entries = [
        { event: "Weekly Sync Completed", target: "GOV_DOMAINS", status: "VERIFIED" },
        { event: "BGP Topology Update", target: "AS-PACIFIC", status: "STABLE" },
        { event: "Certificate Mining", target: "SAN-SCANNER", status: "ACTIVE" }
    ];

    content.innerHTML = entries.map(e => `
        <div class="flex items-center justify-between p-2 bg-white rounded border border-slate-100">
            <span class="text-[8px] font-black text-slate-800">${e.event}</span>
            <span class="text-[7px] font-bold px-1.5 py-0.5 rounded ${e.status === 'STABLE' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}">${e.status}</span>
        </div>
    `).join('');

    // Reveal content on hover or after delay
    setTimeout(() => {
        widget.classList.remove('opacity-50');
        content.classList.remove('hidden');
    }, 1500);
}
