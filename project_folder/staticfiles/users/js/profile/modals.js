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

    let modal_body = form.parentElement.querySelector('.modal-body'),
        button_submit = form.querySelector('.modal-submit-button'),
        input_otp = form.querySelector('input[name="otp_code"]');


    if (response.error) {
        // Report ERROR to the console & technical report <details>
        if (/Empty or mismatched|Mismatched/g.test(response.error)) {
            let msg = response.error, err = arg = '';

            arg = msg.replace(/Empty or mismatched|Mismatched/g, '').trim();
            err = msg.replace(arg, '').trim();
            msg += ': ' + response[arg];

            modal_body.innerHTML = `
                <p>Something went wrong, please restart or try again later.</p>
                <hr>
                <details open>
                    <summary>Technical Report</summary>
                    <span class="badge bg-danger">ERROR ${xhr.status}</span>
                    <span class="badge bg-warning text-dark">${err}</span>
                    <span class="badge bg-secondary">ARG ${arg}</span>
                    <span class="badge bg-light text-dark">ISET ${response[arg]}</span>
                </details>
            `;
    
            // Report ERROR & Disable - OTP <input> & Submit <button>
            button_submit.setAttribute('disabled', '');
            input_otp.setAttribute('disabled', '');
            console.error(msg);
        }
        else {
            console.error(response.error);
        }
    }


    if (response.success) {
        hideModals();
    }
    else if (/Invalid OTP|Invalid password/g.test(response.error)) {
        let input = form.querySelector('input:not([type="hidden"])');
        setInvalidInput(input);
    }


    // Reset modal's submit button

    setNormalButtonForModal(button_submit);

});