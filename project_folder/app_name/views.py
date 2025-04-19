from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import escape

from urllib.parse import quote
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse

from django.views.generic import ListView
from users.utils import get_or_create_stripe_customer
from .models import ModelName
from .forms import (
    ModelForm,
    ContactUsForm,
    PlanForm,
    DonateForm
)

import stripe, json
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def is_model_creator(model_instance, user_instance):
    return model_instance.creator == user_instance



def get_request_with_valid_search_filter_parameters(request):
    """
    Converts posted form arguments, to permitted search url parameters.
    Additional parameters are filtered from the request copy: GET_copy.

    Returns:
        GET_copy (QueryDict) with valid parameters
    """

    # Note: requests are immutable, hence we need to create a mutable copy
    GET_copy = request.GET.copy()   # GET_copy is a mutable copy
    POST_copy = request.POST.copy() # POST_copy is a mutable copy

    # Remove 'creator_id_value' if 'creator_username_value' exists
    if  request.POST.get('creator_id_value') and request.POST.get('creator_username_value'):
        POST_copy.pop('creator_id_value')

    # Add parameters to copy of request GET
    for key, value in POST_copy.items():

        if key == 'search_query':
            GET_copy['search'] = value
        
        elif key == 'creator_id_value':
            try: # Remove invalid 'creator_id' parameter
                GET_copy['creator_id'] = int(value)
            except ValueError:
                messages.error(request, 'Creator\'s ID must be an Integer!')
        
        elif key == 'creator_username_value':
            GET_copy['creator'] = value

        elif key == 'country_code_value':
            GET_copy['country_code'] = value

    
    return GET_copy


def get_encoded_parameters_from_request(request):
    """
    Returns: parameters (as string), in URI Encoded form of a request (QueryDict).
    E.g. IN: request items, OUT: item1=value1&item2=Hello%20World
    """
    parameters = '&'.join([f"{key}={quote(str(value))}" for key, value in request.items()])
    return parameters


def http_response_redirect_with_parameters(path_name, parameters):
    new_url = reverse(path_name) + '?' + parameters
    return HttpResponseRedirect(new_url)











def indexView(request):

    context = {}
    R = request.GET

    # Handle POST request (search form submission)
    if request.method == 'POST':
        R = get_request_with_valid_search_filter_parameters(request)
        params = get_encoded_parameters_from_request(R)
        request.session['search_filter_params'] = params
        # Redirect to indexView with search filter parameters in URI
        return http_response_redirect_with_parameters('index', params)

    # Retrieve search parameters from session
    if 'search_filter_params' in request.session:
        context['search_filter_params'] = request.session['search_filter_params']




    # Get all models ordered by title
    model_list = ModelName.objects.all().order_by('title')
    # Filter search_models based on request parameters
    search_models = model_list
    
    for key, value in R.items():
        if not value:
            continue
        if key == 'search':
            search_models = search_models.filter(title__icontains=value)
        elif key == 'country_code':
            search_models = search_models.filter(country=value)
        elif key == 'creator_id':
            search_models = search_models.filter(creator=value)
        elif key == 'creator':
            search_models = search_models.filter(creator__username__icontains=value)

    # Get other_models (irrelevant to search)
    search_models_ids = search_models.values_list('id', flat=True)
    other_models = model_list.exclude(id__in=search_models_ids)




    # Paginate 'search_models' and 'other_models'
    paginator_search = Paginator(search_models, 5)
    paginator_other = Paginator(other_models, 5)
    
    # Get page number from request
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1



    # Start of - Determine which paginator to use -----------------------------------------

    if page_number <= paginator_search.num_pages:
        # Get relevant to search results. (models = search_models)
        models = paginator_search.get_page(page_number)
        models_type = 'search_relevant'
        

    elif page_number <= paginator_search.num_pages + paginator_other.num_pages:
        # Get irrelevant to search results. (models = other_models)
        page_number_other = page_number - paginator_search.num_pages
        models = paginator_other.get_page(page_number_other)
        models_type = 'search_irrelevant'

        # One time message - End of relevant search results
        if page_number == paginator_search.num_pages + 1:
            context.update({
                'start_other_models_message': True
            })

    else:
        models = False
        models_type = False
        next_page_number = False

    # END of - Determine which paginator to use -------------------------------------------



    # Update context
    context.update({
        'models': models,
        'models_type': models_type,
        'next_page_number': page_number + 1,
    })

    # Render the appropriate template
    template = 'app_name/extensions/models_list.html' if request.htmx else 'app_name/index.html'
    
    return render(request, template, context)









