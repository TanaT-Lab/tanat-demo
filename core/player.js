/**
 * TanaT Demo Player
 * 
 * Universal player that loads and plays any demo based on its config.
 * The player handles:
 * - Loading demo configuration
 * - Generating UI from config (pipeline, stations, code blocks)
 * - Audio playback and synchronization
 * - Navigation (prev, next, pause, reveal)
 * - Typewriter effects
 */

// ═══════════════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════════════

let demoConfig = null;          // Loaded demo configuration
let currentStation = -1;        // -1 = transition, 0 = intro, 1+ = stations
let currentLayout = 'transition';  // 'transition', 'intro', 'demo'
let isTyping = false;
let isDisplayComplete = false;
let isPaused = false;
let isZoomedOut = false;
let currentSessionId = 0;
let audioElement = null;
let demoBasePath = '';          // Base path for demo assets

// Timing constants
const NARRATIVE_TYPING_DELAY = 35;

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO LOADING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get demo ID from URL parameters
 */
function getDemoIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('demo') || 'mimic-clustering';
}

/**
 * Load demo configuration
 */
async function loadDemoConfig(demoId) {
    demoBasePath = `demos/${demoId}/`;

    // Load the config script dynamically (staging only: metadata, stations,
    // shown block ids — no code/output/figure).
    const script = document.createElement('script');
    script.src = `${demoBasePath}config.js`;

    await new Promise((resolve, reject) => {
        script.onload = () => {
            if (typeof DEMO_CONFIG !== 'undefined') {
                demoConfig = DEMO_CONFIG;
                resolve(demoConfig);
            } else {
                reject(new Error('DEMO_CONFIG not found in config.js'));
            }
        };
        script.onerror = () => reject(new Error('Failed to load config.js'));
        document.head.appendChild(script);
    });

    // Enrich each shown block from the executed pipeline's outputs.json.
    // Errors (missing outputs.json or a missing block id) propagate to the
    // existing catch in the DOMContentLoaded handler.
    await fillBlocksFromOutputs();

    console.log('Demo config loaded:', demoConfig.id);
    return demoConfig;
}

/**
 * Fetch <demoBasePath>outputs/outputs.json and fill each shown block's code,
 * output and figure from it. outputs.json is the single source of truth for
 * what the audience sees.
 */
async function fillBlocksFromOutputs() {
    const response = await fetch(`${demoBasePath}outputs/outputs.json`);
    if (!response.ok) {
        throw new Error(
            `Failed to load outputs/outputs.json (HTTP ${response.status})`
        );
    }
    const outputs = await response.json();
    const blockMap = new Map((outputs.blocks || []).map(b => [b.id, b]));

    demoConfig.stations.forEach(station => {
        station.blocks = station.blocks.map(id => {
            const data = blockMap.get(id);
            if (!data) {
                throw new Error(
                    `Block '${id}' (station ${station.id}) missing from outputs.json`
                );
            }
            return {
                id: data.id,
                code: data.code,
                output: data.output,
                figure: data.figure
            };
        });
    });
}

/**
 * Initialize the player with loaded config
 */
function initializePlayer() {
    if (!demoConfig) {
        console.error('No demo config loaded');
        return;
    }
    
    // Update header
    document.getElementById('header-title').textContent = demoConfig.title;
    document.getElementById('header-subtitle').textContent = demoConfig.subtitle;
    
    // Generate pipeline
    generatePipeline();
    
    // Generate stations
    generateStations();
    
    console.log('Player initialized for demo:', demoConfig.id);
}

/**
 * Generate pipeline UI from config
 */
function generatePipeline() {
    const container = document.getElementById('pipeline-container');
    if (!container || !demoConfig) return;
    
    container.innerHTML = demoConfig.stations.map((station, index) => `
        <div class="station" data-station="${station.id}">
            <span class="station-icon">○</span>
            <span class="station-name">${station.name}</span>
            <span class="station-desc">${station.description}</span>
            ${index < demoConfig.stations.length - 1 ? '<div class="station-line"></div>' : ''}
        </div>
    `).join('');
    
    // Also generate mobile pipeline
    generateMobilePipeline();
}

