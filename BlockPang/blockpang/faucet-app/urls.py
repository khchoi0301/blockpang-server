from django.urls import path
from . import views


urlpatterns = [
  path('', views.index, name='index'),
  # path('test', views.test, name='test'),
  path('<str:to_address>/', views.req_icx, name='req_icx')
]