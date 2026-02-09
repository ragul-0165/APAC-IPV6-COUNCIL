document.getElementById('domain-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const domains = document.getElementById('domains').value;
    const status = document.getElementById('domain-status');
    const resultsSection = document.getElementById('results-section');
    const resultsTable = document.getElementById('domain-results');

    status.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    resultsTable.innerHTML = '';

    try {
        const response = await fetch('/domains/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domains })
        });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        data.domain_data.forEach(item => {
            const row = document.createElement('tr');
            row.className = "hover:bg-blue-50/30 transition group";
            row.innerHTML = `
                <td class="px-8 py-6">
                    <div class="flex flex-col">
                        <span class="text-sm font-black text-slate-800 font-display">${item.domain}</span>
                        <span class="text-[9px] font-bold text-gray-400 uppercase tracking-tighter mt-1">Audit Log: ${item.timestamp}</span>
                    </div>
                </td>
                <td class="px-8 py-6">
                    <div class="flex items-center justify-center gap-6">
                        <div class="flex flex-col items-center">
                            <div class="w-8 h-8 rounded-xl flex items-center justify-center ${item.ipv6 !== 'None' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-300'} mb-1 border ${item.ipv6 !== 'None' ? 'border-emerald-100' : 'border-slate-100'}">
                                <span class="text-[10px] font-black">v6</span>
                            </div>
                            <span class="text-[8px] font-black uppercase text-gray-400">${item.ipv6 !== 'None' ? 'Active' : 'Missing'}</span>
                        </div>
                        <div class="flex flex-col items-center">
                            <div class="w-8 h-8 rounded-xl flex items-center justify-center ${item.ipv4 !== 'None' ? 'bg-blue-50 text-blue-600' : 'bg-slate-50 text-slate-300'} mb-1 border ${item.ipv4 !== 'None' ? 'border-blue-100' : 'border-slate-100'}">
                                <span class="text-[10px] font-black">v4</span>
                            </div>
                            <span class="text-[8px] font-black uppercase text-gray-400">Legacy</span>
                        </div>
                    </div>
                </td>
                <td class="px-8 py-6">
                    <div class="space-y-1">
                        <div class="flex items-center gap-2">
                             <div class="w-2 h-2 rounded-full ${item.tls_issuer !== 'Unknown' ? 'bg-emerald-500' : 'bg-amber-400'}"></div>
                             <span class="text-xs font-bold text-slate-700">${item.tls_issuer}</span>
                        </div>
                        <p class="text-[10px] font-medium text-gray-400">Expires: ${item.tls_expiry}</p>
                    </div>
                </td>
                <td class="px-8 py-6">
                    <div class="flex flex-col">
                        <span class="text-xs font-bold text-slate-800 truncate max-w-[150px]">${item.hosting_company}</span>
                        <div class="inline-flex items-center gap-1.5 mt-1">
                            <span class="w-3 h-2 rounded-sm bg-slate-200"></span>
                            <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">${item.hosting_location}</span>
                        </div>
                    </div>
                </td>
                <td class="px-8 py-6 text-right">
                    <span class="inline-flex items-center px-4 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-[0.1em] ${item.dnssec === 'signed' ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' : 'bg-slate-100 text-slate-400'}">
                        ${item.dnssec === 'signed' ? 'DNSSEC' : 'Insecure'}
                    </span>
                </td>
            `;
            resultsTable.appendChild(row);
        });

        // Update Visualizations (Intelligence-Grade Recon Suite)
        const vizGrid = document.getElementById('visualizations-grid');
        vizGrid.innerHTML = '';

        const reconMeta = {
            'relationship_map': {
                title: 'Infrastructure Relationship Map',
                desc: 'Derived host-to-endpoint structure based on scan observations.',
                finding: 'Analyzes the multi-layered connection between scan nodes and resolved protocol endpoints. High density indicates a robust hosting backbone.'
            },
            'recon_flow': {
                title: 'Recon Flow Analytics',
                desc: 'Conversion analysis from batch fleet to secure protocol endpoints.',
                finding: 'Identifies the fallout rate of domains as they pass through IPv6 and DNSSEC filters. A steep drop-off indicates legacy infrastructure debt.'
            },
            'fleet_profile': {
                title: 'Security Fleet Profile',
                desc: 'Comprehensive strength audit across 5 technical axes.',
                finding: 'Evaluates global resilience. Gaps in the hexagon reveal specific weaknesses in geo-diversity or protocol implementation across the fleet.'
            },
            'infrastructure_density': {
                title: 'Global Infrastructure Density',
                desc: 'Stylized geographic concentration of hosting endpoints.',
                finding: 'Visualizes geopolitical infrastructure concentrations. High density in single regions increases risk of regional technical blackouts.'
            }
        };

        if (data.graphs && data.graphs.length > 0) {
            data.graphs.forEach((url) => {
                const card = document.createElement('div');
                card.className = "bg-slate-900 p-8 rounded-[2.5rem] border border-slate-800 shadow-2xl overflow-hidden group hover:border-blue-500/50 transition-all duration-700 relative cursor-pointer active:scale-[0.98]";

                const filename = url.split('/').pop().split('?')[0].replace('.png', '');
                const meta = reconMeta[filename] || { title: filename.replace(/_/g, ' '), desc: 'Advanced infrastructure telemetry data.', finding: 'No specific anomalies detected in this dataset.' };

                card.onclick = () => openIntelligenceModal(url, meta);

                card.innerHTML = `
                    <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[80px] rounded-full"></div>
                    <div class="relative z-10 text-left">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="text-xs font-black text-blue-400 uppercase tracking-[0.2em] group-hover:text-blue-300 transition">${meta.title}</h4>
                            <svg class="w-4 h-4 text-slate-700 group-hover:text-blue-500 transition-all transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                            </svg>
                        </div>
                        <p class="text-[10px] font-medium text-slate-500 mb-6 leading-relaxed">${meta.desc}</p>
                        <div class="aspect-video bg-black/40 rounded-3xl flex items-center justify-center overflow-hidden border border-slate-800/50 shadow-inner group-hover:bg-black/20 transition-all duration-700">
                            <img src="${url}" alt="${meta.title}" class="w-full h-full object-contain group-hover:scale-105 transition duration-1000">
                        </div>
                    </div>
                `;
                vizGrid.appendChild(card);
            });
        }

        resultsSection.classList.remove('hidden');
    } catch (error) {
        alert('Analysis failed: ' + error.message);
    } finally {
        status.classList.add('hidden');
    }
});

// Modal Logic
function openIntelligenceModal(url, meta) {
    const modal = document.getElementById('intelligence-modal');
    const image = document.getElementById('modal-image');
    const title = document.getElementById('modal-title');
    const desc = document.getElementById('modal-desc');
    const finding = document.getElementById('modal-finding');

    image.src = url;
    title.innerText = meta.title;
    desc.innerText = meta.desc;
    finding.innerText = meta.finding;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden'; // Prevent scroll
}

function closeIntelligenceModal() {
    const modal = document.getElementById('intelligence-modal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.body.style.overflow = ''; // Restore scroll
}

// Close on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeIntelligenceModal();
});
