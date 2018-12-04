from django.urls import path
from django.conf.urls import url
from . import utils
from . import views
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='List of APIs')

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/current_balance', 
          views.get_current_balance, name='current_balance'),
    path('admin/get_limit', views.get_limit, name='get_limit'),
    path('admin/set_limit/<int:amount_limit>/<int:block_limit>',
         views.set_limit, name='set_limit'),
    path('admin/stat', views.transfer_stat, name='transfer_stat'),
    path('admin/stat/users', views.user_stat, name='user_stat'),
    path('admin/update', views.update_admin, name='update_admin'),
    path('db/<str:table>', views.db_query, name='db_query'),
    path('leaderboard', views.get_highest_gscores, name='leaderboard'),
    path('token', utils.get_token),
    path('transfer', views.req_icx, name='req_icx'),
    path('wallet/create', views.create_wallet, name='create_wallet'),
    path('wallet/update', views.update_wallet, name='update_wallet'),

    url(r'^docs/', include_docs_urls(title='List of APIs',
                                    authentication_classes=[],
                                    permission_classes=[],
                                    )),

     url(r'^api', schema_view)
]
