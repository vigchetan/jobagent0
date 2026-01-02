// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Error message enhancements
const ERROR_SUGGESTIONS = {
    'Failed to fetch': {
        message: 'Cannot connect to backend server',
        suggestions: [
            'Ensure the backend is running on localhost:8000',
            'Run: uvicorn backend.main:app --reload'
        ]
    },
    'File size must be less than 10MB': {
        message: 'Resume file is too large',
        suggestions: [
            'Compress the PDF using online tools',
            'Remove unnecessary images or pages'
        ]
    },
    'Only PDF files are supported': {
        message: 'Invalid file format',
        suggestions: [
            'Convert your resume to PDF format',
            'Ensure the file extension is .pdf'
        ]
    },
    'Please upload a PDF file': {
        message: 'Invalid file format',
        suggestions: [
            'Only PDF files are accepted',
            'Ensure the file extension is .pdf'
        ]
    },
    'Cannot access this page': {
        message: 'Page cannot be read',
        suggestions: [
            'Navigate to a job posting on LinkedIn, Indeed, or company career pages',
            'Avoid restricted pages like chrome://, file://, or chrome-extension://'
        ]
    },
    'No active tab found': {
        message: 'No browser tab is active',
        suggestions: [
            'Ensure you have a job posting page open',
            'Click on the tab before opening the extension'
        ]
    }
};

function enhanceErrorMessage(errorMessage) {
    // Find matching error pattern
    for (const [pattern, details] of Object.entries(ERROR_SUGGESTIONS)) {
        if (errorMessage.includes(pattern)) {
            let enhanced = `<strong>${details.message}</strong><br><br>`;
            enhanced += '<strong>Suggestions:</strong><ul>';
            details.suggestions.forEach(suggestion => {
                enhanced += `<li>${suggestion}</li>`;
            });
            enhanced += '</ul>';
            return enhanced;
        }
    }
    // Return original message if no match
    return errorMessage;
}

// DOM Elements
const dropZone = document.getElementById('dropZone');
const resumeInput = document.getElementById('resumeInput');
const uploadSection = document.getElementById('uploadSection');
const successSection = document.getElementById('successSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const uploadStatus = document.getElementById('uploadStatus');
const backendStatus = document.getElementById('backendStatus');
const backendPill = document.getElementById('backendPill');
const reuploadBtn = document.getElementById('reuploadBtn');
const generateResumeBtn = document.getElementById('generateResumeBtn');
const generateCoverBtn = document.getElementById('generateCoverBtn');
const loadingText = document.getElementById('loadingText');

function resetUploadStatus() {
    if (!uploadStatus) return;
    uploadStatus.textContent = '';
    uploadStatus.className = 'status-message';
}

function setUploadStatusHTML(html, className = 'status-message') {
    if (!uploadStatus) return;
    uploadStatus.innerHTML = html;
    uploadStatus.className = className;
}

// Check backend health
async function checkBackendHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout

        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await response.json();
        return data.status === 'healthy';
    } catch (error) {
        return false;
    }
}

function showBackendStatus(isHealthy) {
    if (isHealthy) {
        backendStatus.className = 'backend-status online';
        backendStatus.innerHTML = '<span class="status-dot"></span> Backend Connected';
        if (backendPill) {
            backendPill.className = 'backend-pill online';
            backendPill.textContent = 'Online';
        }
        // Enable drop zone and buttons
        if (dropZone) dropZone.style.pointerEvents = 'auto';
        if (generateResumeBtn) generateResumeBtn.disabled = false;
        if (generateCoverBtn) generateCoverBtn.disabled = false;
    } else {
        backendStatus.className = 'backend-status offline';
        backendStatus.innerHTML = '<span class="status-dot"></span> Backend Offline';
        if (backendPill) {
            backendPill.className = 'backend-pill offline';
            backendPill.textContent = 'Offline';
        }
        // Disable drop zone and buttons
        if (dropZone) {
            dropZone.style.pointerEvents = 'none';
            dropZone.style.opacity = '0.5';
        }
        if (generateResumeBtn) generateResumeBtn.disabled = true;
        if (generateCoverBtn) generateCoverBtn.disabled = true;
    }
}

