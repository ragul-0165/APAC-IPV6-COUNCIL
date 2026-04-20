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
            let ai_confidence = "N/A";
            let ai_explanation = "Aggregating regional metrics...";
            let data = {};

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
                ai_confidence = "High";
                ai_explanation = "Regional average derived from 56 measured APAC territories.";
            } else {
                // Fetch specific country stats
                const response = await fetch(`/lab/api/apac/ipv6?country=${country}`);
                if (!response.ok) throw new Error('Failed to fetch country stats');
                data = await response.json();

                rate = data.ipv6_adoption ?? 0;
                label = `Live: ${data.country || country}`;
                ai_confidence = data.ai_confidence || "Medium";
                ai_explanation = data.ai_explanation || "Using optimized adoption model.";
            }

            // Update Adoption Rate
            const rateEl = document.getElementById('dash-adoption-rate');
            if (rateEl) {
                rateEl.textContent = `${rate.toFixed(1)}%`;
            }

            // [NEW] Update AI Metrics (Confidence & Explanation)
            const confidenceEl = document.getElementById('dash-ai-confidence');
            const explanationEl = document.getElementById('dash-ai-explanation');

            if (confidenceEl) {
                confidenceEl.innerText = ai_confidence;
                // Color-coding Confidence Levels
                let colorClass = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
                if (ai_confidence === 'High') colorClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
                else if (ai_confidence === 'Low') colorClass = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
                
                confidenceEl.className = `px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border shadow-lg ${colorClass}`;
            }

            if (explanationEl) {
                explanationEl.textContent = ai_explanation;
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