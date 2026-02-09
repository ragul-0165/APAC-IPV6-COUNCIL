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
            // Use the standardized Lab API which already supports ?country=
            const response = await fetch(`/lab/api/apac/ipv6?country=${country}`);
            if (!response.ok) throw new Error('Failed to fetch country stats');

            const data = await response.json();

            // Update Adoption Rate
            const rateEl = document.getElementById('dash-adoption-rate');
            if (rateEl) {
                const rate = data.ipv6_adoption || 0;
                rateEl.textContent = `${rate.toFixed(1)}%`;
            }

            // Update Country Label
            const labelEl = document.getElementById('dash-country-label');
            if (labelEl) {
                labelEl.textContent = `Live: ${data.country || country}`;
            }

            // Update Time if available (otherwise just say 'Just Now')
            const timeEl = document.getElementById('dash-update-time');
            if (timeEl) {
                // If it's a fresh fetch, we can assume it's current
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
