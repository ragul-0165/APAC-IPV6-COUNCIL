const COUNTRY_NAMES = {
    "AF": "Afghanistan", "AS": "American Samoa", "AU": "Australia", "BD": "Bangladesh",
    "BT": "Bhutan", "BN": "Brunei Darussalam", "KH": "Cambodia", "CN": "China",
    "CK": "Cook Islands", "FJ": "Fiji", "GU": "Guam", "HK": "Hong Kong", "IN": "India",
    "ID": "Indonesia", "JP": "Japan", "KR": "Korea, Republic of", "LA": "Lao PDR",
    "MO": "Macau", "MY": "Malaysia", "MV": "Maldives", "MN": "Mongolia", "MM": "Myanmar",
    "NP": "Nepal", "NC": "New Caledonia", "NZ": "New Zealand", "PK": "Pakistan",
    "PG": "Papua New Guinea", "PH": "Philippines", "WS": "Samoa", "SG": "Singapore",
    "SB": "Solomon Islands", "LK": "Sri Lanka", "TW": "Taiwan", "TH": "Thailand",
    "TL": "Timor-Leste", "TO": "Tonga", "VU": "Vanuatu", "VN": "Vietnam", "KZ": "Kazakhstan",
    "UZ": "Uzbekistan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", "PF": "French Polynesia",
    "KI": "Kiribati", "MH": "Marshall Islands", "FM": "Micronesia", "NR": "Nauru",
    "PW": "Palau", "TV": "Tuvalu", "KP": "Korea, DPR", "MP": "N. Mariana Islands",
    "NU": "Niue", "WF": "Wallis and Futuna", "CX": "Christmas Island", "CC": "Cocos Islands",
    "NF": "Norfolk Island", "IO": "British Indian Ocean Territory", "TK": "Tokelau", "PN": "Pitcairn"
};

function toggleAIChat() {
    const window = document.getElementById('ai-chat-window');
    window.classList.toggle('hidden');
    if (!window.classList.contains('hidden')) {
        document.getElementById('ai-chat-input').focus();
    }
}

async function sendAIMessage() {
    const input = document.getElementById('ai-chat-input');
    const container = document.getElementById('ai-chat-messages');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessageToUI('user', message);
    input.value = '';

    // Add typing indicator
    const typingId = addTypingIndicator();
    container.scrollTop = container.scrollHeight;

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                context: window.location.pathname // Provide page context
            })
        });

        const data = await response.json();
        removeTypingIndicator(typingId);
        addMessageToUI('assistant', data.response);
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToUI('assistant', "I apologize, but I'm having trouble connecting to my intelligence core. Please verify your network connection.");
    }

    container.scrollTop = container.scrollHeight;
}

function addMessageToUI(role, text) {
    const container = document.getElementById('ai-chat-messages');
    const div = document.createElement('div');
    div.className = `ai-message ${role}`;
    div.innerText = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('ai-chat-messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'ai-message assistant typing-indicator';
    div.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    container.appendChild(div);
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
