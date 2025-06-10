from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.urls import reverse

from .models import Profile
from .forms import (
    UserRegisterForm,
    UserUpdateForm,
    ProfileForm,
    AccountForm,
)
from .utils import (
    get_users_mfa_secret_as_qrcode_base64,
    email_otp_to_user,
    sms_otp_to_user,
)

import stripe, pyotp
stripe.api_key = settings.STRIPE_SECRET_KEY





@login_required
def enableMFAView(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    step = request.POST.get('step')
    switch = request.POST.get('switch')

    if request.user.account.mfa_enabled and switch:
        return JsonResponse({'error': 'MFA already enabled'}, status=400)
    if not request.user.account.mfa_enabled and not switch:
        return JsonResponse({'info': 'No action required'}, status=200)


    # Configuration
    # Note: changing STEPS order affects modals-display-sequence
    STEPS = ['password', 'otp_qrcode', 'otp_email', 'otp_sms']
    TITLE = 'Enable MFA'
    POST_URL = reverse('enable_mfa')
    CONTEXT_BASE = {
        'title': TITLE,
        'post_url': POST_URL,
    }


    # --- Prompt logged-in user TO Disable MFA ---
    
    if request.user.account.mfa_enabled and not switch:

        if step == 'password':
            # Validate password
            if not _validate_step(request, step):
                return JsonResponse({'error': _get_validation_error(step), 'step': step}, status=400)
            else:
                request.user.account.mfa_enabled = False
                request.user.account.save()
                return JsonResponse({'success': 'Disabled MFA'}, status=200)

        _reset_all_steps(request, STEPS)
        return render(request, 'users/modals/profile/include.html', {
            'title': 'Disable MFA',
            'post_url': reverse('enable_mfa'),
            'step': 'password',
            'submit': 'Disable',
            'submit_boldend': 'Multi-Factor Authentication',
        })

    # --- Show initial modal TO start verifying steps TO Enable MFA ---

    # If the step is invalid or it's the last step and all previous steps were completed,
    # it's likely the session data is outdated, so we restart the form.
    if step not in STEPS or (not _all_steps_completed(request, STEPS) and request.session[f'verified_{STEPS[-1]}'] == True):
        _reset_all_steps(request, STEPS)
        # If valid step and IS NOT a first step
        if step in STEPS and step != STEPS[0]:
            messages.info(request, f'Restarted the session for Enable MFA')

        return _render_step_modal(request, STEPS[0], STEPS, CONTEXT_BASE)
    

    # Validate current step
    if not _validate_step(request, step):
        return JsonResponse({'error': _get_validation_error(step), 'step': step}, status=400)

    # Mark step as verified
    request.session[f'verified_{step}'] = True

    # Handle step-specific post-validation actions
    _handle_post_validation(request, step)

    # Check if all steps are completed
    if _all_steps_completed(request, STEPS):
        request.user.account.mfa_enabled = True
        request.user.account.save()
        _reset_all_steps(request, STEPS)
        return JsonResponse({'success': 'Enabled MFA', 'step': step}, status=200)

    # Handle final step verification failure
    if step == STEPS[-1]:
        return JsonResponse({'error': 'Not all steps are verified', 'step': step}, status=400)

    # Proceed to next step
    next_step = STEPS[STEPS.index(step) + 1]
    return _render_step_modal(request, next_step, STEPS, CONTEXT_BASE)



def _reset_all_steps(request, steps):
    # Reset verification status
    for step_name in steps:
        request.session[f'verified_{step_name}'] = False


def _render_step_modal(request, step, all_steps, base_context):
    is_last_step = all_steps.index(step) == len(all_steps) - 1
    
    context = {
        **base_context,
        'step': step,
        'page': f'{all_steps.index(step) + 1}/{len(all_steps)}',
        'submit': 'Enable' if is_last_step else 'Proceed to the next step',
        'submit_boldend': 'Multi-Factor Authentication' if is_last_step else '',
    }
    
    if step == 'otp_qrcode':
        context['qrcode_data_uri'] = get_users_mfa_secret_as_qrcode_base64(request.user)
    return render(request, 'users/modals/profile/include.html', context)


def _validate_step(request, step):
    if step == 'password':
        password = request.POST.get('password')
        return request.user.check_password(password)
    else:
        otp = request.POST.get('otp_code')
        interval = {
            'otp_email': settings.OTP_EMAIL_INTERVAL,
            'otp_sms': settings.OTP_SMS_INTERVAL
        }.get(step, settings.OTP_DEFAULT_INTERVAL)

        totp = pyotp.TOTP(request.user.account.mfa_secret, interval=interval)
        return totp.verify(otp)


def _get_validation_error(step):
    return 'Invalid password' if step == 'password' else 'Invalid OTP'


def _handle_post_validation(request, step):
    if step == 'otp_qrcode':
        email_otp_to_user(request.user)
    elif step == 'otp_email':
        sms_otp_to_user(request.user)


def _all_steps_completed(request, steps):
    return all(request.session.get(f'verified_{step}', False) for step in steps)





@login_required
def requestOTPView(request, method):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    # Allow requests only from this Django project
    allowed_origins = ['http://localhost', 'http://127.0.0.1']

    origin = request.headers.get('Origin') or request.headers.get('Referer')
    if not origin or not any(origin.startswith(o) for o in allowed_origins):
        return JsonResponse({'error': 'Unauthorized request'}, status=403)


    # Send OTP to user via specified method: (email | sms)
    send_otp_via = {
        'email': email_otp_to_user,
        'sms': sms_otp_to_user
    }
    
    if method in send_otp_via:
        send_otp_via[method](request.user)
        return JsonResponse({'success': 'OTP Sent', 'method': method}, status=200)


    # Return invalid method error
    return JsonResponse({'error': 'Invalid method', 'method': method}, status=400)
 




def registerUserView(request):
    if request.method == 'POST':

        form_user = UserRegisterForm(request.POST)
        form_profile = ProfileForm(request.POST)

        if form_user.is_valid() and form_profile.is_valid():

            # Register the user, (and returns user instance)
            user = form_user.save()
            # Create Profile model for new user
            profile = form_profile.save(commit=False)
            profile.user = user
            profile.save()

            # Authenticate the user
            raw_password = form_user.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)

            messages.success(request, f'Created account: {user.username}')
           
            # Sign-in new user
            if user is not None:
                login(request, user)
                messages.success(request, f'Logged-in: {user.username}')
                return redirect('index')
            else:
                messages.error(request, 'Failed to login user')
                return redirect('login')
        else:
            messages.error(request, 'Invalid credentials!')
    else:
        form_user = UserRegisterForm()
        form_profile = ProfileForm()

    context = {
        'registry': True,
        'register_view_forms': {
            'user': form_user, 
            'profile': form_profile
        }
    }

    return render(request, 'users/form.html', context)





