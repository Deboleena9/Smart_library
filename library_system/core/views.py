from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Book, Transaction, Student

def login_view(request):
    # If they are already logged in, skip the login page entirely
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('librarian')
        return redirect('student')

    if request.method == 'POST':
        # Grab the data from the HTML form
        user_id = request.POST.get('userId').strip()
        password = request.POST.get('password').strip()
        
        # MAGIC HAPPENS HERE: Django securely checks the hashed password
        user = authenticate(request, username=user_id, password=password)
        
        if user is not None:
            login(request, user) # This creates the secure session
            
            # Route 1: Librarian (Admin)
            if user.is_superuser:
                return redirect('librarian')
            
            # Route 2: Student
            else:
                try:
                    # Link the logged-in Auth User to our Student database via regd_no
                    student = Student.objects.get(regd_no__iexact=user.username)
                    request.session['student_id'] = str(student.id)
                    return redirect('student')
                except Student.DoesNotExist:
                    logout(request)
                    messages.error(request, "❌ System error: Student profile not linked to this account.")
                    return redirect('login')
        else:
            messages.error(request, "❌ Invalid User ID or Password.")
            return redirect('login')

    return render(request, 'index.html')

# Security Lock: Kicks unauthenticated users back to the login page
@login_required(login_url='login')
def librarian_dashboard(request):
    # Security Lock: Only superusers (admins) can see this page
    if not request.user.is_superuser:
        return redirect('student')

    total_books = Book.objects.count()
    active_checkouts = Transaction.objects.filter(status='ACTIVE').count()
    overdue_books = Transaction.objects.filter(status='OVERDUE').count()
    active_transactions = Transaction.objects.filter(status='ACTIVE').order_by('due_date')

    context = {
        'total_books': total_books,
        'active_checkouts': active_checkouts,
        'overdue_books': overdue_books,
        'active_transactions': active_transactions,
    }
    return render(request, 'librarian.html', context)

@login_required(login_url='login')
def student_portal(request):
    student_id = request.session.get('student_id')
    if not student_id:
        logout(request)
        return redirect('login')

    student = Student.objects.get(id=student_id)
    all_books = Book.objects.all()
    my_transactions = Transaction.objects.filter(student=student, status='ACTIVE')
    
    context = {
        'student': student,
        'books': all_books,
        'my_transactions': my_transactions
    }
    return render(request, 'student.html', context)

@login_required(login_url='login')
def issue_book(request):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        regd_no = request.POST.get('regd_no')
        isbn = request.POST.get('isbn')

        try:
            student = Student.objects.get(regd_no=regd_no)
            book = Book.objects.get(isbn=isbn)

            if book.available_copies > 0:
                due_date = timezone.now() + timedelta(days=14)
                Transaction.objects.create(
                    book=book,
                    student=student,
                    due_date=due_date,
                    status='ACTIVE'
                )
                
                book.available_copies -= 1
                book.save()
                
                messages.success(request, f"⚡ Success! '{book.title}' issued to {student.name}.")
            else:
                messages.error(request, f"❌ Sorry, '{book.title}' is currently out of stock.")
                
        except Student.DoesNotExist:
            messages.error(request, "❌ Student Registration Number not found.")
        except Book.DoesNotExist:
            messages.error(request, "❌ Book ISBN not found.")
        
    return redirect('librarian')

@login_required(login_url='login')
def return_book(request, transaction_id):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        try:
            transaction = Transaction.objects.get(id=transaction_id, status='ACTIVE')
            book = transaction.book

            transaction.status = 'RETURNED'
            transaction.return_date = timezone.now()
            transaction.save()

            book.available_copies += 1
            book.save()

            messages.success(request, f"✅ '{book.title}' was successfully returned by {transaction.student.name}.")
        except Transaction.DoesNotExist:
            messages.error(request, "❌ Transaction not found or already returned.")

    return redirect('librarian')

def logout_user(request):
    logout(request) # Uses Django's secure logout
    request.session.flush() 
    messages.success(request, "You have been securely logged out.")
    return redirect('login')