from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='index'),
    path('a-propos/', views.a_propos, name='a_propos'),
    path('contact/', views.contact, name='contact'),
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),
    path('politique-confidentialite/', views.politique_confidentialite, name='politique_confidentialite'),
    path('conditions-generales-vente/', views.conditions_generales_vente, name='conditions_generales_vente'),
]
