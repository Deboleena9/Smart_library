from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Book, Transaction, Student

def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId').strip()
        
        # Route 1: Librarian Login
        if user_id.lower() == 'admin':
            return redirect('librarian')
            
        # Route 2: Student Login
        try:
            student = Student.objects.get(regd_no__iexact=user_id)
            # Save the student's ID in a secure Django session
            request.session['student_id'] = str(student.id)
            return redirect('student')
        except Student.DoesNotExist:
            messages.error(request, "❌ Registration Number not found.")
            return redirect('login')

    return render(request, 'index.html')

def librarian_dashboard(request):
    total_books = Book.objects.count()
    active_checkouts = Transaction.objects.filter(status='ACTIVE').count()
    overdue_books = Transaction.objects.filter(status='OVERDUE').count()

    # NEW: Fetch the list of active transactions, sorted by due date
    active_transactions = Transaction.objects.filter(status='ACTIVE').order_by('due_date')

    context = {
        'total_books': total_books,
        'active_checkouts': active_checkouts,
        'overdue_books': overdue_books,
        'active_transactions': active_transactions, # Pass them to the HTML
    }
    return render(request, 'librarian.html', context)

def student_portal(request):
    # 1. Check who is logged in
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login') # Kick them back to login if not authenticated

    # 2. Fetch their specific data
    student = Student.objects.get(id=student_id)
    all_books = Book.objects.all()
    
    # 3. Fetch ONLY the books currently issued to them
    my_transactions = Transaction.objects.filter(student=student, status='ACTIVE')
    
    context = {
        'student': student,
        'books': all_books,
        'my_transactions': my_transactions
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


def return_book(request, transaction_id):
    if request.method == 'POST':
        try:
            # Find the exact active transaction
            transaction = Transaction.objects.get(id=transaction_id, status='ACTIVE')
            book = transaction.book

            # 1. Update Transaction Status and Return Date
            transaction.status = 'RETURNED'
            transaction.return_date = timezone.now()
            transaction.save()

            # 2. Add the book back to the library's available inventory
            book.available_copies += 1
            book.save()

            messages.success(request, f"✅ '{book.title}' was successfully returned by {transaction.student.name}.")
        except Transaction.DoesNotExist:
            messages.error(request, "❌ Transaction not found or already returned.")

    return redirect('librarian')

def logout_user(request):
    # This completely wipes the secure session data
    request.session.flush() 
    return redirect('login')
