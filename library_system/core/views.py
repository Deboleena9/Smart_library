from django.shortcuts import render
from .models import Book, Transaction

def login_view(request):
    return render(request, 'index.html')

def librarian_dashboard(request):
    # Count the real numbers from the database
    total_books = Book.objects.count() # Counts unique book titles
    active_checkouts = Transaction.objects.filter(status='ACTIVE').count()
    overdue_books = Transaction.objects.filter(status='OVERDUE').count()

    # Package the data to send to the HTML
    context = {
        'total_books': total_books,
        'active_checkouts': active_checkouts,
        'overdue_books': overdue_books,
    }
    return render(request, 'librarian.html', context)

def student_portal(request):
    # Fetch all books from the database
    all_books = Book.objects.all()
    
    context = {
        'books': all_books
    }
    return render(request, 'student.html', context)