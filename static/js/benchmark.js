let adoptionChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    await populateSelectors();
});

async function populateSelectors() {
    try {
        const response = await fetch('/gov-monitor/api/stats');
        const data = await response.json();
        const ranking = data.ranking || [];

        const s1 = document.getElementById('entity1-select');
        const s2 = document.getElementById('entity2-select');

        // Sort ranking alphabetically by full_name
        ranking.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));

        ranking.forEach(item => {
            const opt1 = new Option(item.full_name, item.country);
            const opt2 = new Option(item.full_name, item.country);
            s1.add(opt1);
            s2.add(opt2);
        });

        // Set defaults
        if (ranking.length >= 2) {
            s1.value = ranking[0].country;
            s2.value = ranking[3] ? ranking[3].country : ranking[1].country; // Just some variance
        }
    } catch (error) {
        console.error("Failed to populate country selectors:", error);
    }
}

async function runComparison() {
    const id1 = document.getElementById('entity1-select').value;
    const id2 = document.getElementById('entity2-select').value;

    if (!id1 || !id2) return;

    // Show view, hide empty state
    document.getElementById('benchmark-view').classList.remove('hidden');
    document.getElementById('benchmark-empty').classList.add('hidden');

    try {
        const response = await fetch(`/gov-monitor/api/benchmark/compare?id1=${id1}&id2=${id2}`);
        const data = await response.json();

        updateEntityColumn(1, data.entity1);
        updateEntityColumn(2, data.entity2);
        updateDetailedTable(data.entity1, data.entity2);
        renderAdoptionChart(data.entity1, data.entity2);

    } catch (error) {
        console.error("Comparison failed:", error);
    }
}

function updateEntityColumn(index, data) {
    document.getElementById(`e${index}-id`).innerText = data.id;
    document.getElementById(`e${index}-name`).innerText = data.country_name;
    document.getElementById(`e${index}-score`).innerText = Math.round(data.domain_readiness);
    document.getElementById(`e${index}-adoption`).innerText = data.national_adoption + '%';

    // Update Adoption Bar
    const adoptionBar = document.getElementById(`e${index}-adoption-bar`);
    if (adoptionBar) {
        adoptionBar.style.width = data.national_adoption + '%';
    }

    const badge = document.getElementById(`e${index}-rank-badge`);
    badge.innerText = `Rank #${data.rank}`;

    // Gauge Logic
    const gauge = document.getElementById(`e${index}-gauge`);
    const circumference = 502.65; // 2 * Math.PI * 80
    const offset = circumference - (data.domain_readiness / 100) * circumference;
    gauge.style.strokeDashoffset = offset;

    // Sync Level
    const syncEl = document.getElementById(`e${index}-gov-sync`);
    const diff = Math.abs(data.domain_readiness - data.national_adoption);
    if (diff < 15) {
        syncEl.innerText = "High Correlation";
        syncEl.className = "text-2xl font-black text-emerald-600";
    } else if (diff < 30) {
        syncEl.innerText = "Moderate Lag";
        syncEl.className = "text-2xl font-black text-amber-600";
    } else {
        syncEl.innerText = "Deployment Gap";
        syncEl.className = "text-2xl font-black text-rose-600";
    }
}

function updateDetailedTable(e1, e2) {
    const metrics = [
        { key: 'missing_dns_pct', e1Id: 'e1-dns', e2Id: 'e2-dns' },
        { key: 'web_unreachable_pct', e1Id: 'e1-web', e2Id: 'e2-web' },
        { key: 'missing_dnssec_pct', e1Id: 'e1-sec', e2Id: 'e2-sec' }
    ];

    metrics.forEach(m => {
        // We show adoption (100 - failure %)
        const val1 = 100 - (e1.breakdown[m.key] || 0);
        const val2 = 100 - (e2.breakdown[m.key] || 0);

        document.getElementById(`${m.e1Id}-progress`).style.width = val1 + '%';
        document.getElementById(`${m.e1Id}-val`).innerText = val1 + '%';

        document.getElementById(`${m.e2Id}-progress`).style.width = val2 + '%';
        document.getElementById(`${m.e2Id}-val`).innerText = val2 + '%';
    });
}

function renderAdoptionChart(e1, e2) {
    const options = {
        series: [
            {
                name: 'AI Domain Readiness',
                data: [Math.round(e1.domain_readiness), Math.round(e2.domain_readiness)]
            },
            {
                name: 'National Adoption (%)',
                data: [e1.national_adoption, e2.national_adoption]
            }
        ],
        chart: {
            type: 'bar',
            height: 350,
            toolbar: { show: false },
            animations: { enabled: true, easing: 'easeinout', speed: 800 },
            fontFamily: 'inherit'
        },
        plotOptions: {
            bar: {
                borderRadius: 8,
                columnWidth: '60%',
                dataLabels: { position: 'top' }
            }
        },
        colors: ['#06b6d4', '#6366f1'],
        dataLabels: {
            enabled: true,
            formatter: (val) => val + "%",
            offsetY: -20,
            style: { fontSize: '10px', fontWeight: '900', colors: ["#64748b"] }
        },
        stroke: {
            show: true,
            width: 4,
            colors: ['transparent']
        },
        legend: { 
            show: true, 
            position: 'top', 
            horizontalAlign: 'right',
            fontFamily: 'inherit',
            fontWeight: 800,
            fontSize: '10px',
            labels: { colors: '#64748b' },
            markers: { radius: 12 }
        },
        xaxis: {
            categories: [e1.country_name, e2.country_name],
            labels: { style: { fontWeight: '900', fontSize: '11px', colors: '#1e293b' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: { 
            show: true, 
            max: 100,
            labels: { style: { fontWeight: '700', fontSize: '10px', colors: '#94a3b8' } }
        },
        grid: { 
            show: true, 
            borderColor: '#f1f5f9',
            strokeDashArray: 4,
            xaxis: { lines: { show: false } }
        },
        tooltip: { theme: 'light', y: { formatter: (val) => val + "%" } }
    };

    if (adoptionChart) {
        adoptionChart.updateOptions(options);
    } else {
        const chartEl = document.querySelector("#national-adoption-chart");
        if (chartEl) {
            adoptionChart = new ApexCharts(chartEl, options);
            adoptionChart.render();
        }
    }
}
