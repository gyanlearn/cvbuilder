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
    dropZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
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

// Connection test function
async function testConnection() {
    try {
        console.log('Testing backend connection...');
        const response = await fetch(`${API_BASE_URL}/test-cors`, {
            method: 'GET',
            mode: 'cors'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Backend connection successful:', data);
            return true;
        } else {
            console.error('❌ Backend connection failed:', response.status, response.statusText);
            return false;
        }
    } catch (error) {
        console.error('❌ Backend connection error:', error);
        return false;
    }
}

// Test connection on page load
document.addEventListener('DOMContentLoaded', function() {
    testConnection();
});

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
            ${i.snippet ? `<div class="text-xs text-gray-600 mt-1">“${i.snippet.replaceAll('<','&lt;').replaceAll('>','&gt;')}”</div>` : ''}
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

// Success notification
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
            <div class="ml-3 flex-shrink-0">
                <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 5000);
}

// Optimize Button Handler
function handleOptimizeClick() {
    // This would typically redirect to an AI optimization service
    alert('AI Resume Optimization feature coming soon! This would integrate with advanced AI services to provide specific improvement suggestions.');
}

// Start CV improvement process
async function startCVImprovement() {
    const industry = document.getElementById('improvement-industry').value;
    
    // Use existing ATS feedback and CV text
    if (!window.currentResults || !window.currentResults.advanced_report) {
        showError('No ATS analysis results found. Please analyze a resume first.');
        return;
    }
    
    try {
        // Show progress
        showImprovementProgress();
        
        // Get the original CV text from the stored results
        const originalCVText = window.originalCVText || 'CV content from analysis';
        
        if (!originalCVText || originalCVText === 'CV content from analysis') {
            showError('Original CV text not found. Please re-upload your resume.');
            return;
        }
        
        // Create the request payload
        const requestData = {
            original_cv_text: originalCVText,
            ats_feedback: window.currentResults.advanced_report,
            industry: industry,
            original_score: window.currentResults.advanced_report.ats_score
        };
        
        // Call the improvement endpoint
        const response = await fetch(`${API_BASE_URL}/improve-cv`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
            mode: 'cors'
        });
        
        if (!response.ok) {
            let errorMessage = 'CV improvement failed';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                switch (response.status) {
                    case 400:
                        errorMessage = 'Invalid request data.';
                        break;
                    case 500:
                        errorMessage = 'Server error during CV improvement.';
                        break;
                    case 503:
                        errorMessage = 'AI service temporarily unavailable.';
                        break;
                    default:
                        errorMessage = `CV improvement failed (Error ${response.status})`;
                }
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showImprovementResults(result);
        } else {
            throw new Error('CV improvement processing failed');
        }
        
    } catch (error) {
        console.error('CV improvement error:', error);
        showError(error.message || 'Failed to improve CV. Please try again.');
    } finally {
        hideImprovementProgress();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('CV Parser & ATS Scorer initialized');
});
