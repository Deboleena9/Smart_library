from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('librarian/', views.librarian_dashboard, name='librarian'),
    path('student/', views.student_portal, name='student'),
    path('issue/', views.issue_book, name='issue_book'),
    path('return/<uuid:transaction_id>/', views.return_book, name='return_book'),
    path('logout/', views.logout_user, name='logout'),
    path('setup-admin/', views.setup_admin, name='setup_admin'),
    path('manage-books/', views.manage_books, name='manage_books'),
    path('manage-students/', views.manage_students, name='manage_students'),
    path('manage-issues/', views.manage_issues, name='manage_issues'),
    
    # NEW DELETE ROUTE
    path('delete-student/<uuid:student_id>/', views.delete_student, name='delete_student'),
    # Add this right below your delete_student route
    path('delete-book/<uuid:book_id>/', views.delete_book, name='delete_book'),
    # Add this to your urlpatterns
    path('settings/', views.manage_settings, name='manage_settings'),

    
]