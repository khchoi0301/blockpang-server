from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/update/<str:cmd>/<str:email>',
         views.update_admin, name='update_admin'),
    path('admin/current_balance',
          views.get_current_balance, name='current_balance'),
    path('create_wallet', views.create_wallet, name='create_wallet'),
    path('get_limit', views.get_limit, name='get_limit'),
    path('set_limit/<int:amount_limit>/<int:block_limit>',
         views.set_limit, name='set_limit'),
    path('<str:to_address>/<int:value>', views.req_icx, name='req_icx'),
    path('db/transaction', views.query_transaction, name='transaction'),
    path('db/users', views.query_user, name='user'),
]