@login_required
def profileView(request, user_id):
    user_instance = get_object_or_404(User, pk=user_id)

    # Generate QR Code image to verify OTP for user's MFA
    qrcode_data_uri = get_users_mfa_secret_as_qrcode_base64(request.user)

    if request.method == 'POST' and request.user.id == user_instance.id:


        form_user = UserUpdateForm(
            request.POST,
            instance=user_instance
        )
        form_profile = ProfileForm(
            request.POST,
            request.FILES,
            instance=user_instance.profile
        )
        form_account = AccountForm(
            request.POST,
            instance=user_instance.account
        )


        if form_user.is_valid() and form_profile.is_valid() and form_account.is_valid():
            confirm_password = form_user.cleaned_data.get('confirm_password')
            
            if check_password(confirm_password, user_instance.password):
                form_user.save()
                form_profile.save()
                form_account.save()
                stripe.Customer.modify(
                    user_instance.account.stripe_customer_id,
                    name=user_instance.username,
                    email=user_instance.email
                )
                messages.success(request, 'Successfully updated profile')
            else:
                messages.error(request, 'Invalid password!')
                form_user.add_error('confirm_password', 'Invalid password')
        else:
            messages.error(request, 'Invalid credentials!')

    else:
        form_user = UserUpdateForm(instance=user_instance)
        form_profile = ProfileForm(instance=user_instance.profile)
        form_account = AccountForm(instance=user_instance.account)

    context = {
        'profile_user': user_instance,
        'qrcode_data_uri': qrcode_data_uri,
        'forms': {
            'user': form_user,
            'profile': form_profile,
            'account': form_account
        }
    }

    return render(request, 'users/profile.html', context)