// ============== Modal Management ==============

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.warn(`Modal with id "${modalId}" not found`);
        return;
    }
    
    // Remove hidden class and show with animation
    modal.classList.remove('hidden');
    modal.style.visibility = 'visible';
    modal.style.opacity = '0';
    modal.style.pointerEvents = 'none';
    
    // Force reflow
    void modal.offsetHeight;
    
    // Start entrance animation
    requestAnimationFrame(() => {
        modal.style.transition = 'opacity 200ms ease-out';
        modal.style.opacity = '1';
        modal.style.pointerEvents = 'auto';
        
        // Trigger glass effects if they exist
        const base = modal.querySelector('[data-glass-base]');
        if (base) {
            setTimeout(() => {
                base.style.opacity = '1';
            }, 50);
        }
        
        const layer = modal.querySelector('[data-glass-layer]');
        if (layer) {
            setTimeout(() => {
                layer.style.opacity = '1';
                layer.style.backdropFilter = 'blur(24px) saturate(1.8)';
                layer.style.webkitBackdropFilter = 'blur(24px) saturate(1.8)';
            }, 50);
        }
        
        // Show card
        const card = modal.querySelector('[data-modal-card]');
        if (card) {
            setTimeout(() => {
                card.style.transition = 'all 500ms cubic-bezier(0.22, 1, 0.36, 1)';
                card.style.opacity = '1';
                card.style.transform = 'scale(1) translateY(0)';
            }, 100);
        }
        
        // Show header, body, form with delays
        const header = modal.querySelector('[data-modal-header]');
        if (header) {
            setTimeout(() => {
                header.style.transition = 'all 400ms cubic-bezier(0.22, 1, 0.36, 1)';
                header.style.opacity = '1';
                header.style.transform = 'translateY(0)';
            }, 200);
        }
        
        const body = modal.querySelector('[data-modal-body]');
        if (body) {
            setTimeout(() => {
                body.style.transition = 'all 400ms cubic-bezier(0.22, 1, 0.36, 1)';
                body.style.opacity = '1';
                body.style.transform = 'translateY(0)';
            }, 300);
        }
        
        const form = modal.querySelector('[data-modal-form]');
        if (form) {
            setTimeout(() => {
                form.style.transition = 'all 400ms cubic-bezier(0.22, 1, 0.36, 1)';
                form.style.opacity = '1';
                form.style.transform = 'translateY(0)';
            }, 400);
        }
    });
    
    // Prevent body scrolling
    document.body.classList.add('overflow-hidden');
    document.body.style.pointerEvents = 'none';
    
    // Allow interaction with modal
    const modalContent = modal.querySelector('.relative.rounded-2xl, .relative.rounded-xl');
    if (modalContent) {
        modalContent.style.pointerEvents = 'auto';
    }
}

function closeModal(modal) {
    if (!modal) return;
    
    // Start exit animation
    modal.style.transition = 'opacity 300ms ease-out';
    modal.style.opacity = '0';
    
    // Hide card
    const card = modal.querySelector('[data-modal-card]');
    if (card) {
        card.style.transition = 'all 300ms cubic-bezier(0.22, 1, 0.36, 1)';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95) translateY(20px)';
    }
    
    // Hide glass effects
    const base = modal.querySelector('[data-glass-base]');
    if (base) {
        base.style.transition = 'opacity 200ms ease-out';
        base.style.opacity = '0';
    }
    
    const layer = modal.querySelector('[data-glass-layer]');
    if (layer) {
        layer.style.transition = 'all 300ms ease-out';
        layer.style.opacity = '0';
        layer.style.backdropFilter = 'blur(0px)';
        layer.style.webkitBackdropFilter = 'blur(0px)';
    }
    
    // After animation, hide completely
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.style.visibility = 'hidden';
        modal.style.pointerEvents = 'none';
    }, 350);
    
    // Restore body
    document.body.classList.remove('overflow-hidden');
    document.body.style.pointerEvents = '';

    // Delay the modal's deletion so that fadeout animations apply 
    setTimeout(() => { modal.remove(); }, 1000);
}

