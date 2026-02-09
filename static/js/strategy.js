document.addEventListener('DOMContentLoaded', () => {
    // Try to load last test result from history to show recommendation
    const history = JSON.parse(localStorage.getItem('ipv6TestHistory') || '[]');
    if (history.length > 0) {
        displayStrategy(history[0]);
    }
    initNATCalculator();
    loadComplianceScorecard();
});

async function loadComplianceScorecard() {
    const tbody = document.getElementById('compliance-table-body');
    if (!tbody) return;

    try {
        const response = await fetch('/strategy/api/compliance');
        const data = await response.json();

        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-slate-400 font-bold uppercase tracking-widest">No policy mandates indexed for this region.</td></tr>`;
            return;
        }

        data.forEach(m => {
            const tr = document.createElement('tr');
            tr.className = "group hover:bg-slate-50/50 transition duration-300";

            const gapColor = m.gap >= 0 ? 'text-emerald-500' : (m.gap >= -20 ? 'text-amber-500' : 'text-red-500');
            const statusBg = m.status === 'Compliant' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : (m.status === 'On Track' ? 'bg-blue-50 text-blue-600 border-blue-100' : 'bg-rose-50 text-rose-600 border-rose-100');

            tr.innerHTML = `
                <td class="py-8">
                    <div class="flex items-center gap-3">
                        <img src="https://flagcdn.com/w40/${m.country.toLowerCase()}.png" class="w-8 h-6 rounded shadow-sm">
                        <div>
                            <p class="text-[13px] font-black text-slate-900 uppercase tracking-wider">${m.country}</p>
                            <p class="text-[9px] font-bold text-slate-400 uppercase">Target Year: ${m.deadline}</p>
                        </div>
                    </div>
                </td>
                <td class="py-8">
                    <div class="flex flex-col gap-1">
                        <span class="text-sm font-black text-slate-700">${m.target_pct}% Adoption</span>
                        <div class="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div class="h-full bg-slate-400 w-full opacity-30"></div>
                        </div>
                    </div>
                </td>
                <td class="py-8">
                    <div class="flex flex-col gap-1">
                        <span class="text-sm font-black text-slate-900">${m.current_pct}% Measured</span>
                        <div class="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500 transition-all duration-1000" style="width: ${m.current_pct}%"></div>
                        </div>
                    </div>
                </td>
                <td class="py-8">
                    <div class="flex items-center gap-2 ${gapColor}">
                        <span class="text-lg font-black font-mono">${m.gap > 0 ? '+' : ''}${m.gap}%</span>
                        <svg class="w-4 h-4 ${m.gap >= 0 ? '' : 'rotate-180'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        </svg>
                    </div>
                </td>
                <td class="py-8">
                    <span class="inline-flex px-4 py-1.5 rounded-full border text-[10px] font-black uppercase tracking-widest ${statusBg}">
                        ${m.status}
                    </span>
                    <p class="text-[8px] font-bold text-slate-400 mt-2 uppercase tracking-tighter truncate max-w-[120px] cursor-help" title="${m.source}">
                        Source: ${m.source || 'Verified Policy Doc'}
                    </p>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Compliance fetch failed:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-red-500 font-bold uppercase tracking-widest">Failed to synchronize legislative data.</td></tr>`;
    }
}


function calculateConnectivityScore(data) {
    let score = 0;
    if (data.has_ipv4 || data.ipv4) score += 3;
    if (data.dns_ipv4 || (data.tests && data.tests.dns_ipv4)) score += 1;
    if (data.dns_ipv6 || (data.tests && data.tests.dns_ipv6)) score += 1;
    if (data.has_ipv6 || data.ipv6) score += 2;
    if (data.dual_stack || (data.tests && data.tests.dual_stack)) score += 2;
    if (data.large_packet || (data.tests && data.tests.large_packet)) score += 0.5;
    if (data.dns_over_ipv6 || (data.tests && data.tests.dns_over_ipv6)) score += 0.5;
    return Math.min(10, score);
}

function getStrategyRecommendation(data) {
    const score = calculateConnectivityScore(data);
    const evidence = [];
    const has_ipv6 = data.has_ipv6 || (data.ipv6 && data.ipv6 !== 'None' && data.ipv6 !== 'N/A' && data.ipv6 !== 'Unknown');
    const dns_ipv6 = data.dns_ipv6 || (data.tests && data.tests.dns_ipv6);

    if (!has_ipv6) {
        evidence.push('No IPv6 address detected on current interface');
        return {
            id: 'v4-only',
            title: 'IPv4-Only Network Profile',
            when: 'Standard legacy environment',
            why: 'No IPv6 deployment detected. Focus should be on enabling dual-stack core routing.',
            icon: '⚠️',
            evidence: ['Infrastructure lacks IPv6 routing', 'No IPv6 address assigned', 'DNS IPv6 resolution failed']
        };
    }

    if (score < 8 || !dns_ipv6) {
        return {
            id: 'dual-stack',
            title: 'Dual-Stack Recommended',
            when: 'Mixed compatibility environment',
            why: 'IPv6 is present but not robust enough for a "Mostly" transition. Maintain dual-stack for stability.',
            icon: '⚖️',
            evidence: [`Score: ${score.toFixed(1)}/10`, 'Inconsistent DNS transport', 'Dual-stack parity unconfirmed']
        };
    }

    return {
        id: 'v6-mostly',
        title: 'IPv6-Mostly Recommended',
        when: 'Next-gen ready network',
        why: 'Performance is optimal. You can safely signal IPv6-Mostly (Option 108) to reclaimed IPv4 space.',
        icon: '🚀',
        evidence: [`Excellent Score: ${score.toFixed(1)}/10`, 'Verified DNS over IPv6', 'NAT64/DNS64 candidate']
    };
}

function displayStrategy(data) {
    const rec = getStrategyRecommendation(data);
    const placeholder = document.getElementById('strategy-placeholder');
    const result = document.getElementById('strategy-result');
    const title = document.getElementById('strategy-title');
    const when = document.getElementById('strategy-when');
    const why = document.getElementById('strategy-why');
    const icon = document.getElementById('strategy-icon');
    const evidenceList = document.getElementById('strategy-evidence');

    if (!placeholder || !result) return;

    placeholder.classList.add('hidden');
    result.classList.remove('hidden');

    title.textContent = rec.title;
    when.textContent = rec.when;
    why.textContent = rec.why;
    icon.textContent = rec.icon;

    evidenceList.innerHTML = rec.evidence.map(e => `<li>• ${e}</li>`).join('');
}

// NAT Calculator Logic
function initNATCalculator() {
    const usersInput = document.getElementById('calc-users');
    const trafficInput = document.getElementById('calc-traffic');

    if (!usersInput || !trafficInput) return;

    usersInput.addEventListener('input', (e) => {
        document.getElementById('calc-users-val').innerText = parseInt(e.target.value).toLocaleString();
    });

    trafficInput.addEventListener('input', (e) => {
        document.getElementById('calc-traffic-val').innerText = e.target.value + " Gbps";
    });
}

async function calculateNATImpact() {
    const users = document.getElementById('calc-users').value;
    const traffic = document.getElementById('calc-traffic').value;
    const btn = document.querySelector('button[onclick="calculateNATImpact()"]');
    const results = document.getElementById('calc-results');
    const placeholder = document.getElementById('calc-placeholder');

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="animate-pulse">Analyzing...</span>';
    }

    try {
        const response = await fetch('/api/analytics/nat-calculator', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ users: users, traffic_gbps: traffic })
        });
        const data = await response.json();

        if (data.status === 'success') {
            document.getElementById('res-opex').innerText = "$" + data.annual_cost_usd.toLocaleString();
            document.getElementById('res-capex').innerText = "$" + data.capex_avoidance_usd.toLocaleString();
            document.getElementById('res-asset').innerText = "+" + "$" + data.asset_value_usd.toLocaleString();
            document.getElementById('res-penalty').innerText = `+${data.performance_penalty.latency_added_ms}ms Latency | ${data.performance_penalty.failure_risk_pct} Fail Rate`;

            if (placeholder) placeholder.classList.add('hidden');
            if (results) results.classList.remove('hidden');
        }
    } catch (e) {
        console.error("Calculation failed", e);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span id="calc-btn-text">Calculate Impact</span><svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>';
        }
    }
}
