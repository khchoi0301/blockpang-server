from django.urls import path
from . import utils_admin, utils_db, utils_wallet, views


urlpatterns = [
    path('', views.index),
    path('admin/get_limit', views.get_limit),
    path('admin/set_limit', views.set_limit),
    path('admin/update', views.update_admin),
    path('db/stat', views.transfer_stat),
    path('db/leaderboard', views.get_highest_gscores),
    path('db/<str:table>', views.db_query),
    path('wallet/create', views.create_wallet),
    path('wallet/update', views.update_wallet),
    path('transfer', views.req_icx),
]
