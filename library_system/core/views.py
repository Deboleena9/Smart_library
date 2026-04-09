from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Book, Transaction, Student, LibrarySetting

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('librarian')
        return redirect('student')

    if request.method == 'POST':
        user_id = request.POST.get('userId').strip()
        password = request.POST.get('password').strip()
        user = authenticate(request, username=user_id, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('librarian')
            else:
                try:
                    student = Student.objects.get(regd_no__iexact=user.username)
                    request.session['student_id'] = str(student.id)
                    return redirect('student')
                except Student.DoesNotExist:
                    logout(request)
                    messages.error(request, "❌ Profile not linked.")
                    return redirect('login')
        else:
            messages.error(request, "❌ Invalid ID or Password.")
            return redirect('login')

    # GRAB THE SETTINGS TO SEND TO THE HTML
    setting = LibrarySetting.objects.first()
    return render(request, 'index.html', {'setting': setting})

# Security Lock: Kicks unauthenticated users back to the login page
@login_required(login_url='login')
def librarian_dashboard(request):
    if not request.user.is_superuser:
        return redirect('student')

    total_books = Book.objects.count()
    active_checkouts = Transaction.objects.filter(status='ACTIVE').count()
    overdue_books = Transaction.objects.filter(status='OVERDUE').count()

    context = {
        'total_books': total_books,
        'active_checkouts': active_checkouts,
        'overdue_books': overdue_books,
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
        
    return redirect('manage_issues')

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

    return redirect('manage_issues')

def logout_user(request):
    logout(request) # Uses Django's secure logout
    request.session.flush() 
    messages.success(request, "You have been securely logged out.")
    return redirect('login')

def setup_admin(request):
    # Check if the admin already exists
    if not User.objects.filter(username='admin').exists():
        # Create a new superuser with ID: admin, Password: admin123
        User.objects.create_superuser('admin', 'admin@college.edu', 'admin123')
        return HttpResponse("✅ Admin account created successfully! Username: admin | Password: admin123. You can now go to the login page.")
    
    return HttpResponse("Admin already exists. You can go log in!")


@login_required(login_url='login')
def manage_books(request):
    if not request.user.is_superuser:
        return redirect('student')

    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        author = request.POST.get('author')
        copies = int(request.POST.get('copies'))

        try:
            # Create the new book
            Book.objects.create(
                isbn=isbn, title=title, author=author, 
                total_copies=copies, available_copies=copies
            )
            messages.success(request, f"📚 '{title}' was added to the library catalog.")
        except Exception as e:
            messages.error(request, "❌ Error: A book with this ISBN might already exist.")
        
        return redirect('manage_books')

    books = Book.objects.all().order_by('title')
    return render(request, 'manage_books.html', {'books': books})

@login_required(login_url='login')
def manage_students(request):
    if not request.user.is_superuser:
        return redirect('student')

    if request.method == 'POST':
        regd_no = request.POST.get('regd_no')
        name = request.POST.get('name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password') # The password the librarian assigns

        if User.objects.filter(username=regd_no).exists():
            messages.error(request, "❌ A student with this Registration Number already exists.")
        else:
            # 1. Create the secure login account automatically!
            User.objects.create_user(username=regd_no, email=email, password=password)
            
            # 2. Create the library profile
            Student.objects.create(regd_no=regd_no, name=name, email=email, department=department)
            messages.success(request, f"🎓 Student '{name}' added successfully. They can now log in!")
            
        return redirect('manage_students')

    students = Student.objects.all().order_by('name')
    return render(request, 'manage_students.html', {'students': students})

@login_required(login_url='login')
def delete_student(request, student_id):
    if not request.user.is_superuser:
        return redirect('student')

    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            
            # Find and delete their secure Django login account
            user_account = User.objects.filter(username=student.regd_no).first()
            if user_account:
                user_account.delete()
                
            # Delete their library profile
            student_name = student.name
            student.delete()
            
            messages.success(request, f"🗑️ Success: '{student_name}' and their login access have been permanently removed.")
        except Student.DoesNotExist:
            messages.error(request, "❌ Error: Student not found.")
            
    return redirect('manage_students')


@login_required(login_url='login')
def manage_issues(request):
    if not request.user.is_superuser:
        return redirect('student')
    
    # Fetch the active transactions to display in the return table
    active_transactions = Transaction.objects.filter(status='ACTIVE').order_by('due_date')
    return render(request, 'manage_issues.html', {'active_transactions': active_transactions})

@login_required(login_url='login')
def delete_book(request, book_id):
    if not request.user.is_superuser:
        return redirect('student')

    if request.method == 'POST':
        try:
            book = Book.objects.get(id=book_id)
            book_title = book.title
            book.delete()
            messages.success(request, f"🗑️ Book '{book_title}' deleted successfully.")
        except Book.DoesNotExist:
            messages.error(request, "❌ Error: Book not found.")
            
    return redirect('manage_books')

@login_required(login_url='login')
def manage_settings(request):
    if not request.user.is_superuser:
        return redirect('student')

    # Get the existing setting or create one if it doesn't exist yet
    setting, created = LibrarySetting.objects.get_or_create(id=1)

    if request.method == 'POST':
        # Grab the text
        institute_name = request.POST.get('institute_name')
        
        # Check if a new file was actually uploaded
        if 'background_image' in request.FILES:
            setting.background_image = request.FILES['background_image']
        
        # Save the changes
        setting.institute_name = institute_name
        setting.save()
        
        messages.success(request, "⚙️ Library settings updated successfully.")
        return redirect('manage_settings')

    return render(request, 'manage_settings.html', {'setting': setting})