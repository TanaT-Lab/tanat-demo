/**
 * TanaT Demo Landing Page Controller
 * 
 * Manages the demo selection page and loads available demos
 */

// Registry of available demos
const DEMOS_REGISTRY = [
    {
        id: 'mimic-clustering',
        title: 'Hospital Readmission Patterns',
        subtitle: 'MIMIC-IV Dataset',
        description: 'Analyze hospital readmission patterns using clustering on patient trajectories',
        icon: '🏥',
        tags: ['clustering', 'healthcare', 'MIMIC-IV'],
        duration: '~5 min',
        path: 'demos/mimic-clustering'
    }
    // Add more demos here as they are created
    // {
    //     id: 'survival-analysis',
    //     title: 'Survival Analysis',
    //     subtitle: 'Kaplan-Meier Curves',
    //     description: 'Perform survival analysis on patient cohorts',
    //     icon: '📊',
    //     tags: ['survival', 'statistics'],
    //     duration: '~4 min',
    //     path: 'demos/survival-analysis'
    // }
];

/**
 * Render demo cards in the list
 */
function renderDemoCards() {
    const list = document.getElementById('demos-list');
    if (!list) return;
    
    list.innerHTML = DEMOS_REGISTRY.map(demo => `
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
                    <span class="demo-duration">⏱ ${demo.duration}</span>
                </div>
            </div>
        </article>
    `).join('');
}

/**
 * Launch a specific demo directly (skip welcome screen)
 */
function launchDemo(demoId) {
    const demo = DEMOS_REGISTRY.find(d => d.id === demoId);
    if (!demo) {
        console.error('Demo not found:', demoId);
        return;
    }
    
    // Navigate to the player (keep welcome screen for audio policy compliance)
    window.location.href = `player.html?demo=${demoId}`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== TanaT Demo Landing Page ===');
    renderDemoCards();
});