function hideModals() {
    document.querySelectorAll('[id$="-modal"]:not(.hidden)').forEach(modal => {
        closeModal(modal);
    });
}

// ============== Bounce Animation ==============

function bounceModal(modal) {
    if (!modal) return;
    
    const card = modal.querySelector('[data-modal-card]');
    if (!card) return;
    
    card.classList.remove('bounce');
    void card.offsetWidth;
    card.classList.add('bounce');
    
    setTimeout(() => {
        card.classList.remove('bounce');
    }, 600);
}

// ============== HTMX Auto-show ==============

document.addEventListener('htmx:afterSwap', function(event) {
    // Only process if the target is #modals
    if (event.detail.target.id !== 'modals') return;
    
    const modals = event.detail.target.querySelectorAll('[id$="-modal"]');
    modals.forEach(modal => {
        if (!modal.classList.contains('hidden')) {
            setTimeout(() => {
                openModal(modal.id);
            }, 100);
        }
    });
});

// ============== HTMX Event Handler for Form Validation ==============

document.addEventListener('htmx:afterRequest', async (event) => {
    // Get the triggering element
    const trigger = event.detail.triggeringElement;
    
    // SKIP if this request came from the Resend OTP button
    if (trigger?.classList.contains('resend-btn')) {
        console.log('Resend OTP request, skipping form handler');
        return;
    }
    
    // Also skip if the request path is for resend OTP
    if (event.detail.pathInfo?.requestPath?.includes('request-otp')) {
        console.log('Resend OTP path, skipping form handler');
        return;
    }

    
    const form = event.detail.target.closest('form');
    if (!form?.classList.contains('modal-footer')) return;

    const modal = form.closest('[id$="-modal"]');
    if (!modal) return;

    let xhr = event.detail.xhr;
    let responseText = await xhr.responseText;
    let response = '';

    if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
        try {
            response = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse JSON response', e);
            return;
        }
    } else {
        return;
    }

    let modal_body = modal.querySelector('[data-modal-body], .modal-body');
    let button_submit = form.querySelector('.modal-submit-button');
    let input_otp = form.querySelector('input[name="otp_code"]');

    if (response.error) {
        if (/Empty or mismatched|Mismatched/g.test(response.error)) {
            let msg = response.error;
            let err = '';
            let arg = '';

            arg = msg.replace(/Empty or mismatched|Mismatched/g, '').trim();
            err = msg.replace(arg, '').trim();
            msg += ': ' + response[arg];

            if (modal_body) {
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
            }

            if (button_submit) button_submit.setAttribute('disabled', '');
            if (input_otp) input_otp.setAttribute('disabled', '');
            console.error(msg);
        } else {
            console.error(response.error);
        }
    }

    if (response.success) { hideModals(); }
    else if (/Invalid OTP|Invalid password/g.test(response.error)) {
        let input = form.querySelector('input:not([type="hidden"])');
        if (input) {
            setInvalidInput(input);
        }
    }

    if (button_submit) {
        setNormalButtonForModal(button_submit);
    }
});

// ============== Click Outside Support - BOUNCE INSTEAD OF CLOSE ==============

document.addEventListener('click', function(e) {
    if (e.target.hasAttribute('data-modal-backdrop')) {
        const modal = e.target.closest('[id$="-modal"]');
        if (modal) bounceModal(modal);
    }
});

// ============== Input Helpers ==============

function setInvalidInput(input) {
    if (!input) return;
    input.classList.add('is-invalid', 'text-red-600', 'border-red-500');
    input.classList.remove('border-gray-300');
}

function setNormalInput(input) {
    if (!input) return;
    input.classList.remove('is-invalid', 'text-red-600', 'border-red-500');
    input.classList.add('border-gray-300');
}

