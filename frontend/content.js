/**
 * Content script for extracting job posting data from the current page.
 * Runs in the context of job posting pages (LinkedIn, Indeed, AngelList, etc.)
 */

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'extractJobPosting') {
    try {
      console.log('[JobApp] Extracting job posting from page...');

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