// Initialize popup
async function init() {
    // Check backend health
    const isHealthy = await checkBackendHealth();
    showBackendStatus(isHealthy);

    // Poll backend health every 10 seconds
    setInterval(async () => {
        const isHealthy = await checkBackendHealth();
        showBackendStatus(isHealthy);
    }, 10000);

    // Check if resume is already uploaded
    const { resumeUploaded } = await chrome.storage.local.get(['resumeUploaded']);

    if (resumeUploaded) {
        showSuccessState();
    } else {
        showUploadState();
    }
}

// Event Listeners

// Prevent default drag behaviors on entire document
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop zone when dragging over
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('drag-over');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('drag-over');
    }, false);
});

// Handle dropped files
dropZone.addEventListener('drop', async (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];

        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please drop a PDF file');
            return;
        }

        await uploadResume(file);
    }
}, false);

// Handle click to browse
dropZone.addEventListener('click', () => {
    resumeInput.click();
});

resumeInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        await uploadResume(file);
    }
});

reuploadBtn.addEventListener('click', () => {
    showUploadState();
    resumeInput.value = ''; // Clear file input
});

if (generateResumeBtn) {
    generateResumeBtn.addEventListener('click', async () => {
        await generateDocuments('resume', generateResumeBtn);
    });
}

if (generateCoverBtn) {
    generateCoverBtn.addEventListener('click', async () => {
        await generateDocuments('cover', generateCoverBtn);
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + U: Upload resume
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        if (!uploadSection.classList.contains('hidden')) {
            resumeInput.click();
        }
    }

    // Ctrl/Cmd + G: Generate documents (trigger Resume generate)
    if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
        e.preventDefault();
        if (!successSection.classList.contains('hidden') && generateResumeBtn && !generateResumeBtn.disabled) {
            generateResumeBtn.click();
        }
    }

    // Escape: Clear status messages
    if (e.key === 'Escape') {
        resetUploadStatus();
    }
});

// Button state management helper
function setButtonLoading(button, isLoading, originalText) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Processing...';
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || originalText;
        button.classList.remove('loading');
    }
}

// Generate resume and cover letter for current job posting
async function generateDocuments(docType = 'both', button = null) {
    try {
        if (button) setButtonLoading(button, true);
        // Step 1: Extract and capture job posting
        showLoadingWithProgress(
            1, 3,
            'Extracting Job Posting',
            'Reading job requirements from the page...'
        );

        // Get the current active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab || !tab.id) {
            throw new Error('No active tab found');
        }

        console.log('[JobApp] Injecting content script...');

        // Inject content script dynamically (only when needed)
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js']
            });
            console.log('[JobApp] Content script injected successfully');
        } catch (injectionError) {
            // Check if it's because the script is already injected or if it's a real error
            if (injectionError.message.includes('Cannot access')) {
                throw new Error(
                    'Cannot access this page. Please navigate to a job posting on a website ' +
                    '(LinkedIn, Indeed, company career pages, etc.) and try again.'
                );
            }
            // If it's a "already injected" error, we can proceed
            console.log('[JobApp] Script may already be injected, proceeding...', injectionError.message);
        }

        console.log('[JobApp] Sending message to content script...');

        // Send message to content script to extract job posting
        const response = await chrome.tabs.sendMessage(tab.id, {
            action: 'extractJobPosting'
        });

        console.log('[JobApp] Received response from content script:', response);

        if (!response.success) {
            throw new Error(response.error || 'Failed to extract job posting from page');
        }

        const { raw_text, url } = response.data;

        // Step 2: Analyze job requirements
        console.log('[JobApp] Sending job posting to backend...');
        showLoadingWithProgress(
            2, 3,
            'Analyzing Job Requirements',
            'Understanding role expectations and required skills...'
        );

        const jobResponse = await fetch(`${API_BASE_URL}/job`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                raw_text: raw_text,
                url: url
            })
        });

        const jobResult = await jobResponse.json();

        if (!jobResult.success) {
            throw new Error(jobResult.error || 'Failed to capture job posting');
        }

        const jobSlug = jobResult.job_slug;
        console.log('[JobApp] Job captured:', jobSlug);

        // Step 3: Generate documents
        showLoadingWithProgress(
            3, 3,
            'Generating Documents',
            'Creating tailored resume and cover letter using AI...'
        );

        console.log('[JobApp] Calling /generate endpoint...');
        const generateResponse = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_slug: jobSlug,
                doc_type: docType
            })
        });

        const generateResult = await generateResponse.json();

        if (generateResult.success) {
            // Show success message with workspace path
            const workspacePath = `~/JobAgentWorkspace/jobs/${jobSlug}`;

            if (generateResult.status === 'latex_only') {
                showJobSuccess(`Documents generated! LaTeX files saved to: ${workspacePath}. Note: ${generateResult.error}`);
            } else {
                // tailor message based on requested docType
                if (docType === 'resume') {
                    showJobSuccess(`Resume generated! PDFs saved to: ${workspacePath}`);
                } else if (docType === 'cover') {
                    showJobSuccess(`Cover letter generated! PDFs saved to: ${workspacePath}`);
                } else {
                    showJobSuccess(`Documents generated! PDFs saved to: ${workspacePath}`);
                }
            }

            showSuccessState();
        } else {
            throw new Error(generateResult.error || 'Failed to generate documents');
        }

    } catch (error) {
        console.error('[JobApp] Error generating documents:', error);
        showJobError(error.message || 'Failed to generate documents. Please try again.');
        showSuccessState();
    } finally {
        if (button) setButtonLoading(button, false);
    }
}