// ============== Button Helpers (Tailwind) ==============

function setLoadingButtonForModal(button) {
    if (!button) return;
    const spinner = button.querySelector('.spinner-border, .animate-spin');
    const text = button.querySelector('.button-text');
    
    if (spinner) {
        // Remove sr-only/hidden to show spinner
        spinner.classList.remove('sr-only', 'hidden');
        spinner.classList.add('inline-block');
    }
    
    if (text) {
        // Store original text if not already stored
        if (!button.dataset.name) {
            button.dataset.name = text.innerHTML;
        }
        // Hide text
        text.classList.add('sr-only');
    }
    
    button.disabled = true;
}

function setNormalButtonForModal(button) {
    if (!button) return;
    const spinner = button.querySelector('.spinner-border, .animate-spin');
    const text = button.querySelector('.button-text');
    
    if (spinner) {
        // Hide spinner
        spinner.classList.add('sr-only', 'hidden');
        spinner.classList.remove('inline-block');
    }
    
    if (text && button.dataset.name) {
        // Restore text and show it
        text.innerHTML = button.dataset.name;
        text.classList.remove('sr-only');
    } else if (text) {
        text.classList.remove('sr-only');
    }
    
    button.disabled = false;
}

// ============== Clean up on page load ==============

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-bs-toggle="modal"], [data-bs-dismiss="modal"]').forEach(el => {
        el.removeAttribute('data-bs-toggle');
        el.removeAttribute('data-bs-dismiss');
    });
    
    document.querySelectorAll('[id$="-modal"]').forEach(modal => {
        if (!modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
        }
    });

    document.addEventListener('modal:closed', async (event) => {
        if (!event.detail.modalData) return;

        let xhr = event.detail.xhr;
        let responseText = await xhr.responseText;
        let response = '';

        if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
            try {
                response = JSON.parse(responseText);
            } catch (e) {
                console.error('Failed to parse JSON response', e);
                return;
            }
        }
        
        // Log the error to the console
        if (response.error)
             console.error(response.error, response);
        else console.log(response);


        // Early return for highlighting unverified fields.
        if (response.error != 'Unverified fields') return;
        const fields = response?.unverified_fields; if (!fields) return;
        // Every <input> has a unique identifier.
        // Hence, there should be one element with unique ID per template/page.
        for (fieldName of fields) {

            let field = document.querySelector(`input[id="id_${fieldName}"]`);
            // Skip if field already has unverified-field error message
            if (field.parentElement.querySelector('p[data-unverified-field]')) continue;


            let errCount = field.parentElement.querySelectorAll('p[id^=error]').length + 1;

            // Highlight field as invalid
            removeMatchingClasses(field, /^border-\w+-\d+$/); // utilities.js
            field.setAttribute('aria-invalid', true);
            field.classList.add('border-red-500');

            // Apply error message for unverified field
            let error = document.createElement('p'),
                text = document.createElement('strong');
            
            text.innerText = 'Unverified field. This field must pass OTP verification.';
            error.classList.add('text-red-500', 'text-xs', 'italic');

            error.id = `error_${errCount}_id_${fieldName}`;
            error.dataset.unverifiedField = '';
            error.append(text);
            field.parentElement.append(error);


            // Reset confirm password field
            document.querySelector('input[id="id_confirm_password"]').value = '';
            
            // library AView.js (show error and other hidden AV in-view elements)
            if (AV) AV.load('run');
        }
    });
});

// ============== Expose Globals ==============

window.openModal = openModal;
window.closeModal = closeModal;
window.hideModals = hideModals;
window.bounceModal = bounceModal;
window.setInvalidInput = setInvalidInput;
window.setNormalInput = setNormalInput;
window.setLoadingButtonForModal = setLoadingButtonForModal;
window.setNormalButtonForModal = setNormalButtonForModal;
