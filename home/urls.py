from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='index'),
    path('a-propos/', views.a_propos, name='a_propos'),
]
