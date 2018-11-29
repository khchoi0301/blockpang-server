from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_wallet', views.create_wallet, name='create_wallet'),
    path('get_limit', views.get_limit, name='get_llimit'),
    path('set_limit/<int:amount_limit>/<int:block_limit>',
         views.set_limit, name='set_limit'),
    path('<str:to_address>/<int:value>', views.req_icx, name='req_icx'),
    path('transaction', views.query_transaction, name='transaction'),
    path('users', views.query_user, name='user')
]
