let currentCountry = 'IN';
let currentISPPage = 1;
const ISP_PER_PAGE = 25;
let fullISPData = [];
let filteredISPData = null;
let currentFilter = 'all';
let isVerifying = false;
let benchmarkChart = null;

document.addEventListener('DOMContentLoaded', () => {
    // [GLOBAL SYNC] Initialize based on global state
    const currentGlobalCountry = (typeof CountryState !== 'undefined') ? CountryState.get() : 'IN';

    loadStats();

    // Check if the current country is supported by the ISP explorer (currently only IN/MY)
    if (['IN', 'MY'].includes(currentGlobalCountry)) {
        switchISPCountry(currentGlobalCountry, false);
    } else {
        switchISPCountry('IN', false); // Default to India for ISP view if global is unsupported
    }

    // [GLOBAL SYNC] Listen for region changes
    window.addEventListener('countryChanged', (e) => {
        const newCountry = e.detail.country;
        if (['IN', 'MY'].includes(newCountry) && newCountry !== currentCountry) {
            switchISPCountry(newCountry, false);
        } else if (!['IN', 'MY'].includes(newCountry)) {
            console.log(`ISP Explorer: Country ${newCountry} is not yet indexed. Maintaining ${currentCountry}.`);
        }
    });
});

async function loadStats() {
    try {
        const response = await fetch('/isp-explorer/api/stats');
        const stats = await response.json();

        // Update Banner Counts
        const inStat = document.getElementById('stat-count-in');
        const myStat = document.getElementById('stat-count-my');
        if (inStat) inStat.innerText = `${stats.india_count.toLocaleString()} ASNs`;
        if (myStat) myStat.innerText = `${stats.malaysia_count.toLocaleString()} ASNs`;

        // Update Sidebar Badges
        const inBadge = document.getElementById('badge-count-in');
        const myBadge = document.getElementById('badge-count-my');
        if (inBadge) inBadge.innerText = `${stats.india_count.toLocaleString()} ASNs`;
        if (myBadge) myBadge.innerText = `${stats.malaysia_count.toLocaleString()} ASNs`;

    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

async function switchISPCountry(code, updateGlobal = true) {
    currentCountry = code;
    currentFilter = 'all'; // Reset filter on country switch
    const title = document.getElementById('country-title');
    const fullCountryName = code === 'IN' ? 'India' : 'Malaysia';

    title.innerText = `${fullCountryName} Registry Explorer`;

    // Update active buttons
    const btnIn = document.getElementById('btn-in');
    const btnMy = document.getElementById('btn-my');
    if (btnIn) {
        btnIn.classList.toggle('border-blue-500', code === 'IN');
        btnIn.classList.toggle('bg-blue-50', code === 'IN');
    }
    if (btnMy) {
        btnMy.classList.toggle('border-blue-500', code === 'MY');
        btnMy.classList.toggle('bg-blue-50', code === 'MY');
    }

    // Update global state if requested
    if (updateGlobal && typeof CountryState !== 'undefined') {
        CountryState.set(code);
    }

    await loadCountryData();
}

let asnCache = new Map();

async function loadCountryData() {
    const tbody = document.getElementById('isp-table-body');
    const cacheKey = `${currentCountry}_${currentFilter}`;

    // Performance Guardrail: Check local cache first
    if (asnCache.has(cacheKey)) {
        console.log(`Loading ${cacheKey} from Performance Cache`);
        fullISPData = asnCache.get(cacheKey);
        renderISPAndInitialize();
        return;
    }

    // Loading State
    tbody.innerHTML = `
        <tr class="animate-pulse">
            <td colspan="5" class="py-10 text-center text-slate-300 font-bold italic uppercase tracking-widest">Querying Integrated BGP Registry...</td>
        </tr>
    `;

    try {
        const response = await fetch(`/api/asn?country=${currentCountry}&filter=${currentFilter}`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);

        fullISPData = await response.json();
        console.log(`Loaded ${fullISPData.length} ASNs for ${currentCountry}`);

        if (!Array.isArray(fullISPData)) {
            throw new Error("API did not return a valid list of ASNs");
        }

        // Cache the result
        asnCache.set(cacheKey, fullISPData);
        renderISPAndInitialize();

    } catch (e) {
        console.error("ASN Lookup Failed:", e);
        tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-red-400 font-bold">
            <p>Failed to connect to Intelligence Layer.</p>
            <p class="text-[10px] mt-2 text-slate-400 font-mono">${e.message}</p>
        </td></tr>`;
    }
}

function renderISPAndInitialize() {
    filteredISPData = null;
    currentISPPage = 1;
    renderISPTable(fullISPData);
    updateFilterUI();
    fetchBenchmarks();
}

function renderISPTable(data) {
    const tbody = document.getElementById('isp-table-body');
    const totalPages = Math.ceil(data.length / ISP_PER_PAGE);

    if (currentISPPage > totalPages) currentISPPage = 1;

    tbody.innerHTML = '';

    const start = (currentISPPage - 1) * ISP_PER_PAGE;
    const end = start + ISP_PER_PAGE;
    const pageData = data.slice(start, end);

    if (pageData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="py-10 text-center text-slate-400">No ASN records found matching query.</td></tr>`;
        return;
    }

    pageData.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition group isp-row cursor-pointer";
        tr.onclick = () => openISPModal(item);

        // Data is now guaranteed from Registry/CAIDA
        const orgName = item.org_name || 'Unknown (Registry)';
        const ipv6Score = item.ipv6_percentage !== null ? `${item.ipv6_percentage}%` : '---';
        const ipv6Width = item.ipv6_percentage || 0;

        // BGP Resilience
        const bgp = item.bgp_resilience || { upstream_count: 0, score: 0, status: 'Unknown' };
        const resilColor = bgp.score >= 60 ? 'text-emerald-600' : (bgp.score >= 10 ? 'text-amber-600' : 'text-red-600');

        const verificationBadge = `<span class="inline-flex items-center gap-1.5 bg-indigo-50 text-indigo-600 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border border-indigo-100">
                <span class="w-1 h-1 bg-indigo-500 rounded-full"></span> Registry Verified
               </span>`;

        tr.innerHTML = `
            <td class="py-5">
                <span class="text-xs font-black text-slate-400 bg-slate-100 px-2 py-1 rounded-lg">AS${item.asn}</span>
            </td>
            <td class="py-5">
                <p class="text-sm font-black text-slate-900">${orgName}</p>
                <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Source: ${item.data_source || 'Local Registry'}</p>
            </td>
            <td class="py-5">
                <div class="flex items-center gap-3">
                    <span class="text-lg font-black text-slate-700 font-mono">${ipv6Score}</span>
                    <div class="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div class="h-full ${ipv6Width > 50 ? 'bg-emerald-500' : 'bg-blue-500'} w-0 transition-all duration-1000" style="width: ${ipv6Width}%"></div>
                    </div>
                </div>
            </td>
            <td class="py-5">
                <div class="flex flex-col">
                    <span class="text-xs font-black ${resilColor}">${bgp.status}</span>
                    <span class="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">${bgp.upstream_count} Upstreams</span>
                </div>
            </td>
            <td class="py-5">
                ${verificationBadge}
                <p class="text-[8px] font-medium text-slate-400 mt-1 uppercase tracking-tighter">
                   APNIC Labs Data
                </p>
            </td>
        `;
        tbody.appendChild(tr);
    });

    renderISPPagination(totalPages);
}

