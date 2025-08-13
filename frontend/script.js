// Configuration
const API_BASE_URL = 'https://cv-parser-backend-4eir.onrender.com'; // Production backend URL

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const uploadSection = document.getElementById('upload-section');
const resultsSection = document.getElementById('results-section');

// Results elements
const scoreValue = document.getElementById('score-value');
const scoreBadge = document.getElementById('score-badge');
const scoreGauge = document.getElementById('score-gauge');
const contactScore = document.getElementById('contact-score');
const skillsScore = document.getElementById('skills-score');
const educationScore = document.getElementById('education-score');
const experienceScore = document.getElementById('experience-score');
const structureScore = document.getElementById('structure-score');
const readabilityScore = document.getElementById('readability-score');
const issuesList = document.getElementById('issues-list');
const contactInfo = document.getElementById('contact-info');
const skillsList = document.getElementById('skills-list');
const optimizeBtn = document.getElementById('optimize-btn');
const industrySelect = document.getElementById('industry-select');

// Advanced elements
const advancedCard = document.getElementById('advanced-card');
const advancedScore = document.getElementById('advanced-score');
const advancedScoreBadge = document.getElementById('advanced-score-badge');
const advGenPct = document.getElementById('adv-gen-pct');
const advIndPct = document.getElementById('adv-ind-pct');
const advActionCount = document.getElementById('adv-action-count');
const advQuantCount = document.getElementById('adv-quant-count');
const advGrammarCount = document.getElementById('adv-grammar-count');
const advWeakCount = document.getElementById('adv-weak-count');
const advMissingGeneral = document.getElementById('adv-missing-general');
const advMissingIndustry = document.getElementById('adv-missing-industry');
const advIssuesList = document.getElementById('adv-issues-list');

// Event Listeners
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', handleDragOver);
dropZone.addEventListener('dragleave', handleDragLeave);
dropZone.addEventListener('drop', handleDrop);
fileInput.addEventListener('change', handleFileSelect);
optimizeBtn.addEventListener('click', handleOptimizeClick);

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('border-blue-400', 'bg-blue-50');
}

function handleDragEnter(e) {
    e.preventDefault();
    dropZone.classList.add('border-blue-400', 'bg-blue-50');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// ===== CV IMPROVEMENT FUNCTIONS =====

// Check data function for debugging
function checkData() {
    console.log('📊 Checking available data...');
    
    const data = {
        currentResults: window.currentResults,
        advancedReport: window.currentResults?.advanced_report,
        originalCVText: window.originalCVText,
        originalCVTextLength: window.originalCVText?.length,
        hasAtsScore: !!window.currentResults?.advanced_report?.ats_score,
        atsScore: window.currentResults?.advanced_report?.ats_score,
        issuesCount: window.currentResults?.advanced_report?.issues?.length || 0,
        missingKeywords: window.currentResults?.advanced_report?.keyword_matches?.missing?.length || 0
    };
    
    console.log('📊 Data summary:', data);
    
    // Show data in alert for quick check
    let message = 'Data Check Results:\n\n';
    message += `Current Results: ${data.currentResults ? '✅ Available' : '❌ Missing'}\n`;
    message += `Advanced Report: ${data.advancedReport ? '✅ Available' : '❌ Missing'}\n`;
    message += `Original CV Text: ${data.originalCVText ? `✅ Available (${data.originalCVTextLength} chars)` : '❌ Missing'}\n`;
    message += `ATS Score: ${data.hasAtsScore ? `✅ ${data.atsScore}` : '❌ Missing'}\n`;
    message += `Issues Count: ${data.issuesCount}\n`;
    message += `Missing Keywords: ${data.missingKeywords}\n`;
    
    alert(message);
    
    return data;
}

// Optimize Button Handler
function handleOptimizeClick() {
    alert('Button clicked! Starting CV improvement...'); // Immediate feedback
    
    console.log('🔍 Optimize button clicked');
    console.log('Current results:', window.currentResults);
    console.log('Advanced report:', window.currentResults?.advanced_report);
    console.log('Original CV text:', window.originalCVText);
    
    // Check if we have ATS analysis results
    if (!window.currentResults || !window.currentResults.advanced_report) {
        alert('No ATS analysis results found. Please analyze a resume first.');
        return;
    }
    
    // Show the CV improvement interface
    showCVImprovementInterface();
}

// ===== FILE HANDLING FUNCTIONS =====

// File Handling
function handleFile(file) {
    // Store original file for CV improvement
    window.originalFile = file;
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
        showError('Please upload a PDF, DOCX, or TXT file.');
        return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB.');
        return;
    }
    
    // Upload file
    uploadFile(file);
}

