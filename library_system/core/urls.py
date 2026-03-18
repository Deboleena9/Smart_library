from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'), # The main login page
    path('librarian/', views.librarian_dashboard, name='librarian'),
    path('student/', views.student_portal, name='student'),
]