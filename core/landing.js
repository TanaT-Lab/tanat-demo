/**
 * TanaT Demo Landing Page Controller
 * 
 * Manages the demo selection page and loads available demos.
 * The demo list is read from demos/index.json (written by generate_all.py);
 * the landing keeps no hard-coded copy.
 */

/**
 * Render demo cards in the list
 */
function renderDemoCards(demos) {
    const list = document.getElementById('demos-list');
    if (!list) return;
    
    list.innerHTML = demos.map(demo => `
        <article class="demo-card" onclick="launchDemo('${demo.id}')">
            <div class="demo-card-icon">${demo.icon}</div>
            <div class="demo-card-content">
                <h3 class="demo-card-title">${demo.title}</h3>
                <p class="demo-card-subtitle">${demo.subtitle}</p>
                <p class="demo-card-description">${demo.description}</p>
                <div class="demo-card-meta">
                    <div class="demo-card-tags">
                        ${demo.tags.map(tag => `<span class="demo-tag">${tag}</span>`).join('')}
                    </div>
                    ${demo.duration ? `<span class="demo-duration">⏱ ${demo.duration}</span>` : ''}
                </div>
            </div>
        </article>
    `).join('');
}

/**
 * Launch a specific demo directly (skip welcome screen)
 */
function launchDemo(demoId) {
    // Navigate to the player (keep welcome screen for audio policy compliance)
    window.location.href = `player.html?demo=${demoId}`;
}

/**
 * Load the demo manifest and render the cards. On failure a visible message is
 * shown in #demos-list.
 */
async function loadDemos() {
    const list = document.getElementById('demos-list');
    if (!list) return;
    try {
        const response = await fetch('demos/index.json');
        if (!response.ok) {
            throw new Error(`Failed to load demos/index.json (HTTP ${response.status})`);
        }
        const demos = await response.json();
        if (!demos.length) {
            list.innerHTML = '<p class="demos-empty">No demos available.</p>';
            return;
        }
        renderDemoCards(demos);
    } catch (error) {
        console.error('Failed to load demos:', error);
        list.innerHTML = '<p class="demos-error">Failed to load demos. Please try again later.</p>';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== TanaT Demo Landing Page ===');
    loadDemos();
});