// File Upload
async function uploadFile(file) {
    try {
        // Show progress
        showProgress();
        
        const formData = new FormData();
        formData.append('file', file);

        // Simulate progress
        simulateProgress();

        const industry = (industrySelect && industrySelect.value) ? industrySelect.value : 'technology';
        const response = await fetch(`${API_BASE_URL}/upload-resume?industry=${encodeURIComponent(industry)}`, {
            method: 'POST',
            body: formData,
            // Add timeout and other production settings
            signal: AbortSignal.timeout(60000) // 60 second timeout
        });

        if (!response.ok) {
            let errorMessage = 'Upload failed';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // If we can't parse error JSON, use status-based message
                switch (response.status) {
                    case 400:
                        errorMessage = 'Invalid file type or size. Please check file requirements.';
                        break;
                    case 413:
                        errorMessage = 'File too large. Maximum size is 10MB.';
                        break;
                    case 500:
                        errorMessage = 'Server error. Please try again later.';
                        break;
                    case 502:
                        errorMessage = 'Bad Gateway - Backend service may be down. Please try again later.';
                        break;
                    case 503:
                        errorMessage = 'Service temporarily unavailable. Please try again.';
                        break;
                    default:
                        errorMessage = `Upload failed (Error ${response.status})`;
                }
            }
            
            throw new Error(errorMessage);
        }

        const result = await response.json();
        
        if (result.success) {
            // Store the original CV text for improvement
            if (result.parsed_data && result.parsed_data.original_text) {
                window.originalCVText = result.parsed_data.original_text;
            }
            
            showSuccess('Resume processed successfully!');
            displayResults(result);
        } else {
            throw new Error('Upload processing failed');
        }

    } catch (error) {
        console.error('Upload error:', error);
        
        if (error.name === 'AbortError') {
            showError('Upload timeout. Please check your connection and try again.');
        } else if (error.message.includes('Failed to fetch')) {
            showError('Connection failed. Please check your internet connection.');
        } else {
            showError(error.message || 'Failed to upload file. Please try again.');
        }
    } finally {
        hideProgress();
    }
}

// Test CORS specifically
async function testCORS() {
    try {
        console.log('🔍 Testing CORS configuration...');
        
        // Try a simple OPTIONS request first
        const optionsResponse = await fetch(`${API_BASE_URL}/test-cors`, {
            method: 'OPTIONS',
            mode: 'cors',
            signal: AbortSignal.timeout(10000)
        });
        
        console.log('OPTIONS response status:', optionsResponse.status);
        console.log('OPTIONS response headers:', Object.fromEntries(optionsResponse.headers.entries()));
        
        return optionsResponse.ok;
    } catch (error) {
        console.error('❌ CORS test failed:', error);
        return false;
    }
}

// Simple ping test to check if backend is reachable
async function pingBackend() {
    try {
        console.log('🔍 Pinging backend to check basic connectivity...');
        
        // Try to fetch the root endpoint first
        const response = await fetch(`${API_BASE_URL}/`, {
            method: 'GET',
            mode: 'cors',
            signal: AbortSignal.timeout(15000) // 15 second timeout for ping
        });
        
        if (response.ok) {
            console.log('✅ Backend root endpoint is reachable');
            return true;
        } else {
            console.log(`⚠️ Backend root endpoint responded with status: ${response.status}`);
            return false;
        }
    } catch (error) {
        console.error('❌ Backend ping failed:', error);
        return false;
    }
}

// Enhanced connection test with ping
async function testConnection(retries = 2) {
    // First, try a simple ping
    const isReachable = await pingBackend();
    if (!isReachable) {
        console.error('❌ Backend is not reachable at all - possible network or service issue');
        return false;
    }
    
    // Test CORS configuration
    const corsOk = await testCORS();
    if (!corsOk) {
        console.error('❌ CORS configuration issue detected');
        return false;
    }
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            console.log(`Testing backend connection (attempt ${attempt}/${retries})...`);
            console.log(`Target URL: ${API_BASE_URL}/test-cors`);
            
            // Use longer timeout for production (Render.com can be slow to start)
            const timeout = window.location.hostname.includes('render.com') ? 30000 : 10000;
            console.log(`Using timeout: ${timeout}ms`);
            
            const startTime = Date.now();
            const response = await fetch(`${API_BASE_URL}/test-cors`, {
                method: 'GET',
                mode: 'cors',
                signal: AbortSignal.timeout(timeout) // 30 seconds for production, 10 for local
            });
            const endTime = Date.now();
            
            console.log(`Response received in ${endTime - startTime}ms`);
            console.log(`Response status: ${response.status} ${response.statusText}`);
            console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Backend connection successful:', data);
                return true;
            } else {
                console.error(`❌ Backend connection failed (attempt ${attempt}):`, response.status, response.statusText);
                if (attempt === retries) return false;
            }
        } catch (error) {
            console.error(`❌ Connection attempt ${attempt} failed with error:`, error);
            console.error(`Error name: ${error.name}`);
            console.error(`Error message: ${error.message}`);
            console.error(`Error stack:`, error.stack);
            
            if (error.name === 'AbortError' || error.name === 'TimeoutError') {
                console.error(`❌ Backend connection timeout (attempt ${attempt}) - service may be starting up or down`);
                if (window.location.hostname.includes('render.com')) {
                    console.log('💡 Render.com services can take 30+ seconds to start up');
                }
            } else if (error.message.includes('Failed to fetch')) {
                console.error(`❌ Backend connection failed (attempt ${attempt}) - CORS or network issue`);
            } else {
                console.error(`❌ Backend connection error (attempt ${attempt}):`, error);
            }
            
            if (attempt === retries) return false;
            
            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
        }
    }
    return false;
}

// Test connection on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('CV Parser & ATS Scorer initialized');
    
    // Add status indicator to the page
    addStatusIndicator();
    
    // Add test button for debugging
    addTestButton();
    
    // Test connection on page load
    testConnection().then(success => {
        updateStatusIndicator(success);
        if (!success) {
            // Show a user-friendly message if backend is down
            setTimeout(() => {
                showConnectionError();
            }, 1000);
        }
    });
    
    // Set up periodic health checks (every 2 minutes)
    setInterval(async () => {
        const success = await testConnection(1); // Single attempt for health checks
        updateStatusIndicator(success);
    }, 120000);
    
    // Add console commands for debugging
    window.debugBackend = runDiagnostics;
    window.testBackendConnection = testConnection;
    console.log('🔧 Debug commands available:');
    console.log('  - debugBackend() - Run full diagnostics');
    console.log('  - testBackendConnection() - Test connection');
});

