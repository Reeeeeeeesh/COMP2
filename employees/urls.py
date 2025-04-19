from django.urls import path
from .views import ping, upload_data, employees_list, calculate

urlpatterns = [
    path('ping/', ping, name='api-ping'),
    path('upload-data/', upload_data, name='upload-data'),
    path('employees/', employees_list, name='employees-list'),
    path('calculate/', calculate, name='calculate'),
]
