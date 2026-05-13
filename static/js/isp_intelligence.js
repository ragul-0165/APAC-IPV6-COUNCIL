let currentCountry = 'IN';
let currentISPPage = 1;
const ISP_PER_PAGE = 25;
let currentFilter = 'all';
let isVerifying = false;
let benchmarkChart = null;
let totalISPPages = 1;
let totalISPRecords = 0;
let searchDebounceTimer = null;
let currentSearchQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    // [GLOBAL SYNC] Initialize based on global state
    const currentGlobalCountry = (typeof CountryState !== 'undefined') ? CountryState.get() : 'IN';

    loadStats();

    // Check if the current country is supported by the ISP explorer (currently IN/MY/ID)
    if (['IN', 'MY', 'ID'].includes(currentGlobalCountry)) {
        switchISPCountry(currentGlobalCountry, false);
    } else {
        switchISPCountry('IN', false); // Default to India for ISP view if global is unsupported
    }

    // [GLOBAL SYNC] Listen for region changes
    window.addEventListener('countryChanged', (e) => {
        const newCountry = e.detail.country;
        if (['IN', 'MY', 'ID'].includes(newCountry) && newCountry !== currentCountry) {
            switchISPCountry(newCountry, false);
        } else if (!['IN', 'MY', 'ID'].includes(newCountry)) {
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
        const idStat = document.getElementById('stat-count-id');
        if (inStat) inStat.innerText = `${stats.india_count.toLocaleString()} ASNs`;
        if (myStat) myStat.innerText = `${stats.malaysia_count.toLocaleString()} ASNs`;
        if (idStat) idStat.innerText = `${stats.indonesia_count.toLocaleString()} ASNs`;

        // Update Sidebar Badges
        const inBadge = document.getElementById('badge-count-in');
        const myBadge = document.getElementById('badge-count-my');
        const idBadge = document.getElementById('badge-count-id');
        if (inBadge) inBadge.innerText = `${stats.india_count.toLocaleString()} ASNs`;
        if (myBadge) myBadge.innerText = `${stats.malaysia_count.toLocaleString()} ASNs`;
        if (idBadge) idBadge.innerText = `${stats.indonesia_count.toLocaleString()} ASNs`;

    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

async function switchISPCountry(code, updateGlobal = true) {
    currentCountry = code;
    currentFilter = 'all'; // Reset filter on country switch
    currentISPPage = 1; // Reset page on country switch
    currentSearchQuery = ''; // Reset search on country switch
    const searchInput = document.getElementById('isp-search');
    if (searchInput) searchInput.value = '';
    
    const title = document.getElementById('country-title');
    
    let fullCountryName = 'India';
    if (code === 'MY') fullCountryName = 'Malaysia';
    if (code === 'ID') fullCountryName = 'Indonesia';

    title.innerText = `${fullCountryName} Registry Explorer`;

    // Update active buttons
    const btnIn = document.getElementById('btn-in');
    const btnMy = document.getElementById('btn-my');
    const btnId = document.getElementById('btn-id');
    if (btnIn) {
        btnIn.classList.toggle('border-blue-500', code === 'IN');
        btnIn.classList.toggle('bg-blue-50', code === 'IN');
    }
    if (btnMy) {
        btnMy.classList.toggle('border-blue-500', code === 'MY');
        btnMy.classList.toggle('bg-blue-50', code === 'MY');
    }
    if (btnId) {
        btnId.classList.toggle('border-blue-500', code === 'ID');
        btnId.classList.toggle('bg-blue-50', code === 'ID');
    }

    // Update global state if requested
    if (updateGlobal && typeof CountryState !== 'undefined') {
        CountryState.set(code);
    }

    await loadCountryData();
}

async function loadCountryData() {
    const tbody = document.getElementById('isp-table-body');

    // Loading State
    tbody.innerHTML = `
        <tr class="animate-pulse">
            <td colspan="5" class="py-10 text-center text-slate-300 font-bold italic uppercase tracking-widest">Querying Integrated BGP Registry...</td>
        </tr>
    `;

    try {
        // Build URL with server-side pagination params
        let url = `/api/asn?country=${currentCountry}&filter=${currentFilter}&page=${currentISPPage}&per_page=${ISP_PER_PAGE}`;
        if (currentSearchQuery) {
            url += `&search=${encodeURIComponent(currentSearchQuery)}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);

        const result = await response.json();
        
        // Server now returns {data: [...], total: N, page: N, per_page: N, total_pages: N}
        const pageData = result.data || [];
        totalISPRecords = result.total || 0;
        totalISPPages = result.total_pages || 1;
        currentISPPage = result.page || 1;

        console.log(`Loaded page ${currentISPPage}/${totalISPPages} (${pageData.length} of ${totalISPRecords} ASNs) for ${currentCountry}`);

        renderISPTable(pageData);
        updateFilterUI();
        fetchBenchmarks();

    } catch (e) {
        console.error("ASN Lookup Failed:", e);
        tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-red-400 font-bold">
            <p>Failed to connect to Intelligence Layer.</p>
            <p class="text-[10px] mt-2 text-slate-400 font-mono">${e.message}</p>
        </td></tr>`;
    }
}

function renderISPTable(pageData) {
    const tbody = document.getElementById('isp-table-body');
    tbody.innerHTML = '';

    if (pageData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="py-10 text-center text-slate-400">No ASN records found matching query.</td></tr>`;
        renderISPPagination();
        return;
    }

    pageData.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-white/5 transition group isp-row cursor-pointer";
        tr.onclick = () => openISPModal(item);

        const orgName = item.org_name || 'Unknown (Registry)';
        const ipv6Score = item.ipv6_percentage !== null ? `${item.ipv6_percentage}%` : '---';
        const ipv6Width = item.ipv6_percentage || 0;

        const bgp = item.bgp_resilience || { upstream_count: 0, score: 0, status: 'Unknown' };
        const resilColor = bgp.score >= 60 ? 'text-emerald-400' : (bgp.score >= 10 ? 'text-amber-400' : 'text-rose-400');

        const verificationBadge = `<span class="inline-flex items-center gap-1.5 bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border border-blue-500/20">
                <span class="w-1 h-1 bg-blue-400 rounded-full"></span> Registry Verified
               </span>`;

        tr.innerHTML = `
            <td class="p-6">
                <span class="text-xs font-black text-slate-500 bg-white/5 px-2 py-1 rounded-lg">AS${item.asn}</span>
            </td>
            <td class="p-6">
                <p class="text-sm font-black text-white">${orgName}</p>
                <p class="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">Source: ${item.data_source || 'Local Registry'}</p>
            </td>
            <td class="p-6">
                <div class="flex items-center gap-3">
                    <span class="text-lg font-black text-slate-300 font-mono">${ipv6Score}</span>
                    <div class="w-20 h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div class="h-full ${ipv6Width > 50 ? 'bg-emerald-500' : 'bg-blue-500'} transition-all duration-1000" style="width: ${ipv6Width}%"></div>
                    </div>
                </div>
            </td>
            <td class="p-6">
                <div class="flex flex-col">
                    <span class="text-xs font-black ${resilColor}">${bgp.status}</span>
                    <span class="text-[9px] font-bold text-slate-500 uppercase tracking-tighter">${bgp.upstream_count} Upstreams</span>
                </div>
            </td>
            <td class="p-6">
                ${verificationBadge}
            </td>
        `;
        tbody.appendChild(tr);
    });

    renderISPPagination();
}

function renderISPPagination() {
    let controls = document.getElementById('isp-pagination');
    if (!controls) {
        controls = document.createElement('div');
        controls.id = 'isp-pagination';
        controls.className = "flex justify-center items-center gap-4 py-8 border-t border-white/5 bg-white/5";
        document.getElementById('isp-table-body').parentNode.parentNode.appendChild(controls);
    }

    controls.innerHTML = `
        <button onclick="changeISPPage(-1)" ${currentISPPage === 1 ? 'disabled' : ''} class="px-4 py-2 bg-slate-900 border border-white/10 hover:bg-white/5 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-300 disabled:opacity-30 transition">Previous</button>
        <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest px-4">Page ${currentISPPage} / ${totalISPPages} (${totalISPRecords} total)</span>
        <button onclick="changeISPPage(1)" ${currentISPPage >= totalISPPages ? 'disabled' : ''} class="px-4 py-2 bg-slate-900 border border-white/10 hover:bg-white/5 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-300 disabled:opacity-30 transition">Next</button>
    `;
}

function changeISPPage(delta) {
    const newPage = currentISPPage + delta;
    if (newPage < 1 || newPage > totalISPPages) return;
    currentISPPage = newPage;
    loadCountryData();
    document.getElementById('isp-table-body').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleISPSearch() {
    const query = document.getElementById('isp-search').value.trim();

    // Debounce: wait 300ms after user stops typing before querying
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        currentSearchQuery = query;
        currentISPPage = 1; // Reset to page 1 on new search
        loadCountryData();
    }, 300);
}

function applyASNFilter(type) {
    currentFilter = type;
    currentISPPage = 1; // Reset to page 1 on filter change
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
        yaxis: { 
            show: false, 
            max: 100 
        },
        grid: { 
            show: true,
            borderColor: 'rgba(255,255,255,0.05)',
            strokeDashArray: 4,
            yaxis: {
                lines: { show: true }
            }
        }
    };

    if (benchmarkChart) {
        benchmarkChart.updateOptions(options);
    } else {
        benchmarkChart = new ApexCharts(document.querySelector("#benchmark-chart"), options);
        benchmarkChart.render();
    }
}
