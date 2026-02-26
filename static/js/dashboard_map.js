/**
 * Dashboard Heatmap Initialization
 * Standalone logic to render the APAC IPv6 heatmap.
 */

let dashboardMapInstance = null;
let dashboardDataCache = {};
let dashboardGeoJsonLayer = null;

const mapIso3to2 = {
    "AFG": "AF", "ASM": "AS", "AUS": "AU", "BGD": "BD", "BTN": "BT", "IOT": "IO", "BRN": "BN", "KHM": "KH", "CHN": "CN", "CXR": "CX",
    "CCK": "CC", "COK": "CK", "FJI": "FJ", "PYF": "PF", "ATF": "TF", "GUM": "GU", "HKG": "HK", "IND": "IN", "IDN": "ID", "JPN": "JP",
    "KIR": "KI", "PRK": "KP", "KOR": "KR", "LAO": "LA", "MAC": "MO", "MYS": "MY", "MDV": "MV", "MHL": "MH", "FSM": "FM", "MNG": "MN",
    "MMR": "MM", "NRU": "NR", "NPL": "NP", "NCL": "NC", "NZL": "NZ", "NIU": "NU", "NFK": "NF", "MNP": "MP", "PAK": "PK", "PLW": "PW",
    "PNG": "PG", "PHL": "PH", "PCN": "PN", "WSM": "WS", "SGP": "SG", "SLB": "SB", "LKA": "LK", "TWN": "TW", "THA": "TH", "TLS": "TL",
    "TKL": "TK", "TON": "TO", "TUV": "TV", "VUT": "VU", "VNM": "VN", "WLF": "WF", "KAZ": "KZ"
};

async function initDashboardMap() {
    const mapContainer = document.getElementById('apac-map');
    if (!mapContainer) return;

    dashboardMapInstance = L.map('apac-map', {
        zoomControl: false,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: false,
        doubleClickZoom: false
    }).setView([15, 105], 3);

    try {
        const [resGeo, resStats] = await Promise.all([
            fetch('/lab/api/map/countries.geo.json'),
            fetch('/lab/api/apac/all_stats')
        ]);

        const geoData = await resGeo.json();
        const statsData = await resStats.json();

        dashboardDataCache = statsData;

        dashboardGeoJsonLayer = L.geoJSON(geoData, {
            style: styleMapFeature,
            onEachFeature: onEachMapFeature
        }).addTo(dashboardMapInstance);

        addMapLegend(dashboardMapInstance);

        // Remove loading indicator
        document.getElementById('map-loader')?.remove();

    } catch (e) {
        console.error("Dashboard Map load failed", e);
        mapContainer.innerHTML = `<div class="flex items-center justify-center h-full text-red-400 font-bold">Map Data Unavailable</div>`;
    }
}

function styleMapFeature(feature) {
    const code = feature.properties.ISO_A2 || mapIso3to2[feature.id] || mapIso3to2[feature.properties.ISO_A3];
    const stats = dashboardDataCache[code];

    let color = '#f1f5f9';
    let opacity = 0.5;

    if (stats && stats.ipv6_adoption !== undefined) {
        const rate = stats.ipv6_adoption;
        opacity = 0.9;
        if (rate > 50) color = '#1e3a8a';
        else if (rate > 30) color = '#2563eb';
        else if (rate > 10) color = '#60a5fa';
        else if (rate > 5) color = '#93c5fd';
        else color = '#dbeafe';
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

function onEachMapFeature(feature, layer) {
    const code = feature.properties.ISO_A2 || mapIso3to2[feature.id] || mapIso3to2[feature.properties.ISO_A3];
    const stats = dashboardDataCache[code];
    let tooltipContent = `<strong>${feature.properties.name || code}</strong>`;

    if (stats && stats.ipv6_adoption !== undefined) {
        tooltipContent += `<br/>Adoption: ${stats.ipv6_adoption.toFixed(1)}%`;
    } else {
        tooltipContent += `<br/>No Data`;
    }

    layer.bindTooltip(tooltipContent, { sticky: true, direction: 'top', className: 'map-tooltip' });

    layer.on({
        mouseover: (e) => {
            var layer = e.target;
            layer.setStyle({ weight: 2, color: '#3b82f6', dashArray: '', fillOpacity: 0.9 });
            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) { layer.bringToFront(); }
        },
        mouseout: (e) => { dashboardGeoJsonLayer.resetStyle(e.target); },
        click: (e) => {
            dashboardMapInstance.fitBounds(e.target.getBounds());
            // Mirror Global Sync if CountryState exists
            if (typeof CountryState !== 'undefined') {
                CountryState.set(code);
            }
        }
    });
}

function addMapLegend(map) {
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

// Global Sync: Handle external changes (Map Navigation)
window.addEventListener('countryChanged', (e) => {
    const location = e.detail.country;

    if (location === 'APAC') {
        // Reset to full APAC view
        if (dashboardMapInstance) {
            dashboardMapInstance.setView([15, 105], 3);
            if (dashboardGeoJsonLayer) {
                dashboardGeoJsonLayer.eachLayer(layer => {
                    dashboardGeoJsonLayer.resetStyle(layer);
                });
            }
        }
    } else if (dashboardGeoJsonLayer && dashboardMapInstance) {
        dashboardGeoJsonLayer.eachLayer(layer => {
            const code = layer.feature.properties.ISO_A2 || mapIso3to2[layer.feature.id] || mapIso3to2[layer.feature.properties.ISO_A3];
            if (code === location) {
                dashboardMapInstance.fitBounds(layer.getBounds(), { padding: [50, 50], maxZoom: 5 });
                layer.setStyle({ weight: 3, color: '#3b82f6' });
                setTimeout(() => dashboardGeoJsonLayer.resetStyle(layer), 2000);
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', initDashboardMap);
