from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Book, Transaction, Student

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

def issue_book(request):
    if request.method == 'POST':
        # 1. Grab the data typed into the HTML form
        regd_no = request.POST.get('regd_no')
        isbn = request.POST.get('isbn')

        try:
            # 2. Look up the exact student and book in the database
            student = Student.objects.get(regd_no=regd_no)
            book = Book.objects.get(isbn=isbn)

            # 3. Check if the book is actually in stock
            if book.available_copies > 0:
                
                # Create the transaction (Due in 14 days)
                due_date = timezone.now() + timedelta(days=14)
                Transaction.objects.create(
                    book=book,
                    student=student,
                    due_date=due_date,
                    status='ACTIVE'
                )
                
                # Deduct 1 from the available copies and save
                book.available_copies -= 1
                book.save()
                
                # Send a success message back to the dashboard
                messages.success(request, f"⚡ Success! '{book.title}' issued to {student.name}.")
            else:
                messages.error(request, f"❌ Sorry, '{book.title}' is currently out of stock.")
                
        # 4. Handle typos or missing data
        except Student.DoesNotExist:
            messages.error(request, "❌ Student Registration Number not found.")
        except Book.DoesNotExist:
            messages.error(request, "❌ Book ISBN not found.")
        
    # Refresh the dashboard page
    return redirect('librarian')