function renderISPPagination(total) {
    let controls = document.getElementById('isp-pagination');
    if (!controls) {
        controls = document.createElement('div');
        controls.id = 'isp-pagination';
        controls.className = "flex justify-center items-center gap-4 py-8 border-t border-slate-50";
        document.getElementById('isp-table-body').parentNode.parentNode.appendChild(controls);
    }

    controls.innerHTML = `
        <button onclick="changeISPPage(-1)" ${currentISPPage === 1 ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-30 transition">Previous</button>
        <span class="text-xs font-black text-slate-400">Page ${currentISPPage} of ${total}</span>
        <button onclick="changeISPPage(1)" ${currentISPPage === total ? 'disabled' : ''} class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold uppercase tracking-wider disabled:opacity-30 transition">Next</button>
    `;
}

function changeISPPage(delta) {
    currentISPPage += delta;
    renderISPTable(filteredISPData || fullISPData);
    document.getElementById('isp-table-body').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleISPSearch() {
    const query = document.getElementById('isp-search').value.toLowerCase();

    if (!query) {
        filteredISPData = null;
        currentISPPage = 1;
        renderISPTable(fullISPData);
        return;
    }

    filteredISPData = fullISPData.filter(item =>
        (item.org_name && item.org_name.toLowerCase().includes(query)) ||
        item.asn.toString().includes(query) ||
        (item.asn_name && item.asn_name.toLowerCase().includes(query))
    );

    currentISPPage = 1;
    renderISPTable(filteredISPData);
}

function applyASNFilter(type) {
    currentFilter = type;
    loadCountryData();
}

function updateFilterUI() {
    const btnAll = document.getElementById('filter-all');
    const btnTop = document.getElementById('filter-top');

    if (!btnAll || !btnTop) return;

    btnAll.className = `px-3 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition ${currentFilter === 'all' ? 'bg-blue-600 text-white' : 'hover:bg-slate-50 text-slate-500'}`;
    btnTop.className = `px-3 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition ${currentFilter === 'top_performers' ? 'bg-blue-600 text-white' : 'hover:bg-slate-50 text-slate-500'}`;
}

function openISPModal(item) {
    const modal = document.getElementById('isp-modal');
    document.getElementById('modal-org-name').innerText = item.org_name || 'Unknown ISP';
    document.getElementById('modal-asn').innerText = `AS${item.asn} • ${item.country}`;
    document.getElementById('modal-readiness').innerText = item.ipv6_percentage ? `${item.ipv6_percentage}%` : '---';
    document.getElementById('modal-rir').innerText = item.rir || 'APNIC';

    // BGP Resilience
    const bgp = item.bgp_resilience || { upstream_count: 0, score: 0, status: 'Unknown' };
    document.getElementById('modal-resilience').innerText = bgp.score;

    // Fetch Detailed Upstreams
    loadUpstreamDetails(item.asn);

    modal.classList.replace('hidden', 'flex');
}

async function loadUpstreamDetails(asn) {
    const list = document.getElementById('modal-upstream-list');
    list.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase mb-3">Upstream Infrastructure</p>
                      <div class="animate-pulse space-y-2">
                        <div class="h-8 bg-slate-50 rounded-xl"></div>
                        <div class="h-8 bg-slate-50 rounded-xl"></div>
                      </div>`;

    try {
        const response = await fetch(`/api/asn/bgp?asn=${asn}`);
        const data = await response.json();

        if (data.upstreams && data.upstreams.length > 0) {
            list.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase mb-3">Upstream Infrastructure (${data.upstreams.length})</p>
                              <div class="grid grid-cols-1 gap-2">
                                ${data.upstreams.map(u => `
                                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                                        <div class="flex items-center gap-3">
                                            <span class="text-[10px] font-black text-blue-600 bg-blue-50 px-2 py-1 rounded-lg">AS${u.asn}</span>
                                            <span class="text-xs font-bold text-slate-700 truncate max-w-[200px]">${u.org_name || 'Unknown Peer'}</span>
                                        </div>
                                        <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">${u.source || 'BGP Feed'}</span>
                                    </div>
                                `).join('')}
                              </div>`;
        } else {
            list.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase mb-3">Upstream Infrastructure</p>
                              <div class="p-4 bg-orange-50 rounded-xl border border-orange-100 text-center">
                                <p class="text-xs font-bold text-orange-600 italic">No upstream providers found (Stub / Edge AS)</p>
                              </div>`;
        }
    } catch (e) {
        list.innerHTML = '<p class="text-xs text-red-500 font-bold">Failed to load topology data.</p>';
    }
}

function closeISPModal() {
    document.getElementById('isp-modal').classList.replace('flex', 'hidden');
}

function openSubmissionModal() {
    const modal = document.getElementById('submission-modal');
    document.getElementById('submission-form').classList.remove('hidden');
    document.getElementById('sub-loading').classList.add('hidden');
    document.getElementById('sub-success').classList.add('hidden');
    modal.classList.replace('hidden', 'flex');
}

function closeSubmissionModal() {
    document.getElementById('submission-modal').classList.replace('flex', 'hidden');
}

async function handleContribution(event) {
    event.preventDefault();

    const domain = document.getElementById('sub-domain').value;
    const sector = document.getElementById('sub-sector').value;
    const country = document.getElementById('sub-country').value;

    const form = document.getElementById('submission-form');
    const loading = document.getElementById('sub-loading');
    const success = document.getElementById('sub-success');
    const resultText = document.getElementById('sub-result-text');

    form.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const response = await fetch('/api/analytics/community/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, sector, country })
        });

        const data = await response.json();

        if (response.ok) {
            loading.classList.add('hidden');
            success.classList.remove('hidden');

            const scan = data.details || {};
            const status = (scan.ipv6_web && scan.ipv6_dns) ? 'IPv6 READY' : (scan.ipv6_dns ? 'PARTIAL IPv6' : 'IPv4 ONLY');
            resultText.innerText = `${domain} audit complete: ${status}. Successfully indexed in the community registry.`;
        } else {
            alert(data.error || "Submission failed.");
            form.classList.remove('hidden');
            loading.classList.add('hidden');
        }
    } catch (e) {
        console.error("Submission Error:", e);
        alert("Server communication error. Please try again later.");
        form.classList.remove('hidden');
        loading.classList.add('hidden');
    }
}

async function fetchBenchmarks() {
    try {
        const response = await fetch(`/api/analytics/peer-benchmarks?country=${currentCountry}`);
        const data = await response.json();

        renderBenchmarkChart(data);

        // Update Gap Indicator
        const gapIndicator = document.getElementById('gap-indicator');
        const gapText = document.getElementById('gap-text');
        const insightText = document.getElementById('bench-insight');

        if (gapIndicator && gapText) {
            gapIndicator.classList.remove('hidden');
            gapText.innerText = `Adoption Gap: ${data.gap_index}%`;

            if (data.gap_index > 20) {
                insightText.innerText = `Strategic Gap: Academic sector lags ${data.gap_index}% behind National ISPs. Focus on University upgrades needed.`;
            } else {
                insightText.innerText = `Parity Achieved: Academic sector is sync with National adoption rates (${data.academic_avg}%).`;
            }
        }
    } catch (e) {
        console.error("Benchmark Fetch failed:", e);
    }
}

function renderBenchmarkChart(data) {
    const options = {
        series: [{
            name: 'IPv6 Adoption (%)',
            data: [data.national_isp_avg, data.academic_avg, data.government_avg]
        }],
        chart: {
            type: 'bar',
            height: 250,
            toolbar: { show: false },
            animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        plotOptions: {
            bar: {
                borderRadius: 12,
                columnWidth: '55%',
                distributed: true,
                dataLabels: { position: 'top' }
            }
        },
        colors: ['#2563eb', '#6366f1', '#10b981'],
        dataLabels: {
            enabled: true,
            formatter: (val) => val + "%",
            offsetY: -20,
            style: { fontSize: '10px', colors: ["#304758"], fontWeight: '900' }
        },
        legend: { show: false },
        xaxis: {
            categories: ['National ISPs', 'Academic Sector', 'Gov Portals'],
            labels: { style: { fontWeight: '800', fontSize: '10px', colors: '#94a3b8' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: { show: false, max: 100 },
        grid: { show: false }
    };

    if (benchmarkChart) {
        benchmarkChart.updateOptions(options);
    } else {
        benchmarkChart = new ApexCharts(document.querySelector("#benchmark-chart"), options);
        benchmarkChart.render();
    }
}
