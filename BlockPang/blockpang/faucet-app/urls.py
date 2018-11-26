from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('createwallet', views.createwallet, name='createwallet'),
    path('<str:to_address>/', views.req_icx, name='req_icx')
]
