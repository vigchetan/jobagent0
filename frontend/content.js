/**
 * Content script for extracting job posting data from the current page.
 * Runs in the context of job posting pages (LinkedIn, Indeed, AngelList, etc.)
 */

// Show visual notification on the page
function showNotification(message, type = 'info') {
  // Remove any existing notification
  const existing = document.getElementById('jobagent-notification');
  if (existing) {
    existing.remove();
  }

  // Create notification element
  const notification = document.createElement('div');
  notification.id = 'jobagent-notification';
  notification.className = `jobagent-notification ${type}`;

  // Icon based on type
  let iconPath = '';
  if (type === 'success') {
    iconPath = 'M9 12l2 2 4-4M7.8 21h8.4a1.8 1.8 0 001.8-1.8V4.8A1.8 1.8 0 0016.2 3H7.8A1.8 1.8 0 006 4.8v14.4A1.8 1.8 0 007.8 21z';
  } else if (type === 'error') {
    iconPath = 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z';
  } else {
    iconPath = 'M9 12l2 2 4-4M7.8 21h8.4a1.8 1.8 0 001.8-1.8V4.8A1.8 1.8 0 0016.2 3H7.8A1.8 1.8 0 006 4.8v14.4A1.8 1.8 0 007.8 21z';
  }

  notification.innerHTML = `
    <div class="notification-content">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path d="${iconPath}" stroke="currentColor" stroke-width="2"/>
      </svg>
      <span>${message}</span>
    </div>
  `;

  // Add inline styles to avoid CSP issues
  const bgColor = type === 'success' ? '#2e7d32' : type === 'error' ? '#c62828' : '#1A1A1A';
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, ${bgColor} 0%, ${bgColor}dd 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    z-index: 2147483647;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    animation: slideInRight 0.3s ease-out;
    max-width: 300px;
  `;

  // Add notification to page
  document.body.appendChild(notification);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease-in';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'extractJobPosting') {
    try {
      console.log('[JobApp] Extracting job posting from page...');
      showNotification('Reading job posting...', 'info');

      // Extract the full text content of the page
      // Using document.body.innerText gives us readable text without HTML tags
      const rawText = document.body.innerText;

      // Get the current page URL
      const url = window.location.href;

      // Validate extraction
      if (!rawText || rawText.trim().length === 0) {
        sendResponse({
          success: false,
          error: 'Failed to extract text from page'
        });
        return;
      }

      console.log('[JobApp] Successfully extracted job posting');
      console.log('[JobApp] Text length:', rawText.length);
      console.log('[JobApp] URL:', url);
      showNotification('Job posting captured!', 'success');

      // Send the extracted data back to the popup
      sendResponse({
        success: true,
        data: {
          raw_text: rawText,
          url: url
        }
      });
    } catch (error) {
      console.error('[JobApp] Error extracting job posting:', error);
      showNotification('Failed to read page', 'error');
      sendResponse({
        success: false,
        error: error.message
      });
    }

    // Return true to indicate we'll send a response asynchronously
    return true;
  }
});

console.log('[JobApp] Content script loaded');
