from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse


from .models import Profile, Account
from .forms import (
    UserRegisterForm,
    UserUpdateForm,
    ProfileForm,
    AccountForm,
)
from .utils.throttle import ThrottleOTPRequestExpiryDate as OTPThrottle
from .utils import (
    get_users_mfa_secret_as_qrcode_base64,
    email_otp_to_user,
    sms_otp_to_user,
    mask_email,
    mask_phone_number,
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
        return render(request, 'users/includes/modal.html', {
            'path': '',
            'title': 'Disable MFA',
            'post_url': reverse('enable_mfa'),
            'step': 'password',
            'submit': 'Disable',
            'submit_boldend': 'Multi-Factor Authentication',
        })

    # --- Show initial modal TO start verifying steps TO Enable MFA ---

    # If the step is invalid or it's the last step and all previous steps were completed,
    # it's likely the session data is outdated, so we restart the form.
    if step not in STEPS or (
        not _all_steps_completed(request, STEPS)
        and request.session.get(f'verified_{STEPS[-1]}', False)
    ):
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
        # Enable MFA
        request.user.account.mfa_enabled = True
        request.user.account.save()
        # Clear used session data
        _reset_all_steps(request, STEPS)
        OTPThrottle.remove_session(request)
        # Generate response AND clear used cookie data
        response = JsonResponse({'success': 'Enabled MFA', 'step': step}, status=200)
        OTPThrottle.remove_cookie(response)
        return response

    # Handle final step verification failure
    if step == STEPS[-1]:
        return JsonResponse({'error': 'Not all steps are verified', 'step': step}, status=400)

    # Proceed to next step
    next_step = STEPS[STEPS.index(step) + 1]
    return _render_step_modal(request, next_step, STEPS, CONTEXT_BASE)



def _reset_all_steps(request, steps):
    # Reset verification status by removing it from the session
    for step_name in steps:
        session_key = f'verified_{step_name}'
        if session_key in request.session:
            del request.session[session_key]


def _render_step_modal(request, step, all_steps, base_context):
    is_last_step = all_steps.index(step) == len(all_steps) - 1
    
    context = {
        **base_context,
        'path': 'mfa/' if step != 'password' else '',
        'step': step,
        'page': f'{all_steps.index(step) + 1}/{len(all_steps)}',
        'submit': 'Enable' if is_last_step else 'Proceed to the next step',
        'submit_boldend': 'Multi-Factor Authentication' if is_last_step else '',
    }
    if step == 'otp_qrcode':
        context['qrcode_data_uri'] = get_users_mfa_secret_as_qrcode_base64(request.user)
        
    elif step != 'password':
        # Include OTP_REQUEST_THROTTLE_INTERVAL used in resend_otp.html <component>
        context['OTP_REQUEST_THROTTLE_INTERVAL'] = settings.OTP_REQUEST_THROTTLE_INTERVAL

    response = render(request, 'users/includes/modal.html', context)
    # Set throttle OTP request (cookie)
    # Keep cookie updated in case of manual removal to prevent 'counter' issues
    OTPThrottle.set_cookie(request, response)

    return response


def _validate_step(request, step, user=None):
    user = user if user is not None else request.user
    if not user:
        raise ValueError('User not identified')

    if step == 'password':
        password = request.POST.get('password')
        return user.check_password(password)
    else:
        otp = request.POST.get('otp_code')
        interval = {
            'otp_email': settings.OTP_EMAIL_INTERVAL,
            'otp_sms': settings.OTP_SMS_INTERVAL
        }.get(step, settings.OTP_DEFAULT_INTERVAL)

        totp = pyotp.TOTP(user.account.mfa_secret, interval=interval)
        return totp.verify(otp)


def _get_validation_error(step):
    if step == 'password':
        return 'Invalid password'
    elif 'otp_' in step:
        return 'Invalid OTP'
    else:
        return 'Invalid step' 


def _handle_post_validation(request, step):
    # TRED = Throttle Request Expiry-Date
    tred_expired = OTPThrottle.has_expired(request)
    expiry_date = OTPThrottle.get(request, source='session')

    # Throttle OTP request (via session)
    if not tred_expired and step in ['otp_qrcode', 'otp_email']:
        response = JsonResponse({'error': 'Throttle by expiry_date', 'expiry_date': expiry_date}, status=400)
        # Keep cookie updated in case of manual removal to prevent 'counter' issues
        OTPThrottle.set_cookie(request, response)
        return response

    # Set throttle OTP request (session)
    if tred_expired and step in ['otp_qrcode', 'otp_email']:
        OTPThrottle.set_session(request)

    # Send OTP to user via specified step
    if step == 'otp_qrcode':
        email_otp_to_user(request.user)
    elif step == 'otp_email':
        sms_otp_to_user(request.user)


def _all_steps_completed(request, steps):
    return all(request.session.get(f'verified_{step}', False) for step in steps)






def requestOTPView(request, method):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    expiry_date = OTPThrottle.get(request, source='session')
    send_otp_via = {'email': email_otp_to_user, 'sms': sms_otp_to_user}
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')

    # Allow requests only from CORS_ALLOWED_ORIGINS
    if not origin or not any(origin.startswith(o) for o in settings.CORS_ALLOWED_ORIGINS):
        return JsonResponse({'error': 'Unauthorized request'}, status=403)
    # Return invalid method error
    if method not in send_otp_via:
        return JsonResponse({'error': 'Invalid method', 'method': method}, status=400)
    # Get User ID
    if not user_id:
        return JsonResponse({'error': 'User not identified', 'user_id': user_id}, status=400)
    # Throttle OTP request (via session)
    if not OTPThrottle.has_expired(request):
        response = JsonResponse({'error': f'Throttle by expiry_date {expiry_date}', 'expiry_date': expiry_date}, status=400)
        # Keep cookie updated in case of manual removal to prevent 'counter' issues
        OTPThrottle.set_cookie(request, response)
        return response
    

    # Send OTP to user via specified method: (email | sms)
    user_instance = get_object_or_404(User, id=user_id)
    send_otp_via[method](user_instance)

    # Set throttle OTP request (session)
    OTPThrottle.set_session(request)

    # Generate response AND set throttle OTP request (cookie)
    response = JsonResponse({'success': 'OTP Sent', 'method': method}, status=200)
    OTPThrottle.set_cookie(request, response)

    return response
 




def requestMFAModalView(request, modal):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    MODALS = ['otp_qrcode', 'otp_email', 'otp_sms']
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')

    # Allow requests only from CORS_ALLOWED_ORIGINS
    if not origin or not any(origin.startswith(o) for o in settings.CORS_ALLOWED_ORIGINS):
        return JsonResponse({'error': 'Unauthorized request'}, status=403)
    # Validate requested modal
    if modal not in MODALS:
        return JsonResponse({'error': 'Invalid modal'}, status=400)
    # Get User ID
    if not user_id:
        return JsonResponse({'error': 'User not identified'}, status=400)


    # None ➡ <input value="None"> ➡ "None" (Type: String)
    next_url = request.POST.get('next')
    next_url = None if next_url in ['None', 'null', 'False'] else next_url


    tred_expired = OTPThrottle.has_expired(request)
    user_instance = get_object_or_404(User, id=user_id)

    # Throttle OTP request (via session)
    # ELSE Send OTP to user (via specified modal)
    if tred_expired:
        if modal == 'otp_email':
            email_otp_to_user(user_instance)
        elif modal == 'otp_sms':
            sms_otp_to_user(user_instance)

    # Set throttle OTP request (session)
    if tred_expired and modal != 'otp_qrcode':
        OTPThrottle.set_session(request)


    # Create the modal
    _reset_all_steps(request, MODALS)
    response = render(request, 'users/includes/modal.html', {
        'path': 'mfa/',
        'title': 'Multi-Factor Authentication',
        'post_url': reverse('login'),
        'step': modal,
        'submit': 'Login',
        'submit_boldend': 'Securly via MFA',
        # HX-POST data (in circulation)
        'next': next_url,
        'user_id': request.POST.get('user_id'),
        'email': request.POST.get('masked_email'),
        'phone_number': request.POST.get('masked_phone_number'),
        # Include OTP_REQUEST_THROTTLE_INTERVAL used in resend_otp.html <component>
        **({'OTP_REQUEST_THROTTLE_INTERVAL': settings.OTP_REQUEST_THROTTLE_INTERVAL} 
        if modal != 'otp_qrcode' else {})
    })


    # Set throttle OTP request (cookie)
    if modal != 'otp_qrcode':
        # Keep cookie updated in case of manual removal to prevent 'counter' issues
        OTPThrottle.set_cookie(request, response)

    return response





class CustomLoginView(LoginView):
    template_name = 'users/form.html'
    STEPS = ['password', 'otp_qrcode', 'otp_email', 'otp_sms']


    def success_redirect(self):
        # HTMX requests ruin the default redirection. Hence,
        # success_redirect() method is used to fix this issue.
        success_url = self.get_success_url()

        if self.request.headers.get('HX-Request') == 'true':
            # HTMX-aware response
            response = HttpResponse()
            response['HX-Redirect'] = success_url
            return response
        else:
            # Normal browser redirect 
            return redirect(success_url)


    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        step = request.POST.get('step')
        # Call multi_factor_auth() custom method
        # IF POST request was made by the "Multi-Factor Authentication" modal
        if step in self.STEPS and step != 'password':
            return self.multi_factor_auth(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)



    def multi_factor_auth(self, request, *args, **kwargs):

        # Validate - "session" data

        if request.session.get('verified_password') != True:
            return JsonResponse({'error': 'Unverified password'}, status=400)

        user_id = request.session.get('user_id')
        user_id = str(user_id) if user_id is not None else None
        user_id_post = request.POST.get('user_id')

        if not user_id or user_id != user_id_post:
            return JsonResponse({'error': 'Empty or mismatched user_id', 'user_id': user_id}, status=400)
        
        next_url = request.session.get('next')
        # None ➡ <input value="None"> ➡ "None" (Type: String)
        next_url_post = request.POST.get('next')
        next_url_post = None if next_url_post in ['None', 'null', 'False'] else next_url_post

        if next_url != next_url_post:
            return JsonResponse({'error': 'Mismatched next_url', 'next_url': next_url}, status=400)

        # Validate - "Multi-Factor Authentication" data

        user = get_object_or_404(User, id=user_id)
        if hasattr(user, 'account') and user.account.mfa_enabled != True:
            return JsonResponse({'error': 'Disabled MFA'}, status=400)

        step = request.POST.get('step')
        if not _validate_step(request, step, user):
            return JsonResponse({'error': _get_validation_error(step), 'step': step}, status=400)

        # Reset used session & cookie data AND authenticate the user
        
        del self.request.session['next']
        del self.request.session['user_id']
        _reset_all_steps(request, self.STEPS)
        OTPThrottle.remove_session(self.request)

        login(self.request, user)

        response = self.success_redirect()
        OTPThrottle.remove_cookie(response)
        return response



    def form_valid(self, form):
        # Return "Multi-Factor Authentication" modal IF user has enabled MFA
        # Otherwise, authenticate the user
        user = form.get_user()
        request = self.request

        if hasattr(user, 'account') and user.account.mfa_enabled:
            # Note: POST data (in circulation) includes some session data
            # These are used later to check if POST data matches the session
            _reset_all_steps(request, self.STEPS)
            request.session[f'user_id'] = user.id
            request.session[f'verified_password'] = True
            request.session[f'next'] = request.GET.get('next')

            return render(request, 'users/includes/modal.html', {
                'path': 'mfa/',
                'title': 'Multi-Factor Authentication',
                'post_url': reverse('login'),
                'step': 'otp_qrcode',
                'submit': 'Login',
                'submit_boldend': 'Securly via MFA',
                # Initial data for, in circulation, HX-POST requests
                'user_id': user.id,
                'next': request.GET.get('next'),
                'email': mask_email(user.email),
                'phone_number': mask_phone_number(str(user.account.phone_number)),
            })
            
        else:
            login(self.request, user)
            return self.success_redirect()





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
            # Create Account model for new user
            account = Account.objects.create(user=user)
            account.initialize()

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
            'profile': form_profile,
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