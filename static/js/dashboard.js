/**
 * Dashboard Synchronization Logic
 * Listens for the global 'countryChanged' event and updates the UI accordingly.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized with Global Sync support');

    // [GLOBAL SYNC] Listen for country changes
    window.addEventListener('countryChanged', (e) => {
        const countryCode = e.detail.country;
        refreshDashboardData(countryCode);
    });

    /**
     * Fetches fresh data for the selected country and updates the DOM.
     * @param {string} country 
     */
    async function refreshDashboardData(country) {
        try {
            let rate = 0;
            let label = `Live: ${country}`;

            if (country === 'APAC') {
                // Fetch all stats and calculate average
                const response = await fetch('/lab/api/apac/all_stats');
                if (!response.ok) throw new Error('Failed to fetch aggregate stats');
                const allStats = await response.json();

                const statsArray = Object.values(allStats);
                if (statsArray.length > 0) {
                    const totalAdoption = statsArray.reduce((acc, s) => acc + (s.ipv6_adoption || 0), 0);
                    rate = totalAdoption / statsArray.length;
                }
                label = "Live: APAC Region";
            } else {
                // Fetch specific country stats
                const response = await fetch(`/lab/api/apac/ipv6?country=${country}`);
                if (!response.ok) throw new Error('Failed to fetch country stats');
                const data = await response.json();

                // NEW: prefer AI optimized adoption if available
                rate = data.ai_optimized_rate ?? data.ipv6_adoption ?? 0;

                label = `Live: ${data.country || country}`;
            }

            // Update Adoption Rate
            const rateEl = document.getElementById('dash-adoption-rate');
            if (rateEl) {
                rateEl.textContent = `${rate.toFixed(1)}%`;
            }

            // [NEW] Update AI Metrics (Confidence & Explanation)
            const confidenceEl = document.getElementById('dash-ai-confidence');
            const explanationEl = document.getElementById('dash-ai-explanation');

            if (data.ai_confidence && confidenceEl) {
                confidenceEl.innerText = data.ai_confidence;
                // Color-coding Confidence Levels
                let colorClass = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
                if (data.ai_confidence === 'High') colorClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
                else if (data.ai_confidence === 'Low') colorClass = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
                
                confidenceEl.className = `px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border shadow-lg ${colorClass}`;
            }

            if (data.ai_explanation && explanationEl) {
                explanationEl.textContent = data.ai_explanation;
            }

            // Update Country Label
            const labelEl = document.getElementById('dash-country-label');
            if (labelEl) {
                labelEl.textContent = label;
            }

            // Update Time
            const timeEl = document.getElementById('dash-update-time');
            if (timeEl) {
                timeEl.textContent = 'Updated Just Now';
                timeEl.classList.remove('text-blue-400');
                timeEl.classList.add('text-green-400');
            }

            console.log(`✓ Dashboard updated to ${country}`);

        } catch (error) {
            console.error('❌ Dashboard refresh failed:', error);
        }
    }
});