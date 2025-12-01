// Background service worker for JobApp extension

console.log('JobApp background service worker loaded');

// Listen for extension installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('JobApp extension installed');

    // Initialize storage
    chrome.storage.local.set({
        resumeUploaded: false,
        resumePath: null
    });
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkBackendHealth') {
        checkBackendHealth().then(sendResponse);
        return true; // Indicates async response
    }
});

// Check if backend is running
async function checkBackendHealth() {
    try {
        const response = await fetch('http://localhost:8000/api/health');
        const data = await response.json();
        return { healthy: data.status === 'healthy' };
    } catch (error) {
        return { healthy: false, error: error.message };
    }
}
