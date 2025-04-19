from django_recaptcha.fields import ReCaptchaField
from django.utils.translation import activate, gettext_lazy as _
from django_countries import countries

from django import forms
from .models import ModelName
from .utils import get_json_data

# Get SET of abbrevs OF stripe blocked countries JSON
BLOCKED_COUNTRIES = {entry["abbrev"] for entry in get_json_data("app_name/json/stripe_blocked_countries.json")}




class ModelForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = ModelName
        fields = ['title', 'country', 'captcha']




class ContactUsForm(forms.Form):

    TOPIC_CHOICES = [
        ('', '--- Select a topic ---'),
        ('auth_failure', 'I can\'t access my account'),
        ('auth_failure', 'I can\'t log in with my email address'),
        ('auth_failure', 'I can\'t log in with my username'),
        ('auth_failure', 'I can\'t log in with my TFA code'),
        ('impersonation', 'Someone is impersonating me'),
        ('report_user', 'User violates terms and conditions'),
        ('bug_report', 'A feature on a website is broken'),
        ('other', 'Other')
    ]

    email = forms.EmailField(label='Email', max_length=255)

    subject = forms.ChoiceField(
        label='Subject',
        choices=TOPIC_CHOICES,
        required=True
    )
    
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea,
        initial=''+
            'Hello, my name is: Forename Surname\n\n'+
            'I would like to report the following issue:',
        max_length=10000,
        min_length=250,
        required=True
    )

    captcha = ReCaptchaField()




class PlanForm(forms.Form):

    UNIT = '£'
    PLANS = {
        'basic': 12.25, # Hence, £12.25
        'standard': 25,
        'premium': 50
    }
    OPTION = [
        ('', '--- Select a plan ---'),
        ('basic', f'Basic: {UNIT}{PLANS.get('basic')}'),
        ('standard', f'Standard: {UNIT}{PLANS.get('standard')}'),
        ('premium', f'Premium: {UNIT}{PLANS.get('premium')}')
    ]

    plan = forms.ChoiceField(
        label='Plan',
        choices=OPTION,
        required=True
    )




class DonateForm(forms.Form):
    locale = 'pl' # code e.g. 'pl', 'gb', 'de'
    UNIT = 'zł'

    min_value = 5 # 5 -> 500 groszy (pennies)
    max_value = 100

    donation = forms.DecimalField(
        label='Kwota donacji',
        initial=min_value,
        min_value=min_value,
        max_value=max_value,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'placeholder': f'{min_value} do {max_value} zł',
            'class': 'p-Input-input Input Input-input--empty p-DonationAmountInput-input',
            'inputmode': 'numeric',
            'aria-required': 'true',
            'title': '',
            'id': 'Field-donationAmountInput',
        })
    )

    # CHOICES = [('PL', 'Poland'), ('GB', 'Great Britain') ...]
    country = forms.ChoiceField(
        label='Kraj',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'Input p-Select-select',
            'inputmode': 'text',
            'aria-required': 'true',
            'autocomplete': 'billing country',
            'title': '',
            'id': 'Field-countryInput',
        }),
        required=True
    )

    postal_code = forms.CharField(
        label='Kod pocztowy',
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': '12-345',
            'class': 'p-Input-input Input Input-input--empty p-PostalCodeInput-input',
            'inputmode': 'text',
            'aria-required': 'true',
            'data-country-parent': '#div_id_country',
            'autocomplete': 'billing postal-code',
            'title': '',
            'id': 'Field-postalCodeInput',
        }),
        required=True
    )

    """
    line_1 = forms.CharField(
        label='Adres - linia 1',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ulica',
            'class': 'p-Input-input Input Input-input--empty p-Line1Input-input',
            'inputmode': 'text',
            'aria-required': 'true',
            'autocomplete': 'billing line-1',
            'title': '',
            'id': 'Field-line1Input',
        }),
        required=True
    )

    line_2 = forms.CharField(
        label='Adres - linia 2',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Numer mieszkania',
            'class': 'p-Input-input Input Input-input--empty p-Line2Input-input',
            'inputmode': 'text',
            'aria-required': 'true',
            'autocomplete': 'billing line-2',
            'title': '',
            'id': 'Field-line2Input',
        }),
        required=True
    )

    city = forms.CharField(
        label='Miasto',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Warszawa',
            'class': 'p-Input-input Input Input-input--empty p-CityInput-input',
            'inputmode': 'text',
            'aria-required': 'true',
            'autocomplete': 'billing city',
            'title': '',
            'id': 'Field-cityInput',
        }),
        required=True
    )

    state = forms.CharField(
        label='Województwo',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Mazowieckie',
            'class': 'p-Input-input Input Input-input--empty p-StateInput-input',
            'inputmode': 'text',
            'aria-required': 'true',
            'autocomplete': 'billing state',
            'title': '',
            'id': 'Field-stateInput',
        }),
        required=True
    )"""

    class Meta:
        # Disclude the '*' suffix from the fields
        # NOTE: This does not work for crispy forms
        # Because crispy filters alter the, altered by Meta class, fields
        label_suffix = ''
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Generate country list in the correct language
        activate(self.locale)
        # Manually translate country names using Django's gettext
        self.fields['country'].choices = [
            (code, _(name))  # Wrap country name in gettext_lazy
            for code, name in countries if code not in BLOCKED_COUNTRIES
        ]

        # Select initial county (currently selected)
        self.fields['country'].initial = self.locale.upper()