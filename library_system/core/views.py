from django.shortcuts import render, redirect
from django.contrib import messages # For success/error popups
from django.utils import timezone
from datetime import timedelta
from .models import Book, Transaction, Student

# ... keep your login_view, librarian_dashboard, and student_portal functions here ...

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