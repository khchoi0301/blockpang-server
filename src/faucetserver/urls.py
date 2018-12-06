from django.urls import path
from . import utils_admin, utils_db, utils_wallet, views


urlpatterns = [
    path('', views.index),
    path('admin/get_limit', views.get_limit),
    path('admin/set_limit', views.set_limit),
    path('admin/update', views.update_admin),
    path('db/stat', views.transfer_stat),
    path('db/<str:table>', views.db_query),
    path('wallet/create', views.create_wallet),
    path('wallet/update', views.update_wallet),
    path('token', utils_admin.get_token),
    path('transfer', views.req_icx),
]
