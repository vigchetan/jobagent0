// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const uploadBtn = document.getElementById('uploadBtn');
const resumeInput = document.getElementById('resumeInput');
const uploadSection = document.getElementById('uploadSection');
const successSection = document.getElementById('successSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const uploadStatus = document.getElementById('uploadStatus');
const statusText = document.getElementById('statusText');
const reuploadBtn = document.getElementById('reuploadBtn');
const generateBtn = document.getElementById('generateBtn');
const jobStatus = document.getElementById('jobStatus');
const loadingText = document.getElementById('loadingText');

// Initialize popup
async function init() {
    // Check if resume is already uploaded
    const { resumeUploaded } = await chrome.storage.local.get(['resumeUploaded']);

    if (resumeUploaded) {
        showSuccessState();
    } else {
        showUploadState();
    }
}

// Event Listeners
uploadBtn.addEventListener('click', () => {
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

generateBtn.addEventListener('click', async () => {
    await generateDocuments();
});

// Generate resume and cover letter for current job posting
async function generateDocuments() {
    try {
        // Step 1: Extract and capture job posting
        showLoadingForJob('Extracting job posting...');

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

        // Send job posting data to backend
        console.log('[JobApp] Sending job posting to backend...');
        showLoadingForJob('Capturing job posting...');

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

        // Step 2: Generate documents
        showLoadingForJob('Generating cover letter and resume...');

        console.log('[JobApp] Calling /generate endpoint...');
        const generateResponse = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_slug: jobSlug
            })
        });

        const generateResult = await generateResponse.json();

        if (generateResult.success) {
            // Show success message with workspace path
            const workspacePath = `~/JobAgentWorkspace/jobs/${jobSlug}`;

            if (generateResult.status === 'latex_only') {
                showJobSuccess(`Documents generated! LaTeX files saved to: ${workspacePath}. Note: ${generateResult.error}`);
            } else {
                showJobSuccess(`Documents generated! PDFs saved to: ${workspacePath}`);
            }

            showSuccessState();
        } else {
            throw new Error(generateResult.error || 'Failed to generate documents');
        }

    } catch (error) {
        console.error('[JobApp] Error generating documents:', error);
        showJobError(error.message || 'Failed to generate documents. Please try again.');
        showSuccessState();
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
        // Show loading state
        showLoading();

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
    }
}

// UI State Management
function showUploadState() {
    uploadSection.classList.remove('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.add('hidden');
    statusText.textContent = 'Ready';
}

function showSuccessState() {
    uploadSection.classList.add('hidden');
    successSection.classList.remove('hidden');
    loadingIndicator.classList.add('hidden');
    statusText.textContent = 'Resume uploaded';
}

function showLoading() {
    uploadSection.classList.add('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    uploadStatus.textContent = '';
    uploadStatus.className = 'status-message';
    loadingText.textContent = 'Processing resume...';
    statusText.textContent = 'Processing...';
}

function showLoadingForJob(message = 'Capturing job posting...') {
    uploadSection.classList.add('hidden');
    successSection.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    jobStatus.textContent = '';
    jobStatus.className = 'status-message';
    loadingText.textContent = message;
    statusText.textContent = 'Processing...';
}

function showError(message) {
    uploadStatus.textContent = message;
    uploadStatus.className = 'status-message error';
}

function showJobSuccess(message) {
    jobStatus.textContent = message;
    jobStatus.className = 'status-message success';
}

function showJobError(message) {
    jobStatus.textContent = message;
    jobStatus.className = 'status-message error';
}

// Initialize on load
init();