@login_required
def formView(request): # createModelView
    if request.method == 'POST':
        form = ModelForm(request.POST)
        if form.is_valid():
            model_instance = form.save(commit=False)
            model_instance.creator = request.user
            model_instance.save()

            messages.success(request, 'Model created successfully!')
            return redirect('index')
        else:
            messages.error(request, 'Failed to create new model!')
    else:
        form = ModelForm()

    return render(request, 'app_name/form.html', {'form': form})




@login_required
def editModelView(request, model_id):
    model_instance = get_object_or_404(ModelName, pk=model_id)    
    
    if not is_model_creator(model_instance, request.user):
        messages.error(request, 'You are not the owner of this model')
        return redirect('index')

    if request.method == 'POST':
        form = ModelForm(request.POST, instance=model_instance)

        if form.is_valid():
            messages.success(request,  f'Updated model: {model_instance.title}')
            form.save() # ← Updates Model
            return redirect('index')
        else:
            messages.error(request,  f'Failed to update model: {model_instance.title}')
    else:
        form = ModelForm(instance=model_instance)

    return render(request, 'app_name/form.html', {'form': form})




@login_required
def deleteModelView(request, model_id):
    model_instance = get_object_or_404(ModelName, pk=model_id)

    if not is_model_creator(model_instance, request.user):
        messages.error(request, 'You are not the owner of this model')
        return redirect('index')

    model_instance.delete()

    messages.warning(request, f'Deleted model: {model_instance.title}')

    return redirect('index')





def email_client_and_support_team(email, subject, message):
    
    # Escape HTML tags to treat them as plain text
    escaped_message = escape(message)

    # Replace newline characters with <br> for the HTML content
    html_message = escaped_message.replace('\n', '<br>')

    recipient_message = (
        '<p style="color: rgb(95,95,95);font-family: &quot;Indeed Sans&quot; , &quot;Noto Sans&quot; , Helvetica , Arial , sans-serif;font-size: 14.0px;font-weight: normal;line-height: 24.0px;margin: 0;padding: 0;direction: ltr;">'
        '<strong>You have sent the following message to our support team:</strong><br><br>'
        f'{html_message}<br><br>'
        '<strong>Our support team will get back to you as soon as possible.</strong><br>'
        '<strong>Feel free to ignore this email if it wasn\'t you.</strong>'
        '</p>'
    )

    # Send HTML email to recipient
    email_to_recipient = EmailMultiAlternatives(
        subject=f"Support Request: {subject}",
        body=recipient_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[email]
    )

    # Send email to recipient
    email_to_recipient.attach_alternative(recipient_message, "text/html")
    email_to_recipient.send()

    # Send email to support team
    send_mail(
        subject=f'Support Request: {subject}',
        message=f'{message}\n\nRequest from (Email): {email}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=['support@walentynki.site']
    )


def contactFormView(request):

    if request.method == 'POST':
        form = ContactUsForm(request.POST)

        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            email = form.cleaned_data['email']
            
            email_client_and_support_team(email, subject, message)

            messages.success(request, 'Message sent successfully!')
            messages.info(request, f'Our support team will contact you shortly at: {email}')

            # Reset some fields to their default values
            initial_data = form.cleaned_data.copy()
            initial_data['subject'] = ContactUsForm.TOPIC_CHOICES[0][0]
            initial_data['message'] = ContactUsForm.base_fields['message'].initial

            form = ContactUsForm(initial=initial_data)

        else:
            messages.error(request, 'Failed to send message!')
    else:
        form = ContactUsForm()

    return render(request, 'app_name/contact.html', {'form': form})




