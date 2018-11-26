from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('createwallet', views.createwallet, name='createwallet'),
    path('setlimit/<int:amountlimit>/<int:blocklimit>',
         views.setlimit, name='setlimit'),
    path('<str:to_address>/<int:value>', views.req_icx, name='req_icx')
]
