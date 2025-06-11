const modals = document.getElementById('modals');


function hideModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        const Modal = bootstrap.Modal.getOrCreateInstance(modal);
              Modal.hide();
    });
}
function setInvalidInput(input) {
    input.classList.add('is-invalid');
    input.classList.add('text-danger');
}
function setNormalInput(input) {
    input.classList.remove('is-invalid');
    input.classList.remove('text-danger');
}
function setLoadingButtonForModal(button) {
    button.querySelector('.spinner-grow').classList.remove('visually-hidden');
    button.querySelector('.button-text').innerText = 'loading...';
}
function setNormalButtonForModal(button) {
    button.querySelector('.spinner-grow').classList.add('visually-hidden');
    button.querySelector('.button-text').innerHTML = button.dataset.name;
}


document.addEventListener('htmx:afterRequest', async (event) => {

    let form = event.detail.target.closest('form');
    if (!form?.classList.contains('modal-footer')) return;


    // Receive response from the backend

    let xhr = event.detail.xhr,
        responseText = await xhr.responseText,
        response = '';

    if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
        response = JSON.parse(responseText);
    }
    else return;


    // Handle response

    if (response.error) {
        console.error(response.error);
    }
    if (response.success) {
        hideModals();
    }
    else if (response.error === 'Invalid OTP' || 'Invalid password') {
        let input = form.querySelector('input:not([type="hidden"])');
        setInvalidInput(input);
    }


    // Reset modal's submit button

    let button_submit = form.querySelector('.modal-submit-button');
    setNormalButtonForModal(button_submit);

});