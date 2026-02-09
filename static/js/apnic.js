function switchApnicTab(tabId) {
    document.querySelectorAll('.apnic-tab-pane').forEach(tab => tab.classList.add('hidden'));
    const target = document.getElementById(`apnic-${tabId}-content`);
    if (target) target.classList.remove('hidden');

    document.querySelectorAll('.apnic-tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-600', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-400');
    });
    const btn = document.getElementById(`${tabId}-tab-btn`);
    if (btn) {
        btn.classList.add('border-blue-600', 'text-blue-600');
        btn.classList.remove('border-transparent', 'text-gray-400');
    }
}

async function lookupApnicResource() {
    const query = document.getElementById('apnic-query').value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('apnic-lookup-results');
    const loadingDiv = document.getElementById('apnic-lookup-loading');

    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    try {
        const response = await fetch('/apnic/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        resultsDiv.innerHTML = `
            <div class="bg-white p-6 rounded-2xl border-l-8 border-blue-600 shadow-lg animate-in slide-in-from-left duration-300">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Resource Identity</p>
                        <p class="text-lg font-mono font-bold text-blue-900">${data.resource || data.query}</p>
                    </div>
                    <div class="space-y-1 md:col-span-2">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Registrant / Organization</p>
                        <p class="text-lg font-bold text-gray-800">${data.organization || 'N/A'}</p>
                    </div>
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Economy / Country</p>
                        <p class="text-sm font-semibold text-gray-700">${data.country || 'N/A'}</p>
                    </div>
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Registration Date</p>
                        <p class="text-sm font-semibold text-gray-700">${data.registration_date || 'N/A'}</p>
                    </div>
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Direct Status</p>
                        <p class="text-sm font-bold text-blue-600 capitalize">${data.status || 'N/A'}</p>
                    </div>
                </div>
                ${data.description ? `
                <div class="mt-6 pt-6 border-t border-gray-50">
                    <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Administrative Remarks</p>
                    <p class="text-sm text-gray-600 italic leading-relaxed">${data.description}</p>
                </div>` : ''}
            </div>
        `;
        resultsDiv.classList.remove('hidden');
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="bg-red-50 p-6 rounded-2xl border border-red-100 flex items-center space-x-4">
                <div class="bg-red-500 text-white p-2 rounded-lg">✕</div>
                <div>
                    <h4 class="font-bold text-red-800">Lookup Interrupted</h4>
                    <p class="text-sm text-red-600">${error.message}</p>
                </div>
            </div>`;
        resultsDiv.classList.remove('hidden');
    } finally {
        loadingDiv.classList.add('hidden');
    }
}

const docDetails = {
    'intro': `
        <h3 class="text-2xl font-black mb-6 text-blue-900">IPv6 Architectural Fundamentals</h3>
        <p class="mb-4 leading-relaxed">IPv6 (Internet Protocol version 6) is the bedrock of the modern internet, replacing the exhausted 32-bit IPv4 system with a robust 128-bit addressing model.</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-8">
            <div class="bg-blue-50 p-6 rounded-2xl">
                <h4 class="font-bold text-blue-800 mb-2">Massive Scale</h4>
                <p class="text-sm text-blue-700">340+ undecillion addresses. Enough for every grain of sand on Earth to have trillions of IPs.</p>
            </div>
            <div class="bg-blue-900 p-6 rounded-2xl text-white">
                <h4 class="font-bold text-blue-200 mb-2">Native Security</h4>
                <p class="text-sm text-blue-100">Designed with IPSec as a core requirement, ensuring encrypted transport is accessible by default.</p>
            </div>
        </div>
        <div class="bg-gray-50 p-6 rounded-2xl border border-gray-100">
            <h4 class="font-bold mb-4">Key Characteristics:</h4>
            <ul class="space-y-3 text-sm">
                <li class="flex items-start"><span class="text-blue-600 mr-2">•</span> <strong>Simplified Header:</strong> Reduces processing overhead in routers.</li>
                <li class="flex items-start"><span class="text-blue-600 mr-2">•</span> <strong>No Checksum at IP Layer:</strong> Relies on higher layer protocols.</li>
                <li class="flex items-start"><span class="text-blue-600 mr-2">•</span> <strong>Extensibility:</strong> Uses extension headers for new features.</li>
            </ul>
        </div>
    `,
    'allocation': `
        <h3 class="text-2xl font-black mb-6 text-green-900">Address Distribution Hierarchy</h3>
        <p class="mb-6 leading-relaxed">The allocation of IPv6 addresses follows a controlled, hierarchical flow to prevent fragmentation and maintain efficient routing.</p>
        <div class="space-y-6">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center font-bold text-green-700 shrink-0">1</div>
                <div>
                    <h4 class="font-bold">IANA to RIRs</h4>
                    <p class="text-sm text-gray-600">IANA assigns large /12 blocks to the 5 Regional Internet Registries (like APNIC).</p>
                </div>
            </div>
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center font-bold text-green-700 shrink-0">2</div>
                <div>
                    <h4 class="font-bold">RIR to NIR/LIR</h4>
                    <p class="text-sm text-gray-600">APNIC sub-allocates blocks (typically /32) to National Registries or directly to ISPs.</p>
                </div>
            </div>
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center font-bold text-green-700 shrink-0">3</div>
                <div>
                    <h4 class="font-bold">LIR to End User</h4>
                    <p class="text-sm text-gray-600">ISPs assign blocks (like /48 for enterprises or /64 for homes) to their customers.</p>
                </div>
            </div>
        </div>
    `,
    'policies': `
        <h3 class="text-2xl font-black mb-6 text-orange-900">Community-Driven Policies</h3>
        <p class="mb-4 leading-relaxed">APNIC policies ensure that resources are handled fairly and transparently according to technical best practices.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 my-8">
            <div class="border-2 border-dashed border-orange-200 p-6 rounded-2xl">
                <h4 class="font-bold text-orange-800 mb-2">Conservation</h4>
                <p class="text-sm text-orange-700">Preventing wasteful assignment through strict utilization criteria.</p>
            </div>
            <div class="border-2 border-dashed border-orange-200 p-6 rounded-2xl">
                <h4 class="font-bold text-orange-800 mb-2">Aggregation</h4>
                <p class="text-sm text-orange-700">Grouping multiple networks under a single route to keep global routing tables lean.</p>
            </div>
        </div>
        <p class="text-sm text-gray-600 italic leading-relaxed">"Policies are developed by the APNIC community through an open, bottom-up process."</p>
    `,
    'exhaustion': `
        <h3 class="text-2xl font-black mb-6 text-purple-900">The IPv4 Exhaustion Crisis</h3>
        <p class="mb-6 leading-relaxed">The IPv4 address space (4.3 billion IPs) was officially exhausted at the IANA level in February 2011.</p>
        <div class="bg-purple-900 text-white p-8 rounded-3xl relative overflow-hidden">
            <h4 class="text-xl font-bold mb-4">Why IPv6 is Non-Negotiable</h4>
            <ul class="space-y-4 text-sm text-purple-100">
                <li class="flex items-center"><svg class="w-4 h-4 mr-3 text-purple-300" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"/></svg> Unlimited Growth for IoT and Mobile.</li>
                <li class="flex items-center"><svg class="w-4 h-4 mr-3 text-purple-300" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"/></svg> Eliminates complex NAT workarounds.</li>
                <li class="flex items-center"><svg class="w-4 h-4 mr-3 text-purple-300" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"/></svg> Future-proofs global internet infrastructure.</li>
            </ul>
        </div>
    `
};

function showDocDetail(docId) {
    const area = document.getElementById('doc-content-area');
    const section = document.getElementById('doc-active-detail');
    if (area && section) {
        area.innerHTML = docDetails[docId] || `<h3 class="text-xl font-bold">Documentation: ${docId}</h3><p class="text-gray-500 mt-4 italic">Full educational content coming soon.</p>`;
        section.classList.remove('hidden');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function closeDocDetail() {
    const section = document.getElementById('doc-active-detail');
    if (section) section.classList.add('hidden');
}
