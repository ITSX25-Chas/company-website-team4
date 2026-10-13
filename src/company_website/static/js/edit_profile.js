const previewSignatureButton = document.getElementById('previewSignatureButton');
const emailSignatureInput = document.getElementById('email_signature');
const emailPreviewModal = document.getElementById('emailPreviewModal');
const emailPreviewContent = document.getElementById('emailPreviewContent');
const emailPreviewError = document.getElementById('emailPreviewError');

previewSignatureButton.addEventListener('click', async () => {
    emailPreviewError.hidden = true;
    emailPreviewContent.textContent = '';
    const previewData = new FormData();
    previewData.append('email_template', emailSignatureInput.value);
    previewData.append('csrf_token', document.querySelector('#profileEditForm [name=csrf_token]').value);

    try {
        const response = await fetch(previewSignatureButton.dataset.previewUrl, {
            method: 'POST',
            body: previewData,
            headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) throw new Error('Preview request failed');
        const result = await response.json();
        emailPreviewContent.textContent = result.preview;
    } catch (error) {
        emailPreviewError.hidden = false;
    }

    emailPreviewModal.showModal();
});

document.getElementById('emailPreviewClose').addEventListener('click', () => {
    emailPreviewModal.close();
});

emailPreviewModal.addEventListener('click', (event) => {
    if (event.target === emailPreviewModal) emailPreviewModal.close();
});