@login_required
def donateView(request):

    form = DonateForm()
    min_value = form.fields['donation'].min_value

    context = {
        'form': form,
        'locale': DonateForm.locale,
        'payment_unit': DonateForm.UNIT,
        'display_price': min_value, # 5 -> 5,00zł
        'stripe_public': settings.STRIPE_PUBLIC_KEY
    }

    # Retrieve the user's Stripe customer ID from its profile
    stripe_customer_id = get_or_create_stripe_customer(request.user)

    intent = stripe.PaymentIntent.create(
        amount=int(min_value * 100),
        currency='pln',
        customer=stripe_customer_id,
        payment_method_types=[
            'card', #"paypal", "p24", "klarna", "google_pay", "apple_pay"
        ],
        description=f'Donation',
    )

    request.user.profile.stripe_last_intent_id = intent.id
    request.user.profile.save()

    context.update({
        'client_secret': intent.client_secret
    })

    return render(request, 'app_name/donate.html', context)



@login_required
def donateUpdatePaymentIntentView(request):

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request, expected POST'}, status=400)

    form = DonateForm(request.POST)

    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form', 'form_errors': form.errors}, status=400)


    donation = form.cleaned_data.get('donation')

    # Note: amount is in groszy (PLN)
    intent = stripe.PaymentIntent.modify(
        id=request.user.profile.stripe_last_intent_id,
        amount=int(donation * 100),
        metadata={'donation': str(donation)}
    )

    return JsonResponse({'success': 'Updated payment intent', 'donation': donation}, status=200)





@login_required
def buyPlanView(request):
    
    context = {
        'form': PlanForm(),
        'plans': PlanForm.PLANS,
        'payment_unit': PlanForm.UNIT,
        'display_price': 0, # initial price to be displayed
        'stripe_public': settings.STRIPE_PUBLIC_KEY
    }

    return render(request, 'app_name/buy_plan.html', context)






@login_required
def buyPlanPaymentIntentView(request):

    form = PlanForm(request.POST)
    
    # Validate plan from POST request
    if request.method == 'POST' and form.is_valid():
        plan = request.POST.get('plan')
    else:
        return JsonResponse({'error': 'Invalid form, try refreshing the page'}, status=400)
    if plan not in PlanForm.PLANS.keys():
        return JsonResponse({'error': 'Selected plan is not registered, please report this issue'}, status=400)

    # Retrieve the user's Stripe customer ID from its profile
    stripe_customer_id = get_or_create_stripe_customer(request.user)
    # Stripe's amount is in pennies. Hence, amount=500 → £5.00
    amount = int(PlanForm.PLANS.get(plan) * 100)

    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency="gbp",
        customer=stripe_customer_id,
        payment_method_types=["card"],
        description=f"Purchased '{plan}' plan",
        metadata={"purchased_plan": str(plan)}
    )

    return JsonResponse({'client_secret': intent.client_secret})


def paymentSuccessView(request):
    return render(request, 'app_name/payment_success.html')



"""
@login_required
def paymentFormView(request):

    try:
        intent = stripe.PaymentIntent.create(
            amount=1000, # In pennies hence amount=500 → £5.00
            currency="pln",
            #automatic_payment_methods={"enabled": True},
            payment_method_types=[
                # additional payment methods:
                #   apple_pay, google_pay, amazon_pay ...
                # NOTE: Apple Pay, Google Pay, Link, PayPal, and Amazon Pay require domains to be added
                'card',
                'paypal',
                #'revolut_pay',
                'p24',
                #'klarna'
            ],
        )
    except stripe.error.StripeError as e:
        messages.error(request, f'Failed to create payment intent: {e}')
        return redirect('index')

    # payment_method_types:    https://docs.stripe.com/payments/paypal
    # payment method settings: https://dashboard.stripe.com/test/settings/payment_methods/pmc_1QxSfaCMc3sguBOiAOlb0yd5
    # payment dashboard:       https://dashboard.stripe.com/account/payments/settings

    if request.method == 'POST':

        #customer = stripe.Customer.create(
        #    email=request.user.email,
        #    name=request.user.username,
        #    address={
        #        country=request.POST.get('country'),
        #        postal_code=request.POST.get('postalCode')
        #    }
        #    source=request.POST.get('stripeToken')
        #)
        #charge = stripe.Charge.create(
        #    customer,
        #    amount=int(amount * 100), # amount=500 → $5.00
        #    currency=intent.currency,
        #    description='My description'
        #)

        messages.success(request, 'Payment successful!')
        return redirect('success', args=option)


    context = {
        'display_price': intent.amount / 100, # Convert pennies to pounds
        'client_secret': intent.client_secret,
        'stripe_public': settings.STRIPE_PUBLIC_KEY
    }

    return render(request, 'app_name/payment.html', context)


"""