/**
 * Generate mobile pipeline header
 */
function generateMobilePipeline() {
    const container = document.getElementById('mobile-pipeline-steps');
    if (!container || !demoConfig) return;
    
    container.innerHTML = demoConfig.stations.map((station, index) => `
        <div class="mobile-step" data-station="${station.id}">
            <span class="mobile-step-dot"></span>
            <span class="mobile-step-label">${station.name}</span>
            ${index < demoConfig.stations.length - 1 ? '<span class="mobile-step-line"></span>' : ''}
        </div>
    `).join('');
}

/**
 * Update mobile pipeline state
 */
function updateMobilePipeline() {
    const steps = document.querySelectorAll('.mobile-step');
    steps.forEach(step => {
        const stationId = parseInt(step.dataset.station);
        step.classList.remove('done', 'current');
        
        if (stationId < currentStation) {
            step.classList.add('done');
        } else if (stationId === currentStation) {
            step.classList.add('current');
        }
    });
    
    // Scroll current step into view on mobile
    const currentStep = document.querySelector('.mobile-step.current');
    if (currentStep) {
        currentStep.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
}

/**
 * Generate station elements from config
 */
function generateStations() {
    const container = document.getElementById('stations-container');
    if (!container || !demoConfig) return;
    
    container.innerHTML = demoConfig.stations.map(station => `
        <section id="station-${station.id}" class="station-content" style="display: none;">
            <div class="station-header">
                <span class="step-badge">Step ${station.id}</span>
                <h2 class="station-title">${station.name}: ${station.description}</h2>
            </div>
            
            ${station.blocks.map(block => {
                let outputHtml = '';
                
                if (block.figure) {
                    // Figure output - images are in demo's outputs/ folder,
                    // file name comes from outputs.json
                    outputHtml = `
                        <div class="figure-output" id="output-${block.id}" style="visibility: hidden;">
                            <img src="${demoBasePath}outputs/${block.figure}" alt="Output visualization">
                        </div>
                    `;
                } else if (block.output !== null && block.output !== undefined) {
                    // Terminal text output - use textContent to avoid HTML indentation issues
                    const outputDiv = document.createElement('div');
                    outputDiv.className = 'terminal-output';
                    outputDiv.id = `output-${block.id}`;
                    outputDiv.style.visibility = 'hidden';
                    outputDiv.textContent = block.output;
                    outputHtml = outputDiv.outerHTML;
                }
                // A block with neither figure nor output renders no output area
                
                return `
                    <div class="code-block">
                        <div class="code-header">
                            <span class="code-label">Python</span>
                        </div>
                        <pre><code id="code-${block.id}" class="language-python"></code></pre>
                    </div>
                    ${outputHtml}
                `;
            }).join('')}
        </section>
    `).join('');
}

// ═══════════════════════════════════════════════════════════════════════════════
// LAYOUT MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

function showLayout(layout) {
    console.log('=== Switching to layout:', layout, '===');
    currentLayout = layout;
    
    // Update body class for CSS hiding rules
    document.body.className = `layout-${layout}`;
    
    const introScreen = document.getElementById('intro-screen');
    const transitionScreen = document.getElementById('transition-screen');
    const sidebar = document.querySelector('.sidebar');
    const header = document.querySelector('.main-header');
    const mainContent = document.querySelector('.main-content');
    
    // Hide all
    if (introScreen) introScreen.style.display = 'none';
    if (transitionScreen) transitionScreen.style.display = 'none';
    if (sidebar) sidebar.style.display = 'none';
    if (header) header.style.display = 'none';
    if (mainContent) mainContent.style.display = 'none';
    
    switch (layout) {
        case 'intro':
            if (introScreen) introScreen.style.display = 'flex';
            break;
        case 'transition':
            if (transitionScreen) transitionScreen.style.display = 'flex';
            break;
        case 'demo':
            if (sidebar) sidebar.style.display = 'flex';
            if (header) header.style.display = 'flex';
            if (mainContent) mainContent.style.display = 'block';
            break;
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEMO FLOW
// ═══════════════════════════════════════════════════════════════════════════════

async function playIntroContent() {
    currentStation = 0;
    
    if (!demoConfig?.intro) {
        transitionToCodeDemo();
        return;
    }
    
    isDisplayComplete = false;
    updateShowButton();
    
    const mySessionId = currentSessionId;
    isTyping = true;
    
    // Show global nav controls
    const globalNavControls = document.getElementById('global-nav-controls');
    if (globalNavControls) globalNavControls.style.display = 'flex';
    
    updateGlobalNavButtons();
    
    const introScreen = document.getElementById('intro-screen');
    const notepadEl = document.getElementById('intro-notepad');
    const vizContainer = document.getElementById('intro-visualizations');
    
    // Reset
    if (notepadEl) notepadEl.innerHTML = '';
    if (vizContainer) vizContainer.innerHTML = '';
    
    // Start audio - now with user interaction, this should work!
    const audioStarted = await tryStartAudio();
    console.log('Audio started:', audioStarted);
    
    // Process notes synchronized with audio (or fallback timer if audio blocked)
    if (demoConfig.intro.notes) {
        await playNotesWithAudio(mySessionId, !audioStarted);
    }
    
    if (!isSessionValid(mySessionId)) return;
    
    isTyping = false;
    isDisplayComplete = true;
    updateShowButton();
    
    console.log('=== Intro complete ===');
}

/**
 * Play notes synchronized with audio timestamps
 * If useFallbackTimer is true, uses a manual timer instead of audio.currentTime
 */
async function playNotesWithAudio(sessionId, useFallbackTimer = false) {
    const notes = demoConfig.intro.notes;
    const notepadEl = document.getElementById('intro-notepad');
    const vizContainer = document.getElementById('intro-visualizations');
    
    if (!notes) return;
    
    let lastProcessedIndex = -1;
    
    // For fallback timer: track elapsed time accounting for pauses
    let fallbackStartTime = Date.now();
    let fallbackPausedTime = 0;
    let wasPaused = false;
    
    // Create a promise that resolves when all notes are shown or session changes
    return new Promise((resolve) => {
        const checkNotes = () => {
            if (!isSessionValid(sessionId)) {
                resolve();
                return;
            }
            
            // Get current time - from audio or fallback timer
            let currentTime;
            if (!useFallbackTimer && audioElement) {
                // Use audio time - automatically pauses when audio pauses
                currentTime = audioElement.currentTime;
                
                // Track pause state for fallback sync
                if (audioElement.paused && !wasPaused) {
                    wasPaused = true;
                    fallbackPausedTime = Date.now();
                } else if (!audioElement.paused && wasPaused) {
                    wasPaused = false;
                    // Adjust start time by pause duration
                    fallbackStartTime += (Date.now() - fallbackPausedTime);
                }
            } else {
                // Fallback: use elapsed time (but pause if audio is paused)
                if (audioElement?.paused) {
                    if (!wasPaused) {
                        wasPaused = true;
                        fallbackPausedTime = Date.now();
                    }
                    // Don't advance time while paused
                    currentTime = (fallbackPausedTime - fallbackStartTime) / 1000;
                } else {
                    if (wasPaused) {
                        wasPaused = false;
                        fallbackStartTime += (Date.now() - fallbackPausedTime);
                    }
                    currentTime = (Date.now() - fallbackStartTime) / 1000;
                }
            }
            
            // Find notes that should be displayed at current time
            for (let i = lastProcessedIndex + 1; i < notes.length; i++) {
                const note = notes[i];
                if (currentTime >= note.time) {
                    displayNote(note, notepadEl, vizContainer);
                    lastProcessedIndex = i;
                } else {
                    break; // Notes are sorted by time
                }
            }
            
            // Check if we've processed all notes
            if (lastProcessedIndex >= notes.length - 1) {
                resolve();
                return;
            }
            
            // Check if audio ended (only if using audio)
            if (!useFallbackTimer && audioElement?.ended) {
                resolve();
                return;
            }
            
            // Continue checking
            requestAnimationFrame(checkNotes);
        };
        
        // Start checking notes
        checkNotes();
        
        // Also resolve when audio ends (if using audio)
        if (!useFallbackTimer && audioElement) {
            const onEnded = () => {
                audioElement.removeEventListener('ended', onEnded);
                resolve();
            };
            audioElement.addEventListener('ended', onEnded);
        }
    });
}

/**
 * Display a single note based on its type
 */
function displayNote(note, notepadEl, vizContainer) {
    const introScreen = document.getElementById('intro-screen');
    
    switch (note.type) {
        case 'welcome':
            const welcomeEl = document.createElement('div');
            welcomeEl.className = 'note-welcome note-appear';
            welcomeEl.innerHTML = note.content;
            notepadEl.appendChild(welcomeEl);
            break;
            
        case 'tagline':
            const taglineEl = document.createElement('div');
            taglineEl.className = 'note-tagline note-appear';
            taglineEl.textContent = note.content;
            notepadEl.appendChild(taglineEl);
            break;
            
        case 'title':
            const titleEl = document.createElement('div');
            titleEl.className = 'note-title note-appear';
            titleEl.innerHTML = note.content;
            notepadEl.appendChild(titleEl);
            break;
            
        case 'bullet':
            const bulletEl = document.createElement('div');
            bulletEl.className = 'note-bullet note-appear';
            bulletEl.innerHTML = `<span class="note-check">✓</span> ${note.content}`;
            notepadEl.appendChild(bulletEl);
            break;
            
        case 'detail':
            const detailEl = document.createElement('div');
            detailEl.className = 'note-detail note-appear';
            detailEl.textContent = note.content;
            notepadEl.appendChild(detailEl);
            break;
            
        case 'divider':
            const dividerEl = document.createElement('div');
            dividerEl.className = 'note-divider note-appear';
            notepadEl.appendChild(dividerEl);
            break;
            
        case 'svg':
            // Display SVG visualization in the notepad flow
            const vizId = note.id;
            const vizHtml = demoConfig.intro.visualizations?.[vizId];
            if (vizHtml && notepadEl) {
                const wrapper = document.createElement('div');
                wrapper.innerHTML = vizHtml;
                wrapper.classList.add('intro-viz-phase', 'anim-fade-in');
                notepadEl.appendChild(wrapper);
                
                // Auto-scroll to new content only if audio is playing
                if (audioElement && !audioElement.paused) {
                    setTimeout(() => {
                        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 100);
                }
            }
            break;
    }
    
    // Scroll to bottom of notepad
    if (note.type !== 'svg') {
        notepadEl.scrollTop = notepadEl.scrollHeight;
    }
}

function transitionToCodeDemo() {
    console.log('Transitioning to code demo');
    
    // Show demo layout immediately
    showLayout('demo');
    currentStation = 0;
    
    // Wait 1 second before starting first station
    setTimeout(() => {
        goToStation(1);
    }, 1000);
}

async function goToStation(stationNum) {
    const station = demoConfig?.stations.find(s => s.id === stationNum);
    if (!station || isTyping) return;
    
    console.log('=== Going to station:', stationNum, '===');
    
    isDisplayComplete = false;
    updateShowButton();
    
    const mySessionId = currentSessionId;
    isTyping = true;
    currentStation = stationNum;
    
    updateGlobalNavButtons();
    playAudioForStation(stationNum);
    
    const stationEl = document.getElementById('station-' + stationNum);
    if (!stationEl) return;
    
    stationEl.style.display = 'block';
    
    // Hide outputs initially
    stationEl.querySelectorAll('.terminal-output, .figure-output').forEach(el => {
        el.style.visibility = 'hidden';
    });
    
    // Mark current station active
    for (let k = 1; k <= demoConfig.stations.length; k++) {
        const el = document.getElementById('station-' + k);
        if (el && el.style.display !== 'none') {
            el.classList.toggle('inactive', k !== stationNum);
        }
    }
    
    updatePipeline();
    stationEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Type each code block
    for (const block of station.blocks) {
        if (!isSessionValid(mySessionId)) return;
        
        const codeEl = document.getElementById('code-' + block.id);
        const outputEl = document.getElementById('output-' + block.id);
        
        if (codeEl && block.code) {
            await typewriter(codeEl, block.code, NARRATIVE_TYPING_DELAY, mySessionId);
            if (!isSessionValid(mySessionId)) return;
        }
        
        if (outputEl) {
            outputEl.style.visibility = 'visible';
        }
        
        await sleep(200);
    }
    
    if (!isSessionValid(mySessionId)) return;
    
    await sleep(300);
    stationEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    isTyping = false;
    isDisplayComplete = true;
    updateShowButton();
    
    console.log('=== Station', stationNum, 'complete ===');
}

// ═══════════════════════════════════════════════════════════════════════════════
// TYPEWRITER
// ═══════════════════════════════════════════════════════════════════════════════

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function isSessionValid(sessionId) {
    return sessionId === currentSessionId;
}

async function waitWhilePaused(sessionId) {
    while (isPaused && isSessionValid(sessionId)) {
        await sleep(100);
    }
}

async function pauseAwareSleep(ms, sessionId) {
    if (!isSessionValid(sessionId)) return false;
    await waitWhilePaused(sessionId);
    if (!isSessionValid(sessionId)) return false;
    await sleep(ms);
    if (!isSessionValid(sessionId)) return false;
    await waitWhilePaused(sessionId);
    return isSessionValid(sessionId);
}

async function typewriter(element, text, speed, sessionId) {
    element.textContent = '';
    if (speed === 0) {
        element.textContent = text;
        hljs.highlightElement(element);
        return;
    }
    
    let currentText = '';
    for (let i = 0; i < text.length; i++) {
        if (!isSessionValid(sessionId)) return;
        
        currentText += text[i];
        const result = hljs.highlight(currentText, { language: 'python' });
        element.innerHTML = result.value;
        
        if (i % 25 === 0) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        const continueTyping = await pauseAwareSleep(speed, sessionId);
        if (!continueTyping) return;
    }
    
    if (isSessionValid(sessionId)) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════════

function updateGlobalNavButtons() {
    const prevBtn = document.getElementById('global-prev-btn');
    const nextBtn = document.getElementById('global-next-btn');
    if (!prevBtn || !nextBtn || !demoConfig) return;
    
    const maxStation = demoConfig.stations.length;
    const currentStep = currentLayout === 'intro' ? 0 : (isZoomedOut ? maxStation + 1 : currentStation);
    
    prevBtn.disabled = currentStep <= 0;
    nextBtn.disabled = currentStep >= maxStation + 1;
}

function goToPreviousStep() {
    forceCompleteCurrentStation();
    
    if (currentLayout === 'intro') return;
    
    if (isZoomedOut) {
        backToScrollView();
        showStationInstantly(demoConfig.stations.length);
        playAudioForStation(demoConfig.stations.length);
    } else if (currentStation === 1) {
        showLayout('intro');
        playIntroContent();
    } else if (currentStation > 1) {
        showStationInstantly(currentStation - 1);
        playAudioForStation(currentStation - 1);
    }
    
    updateGlobalNavButtons();
}

function goToNextStep() {
    forceCompleteCurrentStation();
    
    if (currentLayout === 'intro') {
        transitionToCodeDemo();
    } else if (currentStation < demoConfig.stations.length) {
        goToStation(currentStation + 1);
    } else if (currentStation === demoConfig.stations.length && !isZoomedOut) {
        showFullScript();
    }
}

function stopAndShow() {
    if (isDisplayComplete) return;
    
    currentSessionId++;
    isTyping = false;
    
    if (currentLayout === 'intro') {
        forceCompleteIntro();
    } else {
        forceCompleteStationDisplay();
    }
    
    isDisplayComplete = true;
    updateShowButton();
}

function togglePause() {
    isPaused = !isPaused;
    
    const pauseBtn = document.getElementById('global-pause-btn');
    if (pauseBtn) {
        pauseBtn.textContent = isPaused ? '▶ Resume' : '⏸ Pause';
        pauseBtn.classList.toggle('playing', isPaused);
    }
    
    if (audioElement) {
        if (isPaused) audioElement.pause();
        else audioElement.play().catch(e => console.log('Audio resume failed:', e));
    }
}

function forceCompleteCurrentStation() {
    currentSessionId++;
    isTyping = false;
    isPaused = false;
    
    if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
    }
    
    const pauseBtn = document.getElementById('global-pause-btn');
    if (pauseBtn) {
        pauseBtn.textContent = '⏸ Pause';
        pauseBtn.classList.remove('playing');
    }
    
    if (currentLayout === 'demo' && currentStation >= 1) {
        forceCompleteStationDisplay();
    }
}

function forceCompleteStationDisplay() {
    const station = demoConfig?.stations.find(s => s.id === currentStation);
    if (!station) return;
    
    const stationEl = document.getElementById('station-' + currentStation);
    if (!stationEl) return;
    
    stationEl.style.display = 'block';
    stationEl.classList.remove('inactive');
    
    station.blocks.forEach(block => {
        const codeEl = document.getElementById('code-' + block.id);
        const outputEl = document.getElementById('output-' + block.id);
        
        if (codeEl && block.code) {
            codeEl.className = 'language-python';
            codeEl.removeAttribute('data-highlighted');
            const result = hljs.highlight(block.code, { language: 'python' });
            codeEl.innerHTML = result.value;
        }
        
        if (outputEl) {
            outputEl.style.visibility = 'visible';
        }
    });
}

function forceCompleteIntro() {
    if (!demoConfig?.intro) return;
    
    const notepadEl = document.getElementById('intro-notepad');
    if (!notepadEl) return;
    
    // Clear and display ALL notes instantly
    notepadEl.innerHTML = '';
    
    const notes = demoConfig.intro.notes;
    if (notes) {
        notes.forEach(note => {
            displayNote(note, notepadEl, null);
        });
    }
    
    // Remove animation class from all notes
    notepadEl.querySelectorAll('.note-appear').forEach(el => {
        el.classList.remove('note-appear');
    });
    
    isTyping = false;
}

function showStationInstantly(stationNum) {
    const station = demoConfig?.stations.find(s => s.id === stationNum);
    if (!station) return;
    
    currentStation = stationNum;
    isTyping = false;
    isDisplayComplete = true;
    updateShowButton();
    
    // Show all stations up to this one
    for (let s = 1; s <= stationNum; s++) {
        const stationEl = document.getElementById('station-' + s);
        if (!stationEl) continue;
        
        stationEl.style.display = 'block';
        
        const stationConfig = demoConfig.stations.find(st => st.id === s);
        if (stationConfig) {
            stationConfig.blocks.forEach(block => {
                const codeEl = document.getElementById('code-' + block.id);
                const outputEl = document.getElementById('output-' + block.id);
                
                if (codeEl && block.code) {
                    const result = hljs.highlight(block.code, { language: 'python' });
                    codeEl.innerHTML = result.value;
                }
                
                if (outputEl) {
                    outputEl.style.visibility = 'visible';
                }
            });
        }
    }
    
    // Mark current active
    for (let k = 1; k <= demoConfig.stations.length; k++) {
        const el = document.getElementById('station-' + k);
        if (el && el.style.display !== 'none') {
            el.classList.toggle('inactive', k !== stationNum);
        }
    }
    
    updatePipeline();
    updateGlobalNavButtons();
    
    const stationEl = document.getElementById('station-' + stationNum);
    if (stationEl) stationEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ═══════════════════════════════════════════════════════════════════════════════
// UI UPDATES
// ═══════════════════════════════════════════════════════════════════════════════

function updatePipeline() {
    if (!demoConfig) return;
    
    // Update desktop pipeline
    document.querySelectorAll('.pipeline .station').forEach((station, index) => {
        const stationNum = index + 1;
        station.classList.remove('done', 'current');
        
        if (stationNum < currentStation) {
            station.classList.add('done');
        } else if (stationNum === currentStation) {
            station.classList.add('current');
        }
        
        const icon = station.querySelector('.station-icon');
        if (stationNum < currentStation) icon.textContent = '●';
        else if (stationNum === currentStation) icon.textContent = '◉';
        else icon.textContent = '○';
    });
    
    // Update mobile pipeline
    updateMobilePipeline();
}

function updateShowButton() {
    const btn = document.getElementById('global-skip-btn');
    if (btn) btn.disabled = isDisplayComplete;
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUDIO
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Try to start audio for intro. Returns true if audio started successfully.
 */
async function tryStartAudio() {
    if (!audioElement || !demoConfig?.intro?.audio) return false;
    
    const track = demoBasePath + demoConfig.intro.audio;
    audioElement.src = track;
    
    try {
        await audioElement.play();
        console.log('Audio started successfully');
        return true;
    } catch (e) {
        console.log('Audio autoplay blocked:', e.message);
        // Audio blocked - we'll use fallback timer
        return false;
    }
}

function playAudioForStation(stationNum) {
    if (!audioElement || !demoConfig) return;
    
    let track = null;
    
    if (stationNum === 0 && demoConfig.intro?.audio) {
        track = demoBasePath + demoConfig.intro.audio;
    } else if (stationNum === demoConfig.stations.length + 1 && demoConfig.outro?.audio) {
        track = demoBasePath + demoConfig.outro.audio;
    } else {
        const station = demoConfig.stations.find(s => s.id === stationNum);
        if (station?.audio) {
            track = demoBasePath + station.audio;
        }
    }
    
    if (track) {
        audioElement.src = track;
        // Try to play - if blocked by autoplay policy, retry on user interaction
        const playPromise = audioElement.play();
        if (playPromise !== undefined) {
            playPromise.catch(e => {
                console.log('Audio autoplay blocked, will play on user interaction:', e);
                // Add one-time click listener to start audio
                const playOnInteraction = () => {
                    audioElement.play().catch(() => {});
                    document.removeEventListener('click', playOnInteraction);
                };
                document.addEventListener('click', playOnInteraction, { once: true });
            });
        }
    }
}

function onAudioEnded() {
    console.log('Audio ended, currentStation:', currentStation);
    
    if (isTyping) {
        setTimeout(onAudioEnded, 500);
        return;
    }
    
    if (currentStation === 0 && currentLayout === 'intro') {
        transitionToCodeDemo();
        return;
    }
    
    if (currentStation >= 1 && currentStation < demoConfig.stations.length) {
        goToStation(currentStation + 1);
    } else if (currentStation >= demoConfig.stations.length) {
        showFullScript();
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// FULL SCRIPT VIEW
// ═══════════════════════════════════════════════════════════════════════════════

function showFullScript() {
    if (isZoomedOut || !demoConfig) return;
    
    isZoomedOut = true;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Show all stations
    demoConfig.stations.forEach(station => {
        const stationEl = document.getElementById('station-' + station.id);
        if (stationEl) {
            stationEl.style.display = 'block';
            stationEl.classList.remove('inactive');
            
            station.blocks.forEach(block => {
                const codeEl = document.getElementById('code-' + block.id);
                const outputEl = document.getElementById('output-' + block.id);
                
                if (codeEl && !codeEl.textContent.trim()) {
                    const result = hljs.highlight(block.code, { language: 'python' });
                    codeEl.innerHTML = result.value;
                }
                
                if (outputEl) {
                    outputEl.style.visibility = 'visible';
                }
            });
        }
    });
    
    // Apply split-view for final display
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.add('split-view');
    }
    
    // Add full-script-view class to body for CSS targeting
    document.body.classList.add('full-script-view');
    
    // Show explore section in sidebar, hide pipeline
    const pipelineSection = document.getElementById('sidebar-pipeline-section');
    const exploreSection = document.getElementById('sidebar-explore-section');
    if (pipelineSection) pipelineSection.style.display = 'none';
    if (exploreSection) exploreSection.style.display = 'block';
    
    document.getElementById('spacer')?.classList.add('hidden');
    
    isDisplayComplete = true;
    updateShowButton();
    updateGlobalNavButtons();
    
    // Play outro audio
    playAudioForStation(demoConfig.stations.length + 1);
}

function backToScrollView() {
    if (!isZoomedOut) return;
    
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.remove('split-view');
    }
    
    // Remove full-script-view class from body
    document.body.classList.remove('full-script-view');
    
    // Show pipeline section in sidebar, hide explore
    const pipelineSection = document.getElementById('sidebar-pipeline-section');
    const exploreSection = document.getElementById('sidebar-explore-section');
    if (pipelineSection) pipelineSection.style.display = 'block';
    if (exploreSection) exploreSection.style.display = 'none';
    
    document.getElementById('spacer')?.classList.remove('hidden');
    
    isZoomedOut = false;
    
    const lastStation = document.getElementById('station-' + currentStation);
    if (lastStation) lastStation.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function goBackToLanding() {
    // Stop everything and go back to landing page
    currentSessionId++;
    if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
    }
    window.location.href = 'index.html';
}

// ═══════════════════════════════════════════════════════════════════════════════
// DRAGGABLE NAV BAR
// ═══════════════════════════════════════════════════════════════════════════════

function initDraggableNav() {
    const navControls = document.getElementById('global-nav-controls');
    const dragHandle = document.querySelector('.nav-drag-handle');
    
    if (!navControls || !dragHandle) return;
    
    let isDragging = false;
    let offsetX, offsetY;
    
    dragHandle.addEventListener('mousedown', (e) => {
        isDragging = true;
        navControls.classList.add('dragging');
        
        const rect = navControls.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        
        // Keep within viewport bounds
        const maxX = window.innerWidth - navControls.offsetWidth;
        const maxY = window.innerHeight - navControls.offsetHeight;
        
        navControls.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
        navControls.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
        navControls.style.right = 'auto';
        navControls.style.bottom = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        navControls.classList.remove('dragging');
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async function() {
    console.log('=== TanaT Demo Player Initializing ===');
    
    // Initialize audio
    audioElement = document.getElementById('demo-audio');
    if (audioElement) {
        audioElement.addEventListener('ended', onAudioEnded);
    }
    
    // Load demo config
    const demoId = getDemoIdFromUrl();
    try {
        await loadDemoConfig(demoId);
        initializePlayer();
        
        // Update transition screen with demo title
        const transitionTitle = document.getElementById('transition-title');
        if (transitionTitle && demoConfig) {
            transitionTitle.textContent = demoConfig.title || 'Demo';
        }
        
        // Update mobile header with demo title
        const mobileDemoTitle = document.getElementById('mobile-demo-title');
        if (mobileDemoTitle && demoConfig) {
            mobileDemoTitle.textContent = demoConfig.title || 'Demo';
        }
    } catch (error) {
        console.error('Failed to initialize player:', error);
        const transitionText = document.getElementById('transition-text');
        if (transitionText) transitionText.textContent = 'Failed to load demo';
        return;
    }
    
    // Start at transition screen (logo spinning)
    showLayout('transition');
    
    // Hide actions initially
    const transitionActions = document.getElementById('transition-actions');
    if (transitionActions) transitionActions.style.display = 'none';
    
    // After 1.5s, show the action buttons and hide loading text
    setTimeout(() => {
        const transitionText = document.getElementById('transition-text');
        if (transitionActions) transitionActions.style.display = 'flex';
        if (transitionText) transitionText.style.display = 'none';
    }, 1500);
    
    // Event listeners for transition screen
    document.getElementById('transition-back-btn')?.addEventListener('click', goBackToLanding);
    document.getElementById('transition-start-btn')?.addEventListener('click', async () => {
        // Show intro screen and start content directly
        showLayout('intro');
        await playIntroContent();
    });
    
    document.getElementById('global-back-btn')?.addEventListener('click', goBackToLanding);
    document.getElementById('global-pause-btn')?.addEventListener('click', togglePause);
    document.getElementById('global-skip-btn')?.addEventListener('click', stopAndShow);
    document.getElementById('global-prev-btn')?.addEventListener('click', goToPreviousStep);
    document.getElementById('global-next-btn')?.addEventListener('click', goToNextStep);
    
    // Initialize draggable navigation bar
    initDraggableNav();
    
    console.log('=== Player Ready ===');
});
