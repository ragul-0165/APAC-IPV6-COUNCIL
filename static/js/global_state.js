/**
 * Global Country Intelligence Switch - State Manager
 * Handles persistent country selection and synchronizes data across all components.
 */

export const CountryState = {
    // Default country (India) or last selected from persistence
    get() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlCountry = urlParams.get('country');

        if (urlCountry) {
            this.set(urlCountry.toUpperCase(), false); // Set without recursion
            return urlCountry.toUpperCase();
        }

        return localStorage.getItem("selected_country") || "IN";
    },

    set(country, updateUrl = true) {
        if (!country) return;

        const countryCode = country.toUpperCase();
        localStorage.setItem("selected_country", countryCode);

        // Update URL without page reload
        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.set('country', countryCode);
            window.history.pushState({}, '', url);
        }

        // Broadcast the change to all listeners
        window.dispatchEvent(new CustomEvent("countryChanged", {
            detail: {
                country: countryCode
            }
        }));
    }
};

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
    const initialCountry = CountryState.get();
    // Dispatch initial event to trigger data loads
    window.dispatchEvent(new CustomEvent("countryChanged", {
        detail: {
            country: initialCountry
        }
    }));
});

// For backward compatibility with legacy scripts
window.CountryState = CountryState;
