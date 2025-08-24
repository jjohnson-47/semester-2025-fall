// Iframe Code Generator JavaScript
// Extracted from inline script to comply with CSP policy

const baseUrl = window.location.origin;

function generateCode() {
  const course = document.getElementById('course').value;
  const type = document.getElementById('type').value;
  const height = document.getElementById('height').value;

  if (!course || !type) {
    alert('Please select both course and content type.');
    return;
  }

  const url = `${baseUrl}/courses/${course}/fall-2025/${type}/embed/`;
  const iframeCode = `<iframe src="${url}" width="100%" height="${height}" frameborder="0" style="border: 1px solid #ccc; border-radius: 4px;"></iframe>`;

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