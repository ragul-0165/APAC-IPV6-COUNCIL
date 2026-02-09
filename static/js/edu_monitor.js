document.addEventListener('DOMContentLoaded', async () => {
    // [GLOBAL SYNC] Initialize based on global state
    const currentCountry = (typeof CountryState !== 'undefined') ? CountryState.get() : 'APAC';
    const filterSelect = document.getElementById('country-filter');
    if (filterSelect) {
        filterSelect.value = currentCountry === 'APAC' ? 'ALL' : currentCountry;
    }

    await initializeAcademicHub();
    setupFilters();

    // [GLOBAL SYNC] Listen for region changes
    window.addEventListener('countryChanged', (e) => {
        const newCountry = e.detail.country;
        const localValue = newCountry === 'APAC' ? 'ALL' : newCountry;

        if (filterSelect && filterSelect.value !== localValue) {
            filterSelect.value = localValue;
            // Trigger refresh
            if (window.academicResults) {
                updateTable(window.academicResults, localValue);
            }
        }
    });

    // Update global state if local filter changes
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            const val = e.target.value === 'ALL' ? 'APAC' : e.target.value;
            if (typeof CountryState !== 'undefined') {
                CountryState.set(val);
            }
        });
    }
});

// [SHARED ACCESS] COUNTRY_NAMES is now provided globally by ai_hub.js

async function initializeAcademicHub() {
    try {
        const statsResponse = await fetch('/edu-monitor/api/stats');
        const stats = await statsResponse.json();

        const resultsResponse = await fetch('/edu-monitor/api/results');
        const results = await resultsResponse.json();

        // Store globally for filtering
        window.academicStats = stats;
        window.academicResults = results;

        // Enforce full names in ranking
        stats.ranking.forEach(r => {
            r.full_name = COUNTRY_NAMES[r.country] || r.country;
        });

        updateLeaderboard(stats.ranking);
        updateTable(results);
        renderSonarChart(stats.ranking);
        populateCountryFilter(stats.ranking);

    } catch (error) {
        console.error("Failed to initialize Academic Hub:", error);
    }
}

async function handleSourceChange() {
    const source = document.getElementById('data-source-select').value;
    console.log("Switching data source to:", source);

    if (source === 'INTERNAL') {
        // Restore original authentic scan data
        if (window.academicStats) {
            updateLeaderboard(window.academicStats.ranking);
            renderSonarChart(window.academicStats.ranking);
        }
    } else {
        // Fetch Official Benchmark Data
        try {
            const res = await fetch(`/api/analytics/benchmarks?source=${source}`);
            const benchmarks = await res.json();

            // Map benchmarks to the ranking structure for consistent UI updates
            const sourceData = benchmarks[source] || {};
            const simulatedRanking = window.academicStats.ranking.map(item => {
                const officialScore = sourceData[item.country] || 0;
                return {
                    ...item,
                    score: officialScore,
                    is_benchmark: true
                };
            });

            updateLeaderboard(simulatedRanking);
            renderSonarChart(simulatedRanking);

        } catch (e) {
            console.error("Benchmark fetch failed", e);
        }
    }
}

