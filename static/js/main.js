document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('downloadForm');
    const urlInput = document.getElementById('url');
    const pasteButton = document.getElementById('pasteButton');
    const downloadButton = document.getElementById('downloadButton');
    const spinner = downloadButton.querySelector('.spinner-border');
    const buttonText = downloadButton.querySelector('.button-text');
    const alert = document.getElementById('alert');
    const thankYouMessage = document.getElementById('thankYouMessage');

    // Paste button functionality
    pasteButton.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            urlInput.value = text;
        } catch (err) {
            showAlert('Please paste the URL manually', 'warning');
        }
    });

    // Form submission handling
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Reset messages
        hideAlert();
        hideThankYou();

        // Show loading state
        setLoading(true);

        try {
            const formData = new FormData(form);
            const response = await fetch('/download', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to download video');
            }

            // Get filename from response headers
            const contentDisposition = response.headers.get('content-disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1].replace(/['"]/g, '')
                : 'instagram_video.mp4';

            // Create blob from response
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Create temporary link and trigger download
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            // Show thank you message
            showThankYou();
            form.reset();
        } catch (error) {
            showAlert(error.message, 'danger');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        downloadButton.disabled = isLoading;
        spinner.classList.toggle('d-none', !isLoading);
        buttonText.classList.toggle('d-none', isLoading);
    }

    function showAlert(message, type) {
        alert.textContent = message;
        alert.className = `alert alert-${type} mt-3`;
        alert.classList.remove('d-none');
    }

    function hideAlert() {
        alert.classList.add('d-none');
    }

    function showThankYou() {
        thankYouMessage.classList.remove('d-none');
        setTimeout(() => {
            hideThankYou();
        }, 5000);
    }

    function hideThankYou() {
        thankYouMessage.classList.add('d-none');
    }
});