// Show connection error with retry option
function showConnectionError() {
    const isProduction = window.location.hostname.includes('render.com');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
    
    errorDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">Backend service is currently unavailable.</p>
                ${isProduction ? 
                    '<p class="text-xs text-red-100 mt-1">Render.com services can take 30+ seconds to start up after inactivity.</p>' : 
                    '<p class="text-xs text-red-100 mt-1">This may be due to maintenance or network issues.</p>'
                }
                <div class="mt-2 space-y-2">
                    <button onclick="retryConnection()" class="w-full px-3 py-1 bg-white text-red-500 text-xs rounded hover:bg-gray-100 transition-colors">
                        Retry Connection
                    </button>
                    ${isProduction ? 
                        '<button onclick="showRenderInfo()" class="w-full px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors">Learn More</button>' : 
                        ''
                    }
                </div>
            </div>
            <div class="ml-3 flex-shrink-0">
                <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Remove after 20 seconds (longer for production)
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, isProduction ? 20000 : 15000);
}

// Show Render.com specific information
function showRenderInfo() {
    const infoDiv = document.createElement('div');
    infoDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    infoDiv.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">About Render.com Services</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <div class="space-y-3 text-sm text-gray-600">
                <p>• <strong>Free tier services</strong> automatically sleep after 15 minutes of inactivity</p>
                <p>• <strong>Cold starts</strong> can take 30+ seconds to wake up</p>
                <p>• <strong>First request</strong> after sleep will be slower</p>
                <p>• <strong>Subsequent requests</strong> will be much faster</p>
            </div>
            
            <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                <p class="text-xs text-blue-800">
                    <strong>Tip:</strong> If you're experiencing delays, wait a moment and try again. 
                    The service should respond faster on subsequent attempts.
                </p>
            </div>
            
            <div class="mt-4 flex justify-end">
                <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Got it
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(infoDiv);
}

// Retry connection
async function retryConnection() {
    const errorDiv = document.querySelector('.fixed.bg-red-500');
    if (errorDiv) {
        errorDiv.remove();
    }
    
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = 'Retrying...';
        statusText.className = 'text-yellow-500';
    }
    
    const success = await testConnection(2);
    updateStatusIndicator(success);
    
    if (success) {
        showSuccess('Connection restored! Backend is now online.');
    } else {
        showConnectionError();
    }
}

// Progress Handling
function showProgress() {
    progressContainer.classList.remove('hidden');
    uploadSection.classList.add('opacity-50');
}

function hideProgress() {
    progressContainer.classList.add('hidden');
    uploadSection.classList.remove('opacity-50');
}

function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 90) {
            progress = 90;
            clearInterval(interval);
        }
        updateProgress(progress);
    }, 200);
}

function updateProgress(percentage) {
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `${Math.round(percentage)}%`;
}

