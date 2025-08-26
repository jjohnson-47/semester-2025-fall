// Iframe Code Generator JavaScript
// Extracted from inline script to comply with CSP policy

// Use production URL for iframe embedding in Blackboard
const baseUrl = 'https://courses.jeffsthings.com';

function generateCode() {
  const course = document.getElementById('course').value;
  const type = document.getElementById('type').value;
  const height = document.getElementById('height').value;

  if (!course || !type) {
    alert('Please select both course and content type.');
    return;
  }

  const url = `${baseUrl}/courses/${course}/fall-2025/${type}/embed/`;
  
  // Blackboard-optimized iframe with proper security and accessibility attributes
  const iframeCode = `<iframe 
    src="${url}" 
    width="100%" 
    height="${height}" 
    frameborder="0" 
    scrolling="auto"
    title="${course} ${type.charAt(0).toUpperCase() + type.slice(1)}"
    allowfullscreen="false"
    sandbox="allow-same-origin allow-scripts allow-forms"
    style="border: 1px solid #666; border-radius: 4px; display: block; margin: 0 auto; max-width: 100%;"
    loading="lazy">
    <p>Your browser does not support iframes. Please <a href="${url}" target="_blank" rel="noopener noreferrer">click here to view the ${type}</a>.</p>
  </iframe>`;

  document.getElementById('output').style.display = 'block';
  document.getElementById('output').textContent = iframeCode;

  // Update preview
  document.getElementById('preview').innerHTML = iframeCode;
}

// Auto-generate when all fields are filled
document.addEventListener('DOMContentLoaded', function() {
  ['course', 'type', 'height'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
      const course = document.getElementById('course').value;
      const type = document.getElementById('type').value;
      if (course && type) {
        generateCode();
      }
    });
  });
});