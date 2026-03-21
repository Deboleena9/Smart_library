from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('librarian/', views.librarian_dashboard, name='librarian'),
    path('student/', views.student_portal, name='student'),
    path('issue/', views.issue_book, name='issue_book'), # <-- ADD THIS LINE
]