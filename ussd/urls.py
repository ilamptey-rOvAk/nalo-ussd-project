from django.urls import path
from . import views

urlpatterns = [
    path('', views.ussd_handler, name='ussd_handler'),
]