function updateLeaderboard(ranking) {
    const container = document.getElementById('edu-leaderboard');
    container.innerHTML = '';

    ranking.slice(0, 8).forEach(item => {
        const card = `
            <div class="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100/50 hover:border-indigo-100 transition group cursor-default">
                <div class="flex items-center gap-4">
                    <span class="text-xs font-black text-slate-300 w-4 font-mono group-hover:text-indigo-400 transition">#${item.rank}</span>
                    <div>
                        <p class="text-sm font-black text-slate-900 leading-tight">${item.full_name}</p>
                        <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">${item.total_domains} Institutions</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-sm font-black text-slate-900">${item.score}%</p>
                    <div class="w-16 h-1 bg-slate-200 rounded-full mt-1 overflow-hidden">
                        <div class="bg-indigo-500 h-full rounded-full" style="width: ${item.score}%"></div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', card);
    });
}

function updateTable(results, filterCountry = 'ALL') {
    const tbody = document.getElementById('edu-table-body');
    // Don't clear yet, we will generate HTML strings first

    let allRows = [];

    Object.entries(results).forEach(([countryCode, domains]) => {
        if (filterCountry !== 'ALL' && countryCode !== filterCountry) return;
        const countryName = COUNTRY_NAMES[countryCode] || countryCode;

        domains.forEach(d => {
            const row = `
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="py-5">
                        <p class="text-sm font-black text-slate-900">${d.domain}</p>
                        <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">${countryName} Sector</p>
                    </td>
                    <td>${getStatusBadge(d.ipv6_dns)}</td>
                    <td>${getStatusBadge(d.ipv6_web)}</td>
                    <td>${getServiceMatrixBadge(d.service_matrix)}</td>
                    <td>${getPerformanceBadge(d.ipv4_rtt_ms, d.ipv6_rtt_ms)}</td>
                    <td>${getStatusBadge(d.dnssec)}</td>
                    <td class="text-right">
                        <span class="text-[10px] font-bold text-slate-500 font-mono">${d.checked_at ? new Date(d.checked_at).toLocaleDateString() : 'Pending'}</span>
                    </td>
                </tr>
            `;
            allRows.push(row);
        });
    });

    // Pagination Logic
    renderPagination(allRows, document.getElementById('edu-table-body'));
}

let currentPage = 1;
const ITEMS_PER_PAGE = 20;

function renderPagination(rows, tbody) {
    const totalPages = Math.ceil(rows.length / ITEMS_PER_PAGE);

    // Safety check
    if (currentPage > totalPages) currentPage = 1;
    if (currentPage < 1) currentPage = 1;

    // Slice Data
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageData = rows.slice(start, end);

    // Clear and Render Rows
    tbody.innerHTML = ''; // Clear previous full render
    pageData.forEach(row => {
        tbody.insertAdjacentHTML('beforeend', row);
    });

    // Render Controls
    let controls = document.getElementById('pagination-controls');
    if (!controls) {
        controls = document.createElement('div');
        controls.id = 'pagination-controls';
        controls.className = "flex justify-center items-center gap-4 py-6 border-t border-gray-100 col-span-full";
        // Find a place to append. Table container is best.
        tbody.closest('.overflow-x-auto').parentNode.appendChild(controls);
    }

    controls.innerHTML = `
        <button onclick="changePage(-1)" ${currentPage === 1 ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition">Previous</button>
        <span class="text-xs font-black text-slate-500 uppercase tracking-widest">Page ${currentPage} of ${totalPages}</span>
        <button onclick="changePage(1)" ${currentPage === totalPages ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition">Next</button>
    `;

    // Store current filtered data for Next/Prev buttons to use
    window.currentFilteredRows = rows;
}

function changePage(delta) {
    currentPage += delta;
    if (window.currentFilteredRows) {
        renderPagination(window.currentFilteredRows, document.getElementById('edu-table-body'));
    }
    document.getElementById('edu-table-body').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function getStatusBadge(status) {
    if (status) {
        return `<span class="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-600 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border border-emerald-100">
            <span class="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></span> Valid
        </span>`;
    }
    return `<span class="inline-flex items-center gap-1.5 bg-rose-50 text-rose-600 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border border-rose-100">
        Missing
    </span>`;
}

function getServiceMatrixBadge(matrix) {
    if (!matrix || matrix === 'Unknown' || matrix === 'No-IPv6') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-slate-100 text-slate-400">Dimmed</span>`;
    }

    if (matrix === 'Full-Stack') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-emerald-100 text-emerald-700 border border-emerald-200">Full Stack</span>`;
    }

    if (matrix === 'Shadow-IPv6') {
        return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-amber-100 text-amber-700 border border-amber-200">Shadow v6</span>`;
    }

    return `<span class="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-indigo-50 text-indigo-600 border border-indigo-100">${matrix}</span>`;
}

function getPerformanceBadge(v4, v6) {
    if (!v6) return `<span class="text-[10px] font-bold text-slate-300 uppercase tracking-widest">N/A</span>`;
    if (!v4) return `<span class="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">IPv6 Exclusive</span>`;

    const diff = v6 - v4;
    const isFaster = diff <= 0;
    const colorClass = isFaster ? 'text-emerald-500' : (diff < 50 ? 'text-amber-500' : 'text-rose-500');

    return `
        <div class="flex flex-col gap-0.5">
            <div class="flex justify-between items-center gap-4 w-20">
                <span class="text-[9px] font-bold text-slate-400">V6</span>
                <span class="text-[10px] font-black ${colorClass}">${v6}ms</span>
            </div>
            <div class="flex justify-between items-center gap-4 w-20">
                <span class="text-[9px] font-bold text-slate-400">V4</span>
                <span class="text-[10px] font-bold text-slate-500">${v4}ms</span>
            </div>
        </div>
    `;
}

// [UPDATED] Sonar Radial Logic (ApexCharts)
function renderSonarChart(ranking) {
    // Filter Top 12 Economies for Clean "Radar" View
    // Sort by Total Domains (Density)
    const topData = ranking
        .sort((a, b) => b.total_domains - a.total_domains)
        .slice(0, 15);

    const labels = topData.map(r => r.full_name);
    const seriesData = topData.map(r => r.total_domains);

    // Color Logic: Map Readiness Score to Intensity
    // Adjusted for real data range (0-50%)
    const colors = topData.map(r => {
        if (r.score > 40) return '#6366f1';  // Indigo 500 (High: >40%)
        if (r.score > 25) return '#818cf8';  // Indigo 400 (Mid: 25-40%)
        if (r.score > 15) return '#a5b4fc';  // Indigo 300 (Low-Mid: 15-25%)
        return '#475569';                     // Slate 600 (Low: <15%)
    });


    var options = {
        series: seriesData,
        chart: {
            type: 'polarArea',
            height: 500,
            fontFamily: 'Instrument Sans, sans-serif',
            background: 'transparent',
            animations: { enabled: true, easing: 'easeinout', speed: 800 },
            events: {
                dataPointSelection: function (event, chartContext, config) {
                    const selectedCountry = topData[config.dataPointIndex].country;
                    console.log("Sonar Filter:", selectedCountry);
                    // Update dropdown and filter table
                    const select = document.getElementById('country-filter');
                    if (select) {
                        select.value = selectedCountry;
                        select.dispatchEvent(new Event('change'));
                    }
                }
            }
        },
        labels: labels,
        stroke: { colors: ['#0f172a'], width: 2 }, // Dark borders
        fill: { opacity: 0.9 },
        colors: colors,
        legend: {
            show: true,
            position: 'bottom',
            itemMargin: { horizontal: 10, vertical: 5 },
            fontSize: '11px',
            fontWeight: 700,
            formatter: function (seriesName, opts) {
                return seriesName + ": " + opts.w.globals.series[opts.seriesIndex] + " Unis"
            },
            labels: { colors: '#94a3b8' }
        },
        plotOptions: {
            polarArea: {
                rings: { strokeWidth: 1, strokeColor: '#334155' }, // Sonar Rings
                spokes: { strokeWidth: 1, connectorColors: '#334155' }
            }
        },
        theme: { mode: 'dark' }, // Force dark mode aesthetics inside chart
        tooltip: {
            theme: 'dark',
            custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                const data = topData[dataPointIndex];
                const color = w.config.colors[dataPointIndex];
                return `
                    <div class="px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl shadow-xl">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="w-3 h-3 rounded-full" style="background-color: ${color}"></span>
                            <span class="text-xs font-black text-white uppercase tracking-widest">${data.full_name}</span>
                        </div>
                        <div class="grid grid-cols-2 gap-4 text-xs">
                            <div>
                                <p class="text-slate-400 font-bold mb-0.5">Institutions</p>
                                <p class="text-white font-mono font-bold text-lg">${data.total_domains}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-slate-400 font-bold mb-0.5">Readiness</p>
                                <p class="text-indigo-400 font-mono font-bold text-lg">${data.score}%</p>
                            </div>
                        </div>
                        <div class="mt-2 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                            IPv6 Web: ${data.breakdown.web_unreachable_pct < 50 ? 'Active' : 'Offline'}
                        </div>
                    </div>
                `;
            }
        },
        dataLabels: {
            enabled: false // Too cluttered
        }
    };

    // Render
    var chart = new ApexCharts(document.querySelector("#edu-sonar"), options);
    chart.render();
}

function populateCountryFilter(ranking) {
    const select = document.getElementById('country-filter');
    ranking.forEach(item => {
        const opt = new Option(item.full_name, item.country);
        select.add(opt);
    });
}

function setupFilters() {
    document.getElementById('country-filter').addEventListener('change', async (e) => {
        const resultsResponse = await fetch('/edu-monitor/api/results');
        const results = await resultsResponse.json();
        updateTable(results, e.target.value);
    });
}

async function triggerEduScan() {
    const modal = document.getElementById('scan-modal');
    modal.classList.remove('hidden');

    // Animate progress
    const bar = document.getElementById('scan-progress-bar');
    bar.style.width = '10%';
    setTimeout(() => bar.style.width = '40%', 2000);
    setTimeout(() => bar.style.width = '70%', 5000);

    try {
        await fetch('/edu-monitor/api/scan', { method: 'POST' });
        bar.style.width = '100%';

        document.getElementById('scan-status-title').innerText = "Audit Complete";
        document.getElementById('scan-status-text').innerText = "Updating analytical models...";

        setTimeout(() => {
            window.location.reload();
        }, 1000);
    } catch (e) {
        console.error("Scan failed", e);
        modal.classList.add('hidden');
        alert("Scan sequence failed. Check system logs.");
    }
}
