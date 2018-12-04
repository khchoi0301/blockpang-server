from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('transfer', views.req_icx, name='req_icx'),
    path('leaderboard', views.get_highest_gscores, name='leaderboard'),
    path('wallet/create', views.create_wallet, name='create_wallet'),
    path('wallet/update', views.update_wallet, name='update_wallet'),
    path('admin/get_limit', views.get_limit, name='get_limit'),
    path('admin/set_limit/<int:amount_limit>/<int:block_limit>',
         views.set_limit, name='set_limit'),
    path('admin/update', views.update_admin, name='update_admin'),
    # path('admin/current_balance',
    #      views.get_current_balance, name='current_balance'),
    path('admin/stat', views.transfer_stat, name='transfer_stat'),
    # path('admin/stat/users', views.user_stat, name='user_stat'),
    path('admin/summary', views.get_summary, name='get_summary'),
    path('db/<str:table>', views.db_query, name='db_query'),
]
