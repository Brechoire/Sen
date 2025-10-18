from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.SignUpView.as_view(), name='signup'),
    path('connexion/', views.CustomLoginView.as_view(), name='login'),
    path('deconnexion/', views.CustomLogoutView.as_view(), name='logout'),
    path('profil/', views.profile_view, name='profile'),
    path('tableau-de-bord/', views.dashboard_view, name='dashboard'),
]