// Upload resume to backend
async function uploadResume(file) {
    // Validate file type
    if (!file.name.endsWith('.pdf')) {
        showError('Please upload a PDF file');
        return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
    }

    try {
        // Disable drop zone during upload
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.6';
        // Show loading state
        showLoadingWithProgress(1, 1, 'Uploading Resume', 'Analyzing your resume with AI...');

        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Upload to backend
        const response = await fetch(`${API_BASE_URL}/resume`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Save state to storage
            await chrome.storage.local.set({
                resumeUploaded: true,
                resumePath: result.resume_path
            });

            // Show success state
            showSuccessState();
        } else {
            throw new Error(result.error || 'Upload failed');
        }

    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'Failed to upload resume. Please try again.');
        showUploadState();
    } finally {
        // Re-enable drop zone
        dropZone.style.pointerEvents = 'auto';
        dropZone.style.opacity = '1';
    }
}

// UI State Management
function showLoadingWithProgress(step, total, title, detail) {
    uploadSection.classList.add('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');

    const loadingText = document.getElementById('loadingText');
    const loadingProgress = document.getElementById('loadingProgress');
    const loadingDetail = document.getElementById('loadingDetail');

    loadingText.textContent = title;
    loadingProgress.textContent = `Step ${step} of ${total}`;
    loadingDetail.textContent = detail;
}

function showUploadState() {
    uploadSection.classList.remove('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.add('hidden');
    // Reset drop zone if backend is online
    if (backendStatus.classList.contains('online')) {
        dropZone.style.opacity = '1';
    }
}

function showSuccessState() {
    uploadSection.classList.add('hidden');
    successSection.classList.remove('hidden');
    loadingIndicator.classList.add('hidden');
}

function showLoading() {
    uploadSection.classList.add('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    resetUploadStatus();
    loadingText.textContent = 'Processing resume...';
}

function showLoadingForJob(message = 'Capturing job posting...') {
    uploadSection.classList.add('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    // jobStatus element removed; use uploadStatus for interim messages if needed
    resetUploadStatus();
    loadingText.textContent = message;
}

// Format paths in messages
function formatPath(message) {
    // Wrap paths in code tags for better styling
    return message.replace(/(~\/JobAgentWorkspace\/[^\s]+)/g, '<code>$1</code>');
}

function showError(message) {
    const enhancedMessage = enhanceErrorMessage(message);
    setUploadStatusHTML(enhancedMessage, 'status-message error');
}

function showJobSuccess(message) {
    const formattedMessage = formatPath(message);
    // show job success in the uploadStatus area instead (jobStatus removed)
    setUploadStatusHTML(`
        <div class="success-animation">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
        </div>
        <div class="success-text">${formattedMessage}</div>`,
        'status-message success animated'
    );
}

function showJobError(message) {
    const enhancedMessage = enhanceErrorMessage(message);
    // show job error in the uploadStatus area instead (jobStatus removed)
    setUploadStatusHTML(enhancedMessage, 'status-message error');
}

// Initialize on load
init();
