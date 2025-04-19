from django.urls import path
from . import views


urlpatterns = [
    path('', views.indexView, name='index'),
    path('form/', views.formView, name='form'),
    path('edit-model/<int:model_id>', views.editModelView, name='edit_model'),
    path('delete-model/<int:model_id>/', views.deleteModelView, name='delete_model'),
    path('contact/', views.contactFormView, name='contact'),

    path('donate/', views.donateView, name='donate'),
    path('donate/update-intent/', views.donateUpdatePaymentIntentView, name='donate_update_intent'), # Added

    path('buy-plan/', views.buyPlanView, name='buy_plan'),
    path('buy-plan/intent/', views.buyPlanPaymentIntentView, name='buy_plan_intent'),
    path('payment-success/', views.paymentSuccessView, name='payment_success'),
]