// Results Display
function displayResults(result) {
    // Store current results for CV improvement
    window.currentResults = result;
    
    // Update score
    const score = result.ats_score;
    scoreValue.textContent = score;
    
    // Update score badge
    updateScoreBadge(score);
    
    // Update score breakdown
    updateScoreBreakdown(result.score_breakdown);
    
    // Update issues
    updateIssues(result.issues);
    
    // Update parsed data
    updateParsedData(result.parsed_data);

    // Advanced report
    if (result.advanced_report) {
        updateAdvanced(result.advanced_report);
        advancedCard.classList.remove('hidden');
    } else {
        advancedCard.classList.add('hidden');
    }
    
    // Show results
    uploadSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function updateScoreBadge(score) {
    let color, text;
    
    if (score >= 80) {
        color = 'bg-green-100 text-green-800';
        text = 'Excellent';
    } else if (score >= 60) {
        color = 'bg-blue-100 text-blue-800';
        text = 'Good';
    } else if (score >= 40) {
        color = 'bg-yellow-100 text-yellow-800';
        text = 'Fair';
    } else {
        color = 'bg-red-100 text-red-800';
        text = 'Needs Work';
    }
    
    scoreBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${color}`;
    scoreBadge.textContent = text;
}

function updateAdvanced(report) {
    const score = report.ats_score || 0;
    advancedScore.textContent = score;
    const badge = score >= 80 ? ['bg-green-100 text-green-800','Excellent'] :
                 score >= 60 ? ['bg-blue-100 text-blue-800','Good'] :
                 score >= 40 ? ['bg-yellow-100 text-yellow-800','Fair'] : ['bg-red-100 text-red-800','Needs Work'];
    advancedScoreBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${badge[0]}`;
    advancedScoreBadge.textContent = badge[1];

    // Percentages
    advGenPct.textContent = `${report.keyword_matches?.percentage ?? 0}%`;
    advIndPct.textContent = `${report.industry_keyword_matches?.percentage ?? 0}%`;
    // Counts
    const actionCount = Object.values(report.action_verbs_found || {}).reduce((a,b)=>a + b.length, 0);
    advActionCount.textContent = actionCount;
    const quantCount = Object.values(report.quantification_found || {}).reduce((a,b)=>a + b.length, 0);
    advQuantCount.textContent = quantCount;
    advGrammarCount.textContent = (report.grammar_issues || []).length;
    advWeakCount.textContent = (report.weak_language_found || []).length;

    // Missing keywords chips
    const mk = (items) => (items || []).slice(0, 10).map(k=>`<span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">${k}</span>`).join('') || '<span class="text-sm text-gray-500">None</span>';
    advMissingGeneral.innerHTML = mk(report.keyword_matches?.missing);
    advMissingIndustry.innerHTML = mk(report.industry_keyword_matches?.missing);

    // Issues list
    if ((report.issues || []).length === 0) {
        advIssuesList.innerHTML = '<div class="text-sm text-gray-500">No advanced issues detected.</div>';
        return;
    }
    advIssuesList.innerHTML = (report.issues || []).slice(0, 12).map(i => `
        <div class="p-3 border rounded-lg bg-gray-50">
            <div class="text-sm text-gray-900"><strong>${i.type ?? 'issue'}:</strong> ${i.message || ''}</div>
            ${i.snippet ? `<div class="text-xs text-gray-600 mt-1">"${i.snippet.replaceAll('<','&lt;').replaceAll('>','&gt;')}”</div>` : ''}
            ${i.suggestion ? `<div class="text-xs text-blue-700 mt-1">Suggestion: ${i.suggestion}</div>` : ''}
        </div>
    `).join('');
}

function updateScoreBreakdown(breakdown) {
    contactScore.querySelector('.text-lg').textContent = `${breakdown.contact || 0}/15`;
    skillsScore.querySelector('.text-lg').textContent = `${breakdown.skills || 0}/25`;
    educationScore.querySelector('.text-lg').textContent = `${breakdown.education || 0}/10`;
    experienceScore.querySelector('.text-lg').textContent = `${breakdown.experience || 0}/20`;
    structureScore.querySelector('.text-lg').textContent = `${breakdown.structure || 0}/15`;
    readabilityScore.querySelector('.text-lg').textContent = `${breakdown.readability || 0}/15`;
}

function updateIssues(issues) {
    if (issues.length === 0) {
        issuesList.innerHTML = `
            <div class="text-center py-4">
                <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>
                <p class="text-green-600 font-medium">No issues found!</p>
                <p class="text-gray-500 text-sm">Your resume looks great for ATS systems.</p>
            </div>
        `;
        return;
    }

    issuesList.innerHTML = issues.map(issue => {
        const priorityColors = {
            high: 'border-red-200 bg-red-50',
            medium: 'border-yellow-200 bg-yellow-50',
            low: 'border-blue-200 bg-blue-50'
        };
        
        const priorityIcons = {
            high: `<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>`,
            medium: `<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>`,
            low: `<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`
        };

        return `
            <div class="flex items-start p-4 border rounded-lg ${priorityColors[issue.priority] || priorityColors.medium}">
                <div class="flex-shrink-0 mr-3">
                    ${priorityIcons[issue.priority] || priorityIcons.medium}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">${issue.message}</p>
                    <p class="text-xs text-gray-600 mt-1">Category: ${issue.category}</p>
                </div>
            </div>
        `;
    }).join('');
}

function updateParsedData(parsedData) {
    // Update contact information
    contactInfo.innerHTML = '';
    
    if (parsedData.email) {
        contactInfo.innerHTML += `
            <div class="flex items-center">
                <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                </svg>
                <span class="text-gray-700">${parsedData.email}</span>
            </div>
        `;
    }
    
    if (parsedData.mobile) {
        contactInfo.innerHTML += `
            <div class="flex items-center">
                <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                </svg>
                <span class="text-gray-700">${parsedData.mobile}</span>
            </div>
        `;
    }
    
    if (parsedData.linkedin) {
        contactInfo.innerHTML += `
            <div class="flex items-center">
                <svg class="w-4 h-4 text-gray-400 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                <a href="${parsedData.linkedin}" target="_blank" class="text-blue-600 hover:underline">LinkedIn Profile</a>
            </div>
        `;
    }
    
    if (parsedData.github) {
        contactInfo.innerHTML += `
            <div class="flex items-center">
                <svg class="w-4 h-4 text-gray-400 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <a href="${parsedData.github}" target="_blank" class="text-gray-700 hover:underline">GitHub Profile</a>
            </div>
        `;
    }

    // Update skills
    skillsList.innerHTML = '';
    if (parsedData.skills && parsedData.skills.length > 0) {
        parsedData.skills.forEach(skill => {
            skillsList.innerHTML += `
                <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">${skill}</span>
            `;
        });
    } else {
        skillsList.innerHTML = '<p class="text-gray-500 text-sm">No skills detected</p>';
    }
}

// Error Handling
function showError(message) {
    // Create error notification with better styling and close button
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
    
    errorDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-3 flex-shrink-0">
                <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Remove after 8 seconds (longer for production)
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 8000);
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
    
    errorDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-red-100">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

// Show success message
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
    
    successDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-green-100">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 5000);
}

// Show CV improvement interface
function showCVImprovementInterface() {
    console.log('🔧 Showing CV improvement interface...');
    
    // Load available templates
    loadCVTemplates();
    
    // Update current ATS score
    const currentScore = window.currentResults?.advanced_report?.ats_score || 0;
    document.getElementById('current-ats-score').textContent = currentScore;
    
    // Update issues summary
    updateIssuesSummary();
    
    // Show modal
    document.getElementById('cv-improvement-modal').classList.remove('hidden');
    
    console.log('✅ CV improvement interface shown');
}

// Load available CV templates
async function loadCVTemplates() {
    try {
        console.log('🔧 Loading CV templates...');
        
        const response = await fetch(`${API_BASE_URL}/cv-templates`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.templates) {
            console.log('✅ Templates loaded:', data.templates);
            populateTemplateSelect(data.templates);
        } else {
            console.error('❌ Failed to load templates:', data);
            showError('Failed to load CV templates');
        }
        
    } catch (error) {
        console.error('❌ Error loading templates:', error);
        showError('Failed to load CV templates. Please try again.');
        
        // Fallback: use default templates
        const fallbackTemplates = [
            { id: 'modern_professional', name: 'Modern Professional', description: 'Clean, ATS-friendly corporate style' },
            { id: 'creative_professional', name: 'Creative Professional', description: 'Modern design with visual hierarchy' },
            { id: 'academic_research', name: 'Academic/Research', description: 'Formal academic style' },
            { id: 'executive_leadership', name: 'Executive/Leadership', description: 'Senior-level format' }
        ];
        populateTemplateSelect(fallbackTemplates);
    }
}

// Populate template selection dropdown
function populateTemplateSelect(templates) {
    const templateSelect = document.getElementById('template-select');
    
    // Clear existing options
    templateSelect.innerHTML = '';
    
    // Add templates
    templates.forEach(template => {
        const option = document.createElement('option');
        option.value = template.id;
        option.textContent = `${template.name} - ${template.description}`;
        templateSelect.appendChild(option);
    });
    
    // Set default selection
    if (templates.length > 0) {
        templateSelect.value = templates[0].id;
    }
    
    console.log('✅ Template select populated with', templates.length, 'templates');
}

// Update issues summary
function updateIssuesSummary() {
    const issuesSummary = document.getElementById('issues-summary');
    const issues = window.currentResults?.advanced_report?.issues || [];
    
    if (issues.length === 0) {
        issuesSummary.innerHTML = '<p class="text-green-600">No major issues found! Your CV is already well-optimized.</p>';
        return;
    }
    
    // Group issues by type
    const issueGroups = {};
    issues.forEach(issue => {
        const type = issue.type || 'other';
        if (!issueGroups[type]) {
            issueGroups[type] = [];
        }
        issueGroups[type].push(issue);
    });
    
    // Create summary HTML
    let summaryHTML = '<div class="space-y-3">';
    
    Object.entries(issueGroups).forEach(([type, typeIssues]) => {
        const count = typeIssues.length;
        const typeName = type.charAt(0).toUpperCase() + type.slice(1);
        
        summaryHTML += `
            <div class="flex items-center justify-between p-2 bg-white rounded border">
                <span class="text-sm font-medium text-gray-700">${typeName}</span>
                <span class="text-sm text-gray-500">${count} issue${count > 1 ? 's' : ''}</span>
            </div>
        `;
    });
    
    summaryHTML += '</div>';
    issuesSummary.innerHTML = summaryHTML;
}

// Start CV improvement process
async function startCVImprovement() {
    try {
        console.log('🚀 Starting CV improvement process...');
        
        // Get selected values
        const templateId = document.getElementById('template-select').value;
        const industry = document.getElementById('industry-select-improvement').value;
        
        if (!templateId) {
            showError('Please select a CV template');
            return;
        }
        
        console.log('Selected template:', templateId);
        console.log('Selected industry:', industry);
        
        // Show progress
        showImprovementProgress();
        
        // Prepare request data
        const requestData = {
            original_cv_text: window.originalCVText,
            ats_feedback: window.currentResults.advanced_report,
            industry: industry,
            original_score: window.currentResults.advanced_report.ats_score,
            template_id: templateId
        };
        
        console.log('Request data prepared:', requestData);
        
        // Send improvement request
        const response = await fetch(`${API_BASE_URL}/improve-cv`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ CV improvement successful:', result);
            showImprovementResults(result);
        } else {
            throw new Error(result.error || 'CV improvement failed');
        }
        
    } catch (error) {
        console.error('❌ CV improvement error:', error);
        showError(`CV improvement failed: ${error.message}`);
    } finally {
        hideImprovementProgress();
    }
}

// Helper functions for strategy display
function getStrategyColor(strategy) {
    switch (strategy) {
        case 'minor_fix':
            return 'bg-green-100 text-green-800';
        case 'major_overhaul':
            return 'bg-red-100 text-red-800';
        case 'hybrid':
            return 'bg-yellow-100 text-yellow-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

function getStrategyName(strategy) {
    switch (strategy) {
        case 'minor_fix':
            return 'Minor Fix';
        case 'major_overhaul':
            return 'Major Overhaul';
        case 'hybrid':
            return 'Hybrid Approach';
        default:
            return 'Unknown';
    }
}

function getStrategyDescription(strategy) {
    switch (strategy) {
        case 'minor_fix':
            return 'Preserved structure and style, fixed ATS issues only';
        case 'major_overhaul':
            return 'Complete rewrite with modern ATS-friendly template';
        case 'hybrid':
            return 'Improved structure while maintaining original style';
        default:
            return 'Standard optimization';
    }
}

// Helper functions for base64 PDF handling
function previewPDFFromBase64(base64Data) {
    try {
        // Convert base64 to blob
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        
        // Create object URL and open in new tab
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        
        // Clean up object URL after a delay
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
        console.error('Error previewing PDF:', error);
        alert('Error previewing PDF. Please try downloading instead.');
    }
}

function downloadPDFFromBase64(base64Data, filename) {
    try {
        // Convert base64 to blob
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up object URL
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
        console.error('Error downloading PDF:', error);
        alert('Error downloading PDF. Please try again.');
    }
}

// Show improvement results
function showImprovementResults(result) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-semibold text-gray-900">CV Improvement Complete! 🎉</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <div class="space-y-6">
                <!-- Score Improvement -->
                <div class="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg">
                    <div class="flex items-center justify-between">
                        <div>
                            <h4 class="font-medium text-gray-900">Score Improvement</h4>
                            <p class="text-sm text-gray-600">Your CV has been optimized for ATS systems</p>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-gray-900">${result.original_score} → ${result.new_score}</div>
                            <div class="text-sm text-green-600">+${result.new_score - result.original_score} points</div>
                        </div>
                    </div>
                </div>
                
                <!-- Strategy Used -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Improvement Strategy</h4>
                    <div class="flex items-center">
                        <span class="px-3 py-1 rounded-full text-sm font-medium ${getStrategyColor(result.improvement_strategy)}">
                            ${getStrategyName(result.improvement_strategy)}
                        </span>
                        <p class="ml-3 text-sm text-gray-600">${getStrategyDescription(result.improvement_strategy)}</p>
                    </div>
                </div>
                
                <!-- Changes Made -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Changes Made</h4>
                    <ul class="space-y-1">
                        ${result.changes_made.map(change => `<li class="text-sm text-gray-600">• ${change}</li>`).join('')}
                    </ul>
                </div>
                
                <!-- ATS Feedback Summary -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">ATS Issues Addressed</h4>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="font-medium">Total Issues:</span>
                            <span class="text-gray-600">${result.ats_feedback_summary.issues_count}</span>
                        </div>
                        <div>
                            <span class="font-medium">Missing Keywords:</span>
                            <span class="text-gray-600">${result.ats_feedback_summary.missing_keywords}</span>
                        </div>
                        <div>
                            <span class="font-medium">Grammar Issues:</span>
                            <span class="text-gray-600">${result.ats_feedback_summary.grammar_issues}</span>
                        </div>
                        <div>
                            <span class="font-medium">Spelling Issues:</span>
                            <span class="text-gray-600">${result.ats_feedback_summary.spelling_issues}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Download Section -->
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-3">Download Your Improved CV</h4>
                    ${result.pdf_download_url ? 
                        `<div class="space-y-3">
                            <p class="text-sm text-gray-600">Your CV has been optimized and converted to a professional PDF format.</p>
                            <div class="flex space-x-3">
                                <a href="${result.pdf_download_url}" target="_blank" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                    </svg>
                                    Preview PDF
                                </a>
                                <a href="${result.pdf_download_url}" download="improved_cv.pdf" class="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    Download PDF
                                </a>
                            </div>
                        </div>` :
                        result.pdf_data_base64 ?
                        `<div class="space-y-3">
                            <p class="text-sm text-gray-600">Your CV has been optimized and converted to a professional PDF format.</p>
                            <p class="text-xs text-amber-600 bg-amber-50 p-2 rounded">Note: Using direct download (Supabase upload unavailable)</p>
                            <div class="flex space-x-3">
                                <button onclick="previewPDFFromBase64('${result.pdf_data_base64}')" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542 7z"></path>
                                    </svg>
                                    Preview PDF
                                </button>
                                <button onclick="downloadPDFFromBase64('${result.pdf_data_base64}', 'improved_cv.pdf')" class="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    Download PDF
                                </button>
                            </div>
                        </div>` :
                        `<div class="text-center py-4">
                            <div class="text-red-500 mb-2">
                                <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                </svg>
                            </div>
                            <p class="text-sm text-gray-600">PDF generation failed. Please try again or contact support.</p>
                        </div>`
                    }
                </div>
                
                <!-- Improved CV Text Preview -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Improved CV Preview</h4>
                    <div class="bg-white p-3 rounded border max-h-40 overflow-y-auto">
                        <pre class="text-xs text-gray-700 whitespace-pre-wrap">${result.improved_cv_text.substring(0, 500)}${result.improved_cv_text.length > 500 ? '...' : ''}</pre>
                    </div>
                    <p class="text-xs text-gray-500 mt-2">Showing first 500 characters. Full text is available in the downloaded PDF.</p>
                </div>
            </div>
            
            <div class="mt-6 flex justify-end space-x-3">
                <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                    Close
                </button>
                ${result.pdf_download_url ? 
                    `<a href="${result.pdf_download_url}" download="improved_cv.pdf" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        Download PDF
                    </a>` : 
                    result.pdf_data_base64 ?
                    `<button onclick="downloadPDFFromBase64('${result.pdf_data_base64}', 'improved_cv.pdf')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        Download PDF
                    </button>` : ''
                }
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Show improvement progress
function showImprovementProgress() {
    const modal = document.createElement('div');
    modal.id = 'improvement-progress-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4 text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">Improving Your CV...</h3>
            <p class="text-sm text-gray-600 mb-4">AI is analyzing and optimizing your resume based on ATS feedback</p>
            <div class="space-y-2 text-xs text-gray-500">
                <div>✓ Analyzing ATS feedback</div>
                <div>✓ Generating improved content</div>
                <div>✓ Creating optimized PDF</div>
                <div>⏳ Finalizing improvements...</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function hideImprovementProgress() {
    const progressModal = document.getElementById('improvement-progress-modal');
    if (progressModal) {
        progressModal.remove();
    }
}

// Add status indicator to the page
function addStatusIndicator() {
    const header = document.querySelector('header');
    if (header) {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'backend-status';
        statusDiv.className = 'flex items-center text-sm';
        statusDiv.innerHTML = `
            <div class="flex items-center">
                <div class="w-2 h-2 rounded-full bg-gray-400 mr-2" id="status-dot"></div>
                <span class="text-gray-500" id="status-text">Checking...</span>
                <button onclick="manualStatusCheck()" class="ml-2 text-gray-400 hover:text-gray-600" title="Check backend status">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                </button>
                <button onclick="runDiagnostics()" class="ml-2 text-blue-400 hover:text-blue-600" title="Run detailed diagnostics">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                    </svg>
                </button>
            </div>
        `;
        
        // Insert after the title
        const title = header.querySelector('h1');
        if (title && title.parentNode) {
            title.parentNode.insertBefore(statusDiv, title.nextSibling);
        }
    }
}

// Manual status check
async function manualStatusCheck() {
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = 'Checking...';
        statusText.className = 'text-gray-500';
    }
    
    const success = await testConnection(1);
    updateStatusIndicator(success);
    
    if (success) {
        showSuccess('Backend is online and responding!');
    } else {
        showConnectionError();
    }
}

// Update status indicator
function updateStatusIndicator(isOnline) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    if (statusDot && statusText) {
        if (isOnline) {
            statusDot.className = 'w-2 h-2 rounded-full bg-green-500 mr-2';
            statusText.textContent = 'Backend Online';
            statusText.className = 'text-green-600';
        } else {
            statusDot.className = 'w-2 h-2 rounded-full bg-red-500 mr-2';
            statusText.textContent = 'Backend Offline';
            statusText.className = 'text-red-600';
        }
    }
}

// Manual diagnostic function
async function runDiagnostics() {
    console.log('🔍 Running backend diagnostics...');
    
    const results = {
        timestamp: new Date().toISOString(),
        frontend: {
            url: window.location.href,
            userAgent: navigator.userAgent,
            apiBaseUrl: API_BASE_URL
        },
        tests: {}
    };
    
    // Test 1: Basic connectivity
    console.log('\n=== Test 1: Basic Connectivity ===');
    results.tests.connectivity = await pingBackend();
    
    // Test 2: CORS configuration
    console.log('\n=== Test 2: CORS Configuration ===');
    results.tests.cors = await testCORS();
    
    // Test 3: Specific endpoint
    console.log('\n=== Test 3: Test-CORS Endpoint ===');
    try {
        const response = await fetch(`${API_BASE_URL}/test-cors`, {
            method: 'GET',
            mode: 'cors',
            signal: AbortSignal.timeout(15000)
        });
        results.tests.testCorsEndpoint = {
            status: response.status,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries())
        };
        console.log('Test-CORS endpoint response:', results.tests.testCorsEndpoint);
    } catch (error) {
        results.tests.testCorsEndpoint = {
            error: error.name,
            message: error.message
        };
        console.error('Test-CORS endpoint failed:', error);
    }
    
    // Test 4: Health endpoint
    console.log('\n=== Test 4: Health Endpoint ===');
    try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors',
            signal: AbortSignal.timeout(15000)
        });
        results.tests.healthEndpoint = {
            status: healthResponse.status,
            ok: healthResponse.ok
        };
        if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            results.tests.healthEndpoint.data = healthData;
            console.log('Health endpoint data:', healthData);
        }
    } catch (error) {
        results.tests.healthEndpoint = {
            error: error.name,
            message: error.message
        };
        console.error('Health endpoint failed:', error);
    }
    
    console.log('\n=== Diagnostic Results ===');
    console.log(JSON.stringify(results, null, 2));
    
    // Show results to user
    showDiagnosticResults(results);
    
    return results;
}

// Show diagnostic results
function showDiagnosticResults(results) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-semibold text-gray-900">Backend Diagnostics</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <div class="space-y-4">
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">Test Results</h4>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-3 rounded-lg ${results.tests.connectivity ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}">
                            <div class="font-medium">Connectivity</div>
                            <div class="text-sm">${results.tests.connectivity ? '✅ OK' : '❌ Failed'}</div>
                        </div>
                        <div class="p-3 rounded-lg ${results.tests.cors ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}">
                            <div class="font-medium">CORS</div>
                            <div class="text-sm">${results.tests.cors ? '✅ OK' : '❌ Failed'}</div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">Endpoint Tests</h4>
                    <div class="space-y-2">
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <div class="font-medium text-sm">Test-CORS Endpoint</div>
                            <div class="text-xs text-gray-600">
                                Status: ${results.tests.testCorsEndpoint.status || 'N/A'}<br>
                                ${results.tests.testCorsEndpoint.error ? `Error: ${results.tests.testCorsEndpoint.error}` : 'Response OK'}
                            </div>
                        </div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <div class="font-medium text-sm">Health Endpoint</div>
                            <div class="text-xs text-gray-600">
                                Status: ${results.tests.healthEndpoint.status || 'N/A'}<br>
                                ${results.tests.healthEndpoint.error ? `Error: ${results.tests.healthEndpoint.error}` : 'Response OK'}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">Raw Results</h4>
                    <pre class="bg-gray-100 p-3 rounded text-xs overflow-x-auto">${JSON.stringify(results, null, 2)}</pre>
                </div>
            </div>
            
            <div class="mt-6 flex justify-end">
                <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                    Close
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Add test button for debugging
function addTestButton() {
    const header = document.querySelector('header');
    if (header) {
        const testDiv = document.createElement('div');
        testDiv.className = 'ml-4';
        testDiv.innerHTML = `
            <button onclick="testCVImprovement()" class="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700">
                Test CV Improvement
            </button>
        `;
        
        // Insert after the status indicator
        const statusIndicator = document.getElementById('backend-status');
        if (statusIndicator && statusIndicator.parentNode) {
            statusIndicator.parentNode.insertBefore(testDiv, statusIndicator.nextSibling);
        }
    }
}

// Test CV improvement function
function testCVImprovement() {
    console.log('🧪 Testing CV improvement...');
    console.log('Current results:', window.currentResults);
    console.log('Advanced report:', window.currentResults?.advanced_report);
    console.log('Original CV text:', window.originalCVText);
    
    if (!window.currentResults || !window.currentResults.advanced_report) {
        alert('No ATS analysis results found. Please analyze a resume first.');
        return;
    }
    
    if (!window.originalCVText) {
        alert('No original CV text found. Please re-upload your resume.');
        return;
    }
    
    // Show the CV improvement interface
    showCVImprovementInterface();
}

// Initialize event listeners
function initializeEventListeners() {
    console.log('🔧 Initializing event listeners...');
    
    // Get all button elements
    const testOptimizeBtn = document.getElementById('test-optimize-btn');
    const checkDataBtn = document.getElementById('check-data-btn');
    
    // Check if elements exist
    console.log('Drop zone:', dropZone);
    console.log('File input:', fileInput);
    console.log('Optimize button:', optimizeBtn);
    console.log('Test optimize button:', testOptimizeBtn);
    console.log('Check data button:', checkDataBtn);
    
    if (optimizeBtn) {
        console.log('✅ Optimize button found, attaching click handler');
        optimizeBtn.addEventListener('click', handleOptimizeClick);
        console.log('✅ Click handler attached to optimize button');
    } else {
        console.error('❌ Optimize button not found!');
    }
    
    if (testOptimizeBtn) {
        console.log('✅ Test optimize button found, attaching click handler');
        testOptimizeBtn.addEventListener('click', handleOptimizeClick);
        console.log('✅ Click handler attached to test optimize button');
    } else {
        console.error('❌ Test optimize button not found!');
    }
    
    if (checkDataBtn) {
        console.log('✅ Check data button found, attaching click handler');
        checkDataBtn.addEventListener('click', checkData);
        console.log('✅ Click handler attached to check data button');
    } else {
        console.error('❌ Check data button not found!');
    }
    
    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('drop', handleDrop);
        dropZone.addEventListener('dragenter', handleDragEnter);
        dropZone.addEventListener('dragleave', handleDragLeave);
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
}

// Initialize
initializeEventListeners();

// Fallback: Ensure test buttons work even if event listeners fail
setTimeout(() => {
    console.log('🔧 Setting up fallback button handlers...');
    
    const testOptimizeBtn = document.getElementById('test-optimize-btn');
    const checkDataBtn = document.getElementById('check-data-btn');
    
    if (testOptimizeBtn && typeof handleOptimizeClick === 'function') {
        // Remove any existing listeners and add fresh ones
        testOptimizeBtn.replaceWith(testOptimizeBtn.cloneNode(true));
        const newTestBtn = document.getElementById('test-optimize-btn');
        newTestBtn.addEventListener('click', handleOptimizeClick);
        console.log('✅ Fallback handler attached to test optimize button');
    }
    
    if (checkDataBtn && typeof checkData === 'function') {
        // Remove any existing listeners and add fresh ones
        checkDataBtn.replaceWith(checkDataBtn.cloneNode(true));
        const newCheckBtn = document.getElementById('check-data-btn');
        newCheckBtn.addEventListener('click', checkData);
        console.log('✅ Fallback handler attached to check data button');
    }
}, 1000);

// Test function availability
console.log('🧪 Testing function availability...');
console.log('handleOptimizeClick function:', typeof handleOptimizeClick);
console.log('showCVImprovementInterface function:', typeof showCVImprovementInterface);
console.log('checkData function:', typeof checkData);

// Make functions globally available for testing
window.testOptimizeClick = handleOptimizeClick;
window.testShowInterface = showCVImprovementInterface;
window.checkData = checkData;

console.log('🔧 Test functions available:');
console.log('  - testOptimizeClick() - Test the optimize button handler');
console.log('  - testShowInterface() - Test showing the improvement interface');
console.log('  - checkData() - Check available data for CV improvement');

// Test if functions are working
try {
    console.log('🧪 Testing function calls...');
    if (typeof handleOptimizeClick === 'function') {
        console.log('✅ handleOptimizeClick is a function');
    } else {
        console.error('❌ handleOptimizeClick is not a function:', typeof handleOptimizeClick);
    }
    
    if (typeof showCVImprovementInterface === 'function') {
        console.log('✅ showCVImprovementInterface is a function');
    } else {
        console.error('❌ showCVImprovementInterface is not a function:', typeof showCVImprovementInterface);
    }
    
    if (typeof checkData === 'function') {
        console.log('✅ checkData is a function');
    } else {
        console.error('❌ checkData is not a function:', typeof checkData);
    }
} catch (error) {
    console.error('❌ Error testing functions:', error);
}
