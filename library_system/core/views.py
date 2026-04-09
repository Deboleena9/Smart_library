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

    setting = LibrarySetting.objects.first()
    return render(request, 'index.html', {'setting': setting})

@login_required(login_url='login')
def librarian_dashboard(request):
    if not request.user.is_superuser:
        return redirect('student')

    # FIX 1 & 2: Added setting and active_transactions back to the dashboard!
    setting = LibrarySetting.objects.first()
    active_transactions = Transaction.objects.filter(status='ACTIVE').order_by('due_date')

    context = {
        'total_books': Book.objects.count(),
        'active_checkouts': active_transactions.count(),
        'overdue_books': Transaction.objects.filter(status='OVERDUE').count(),
        'active_transactions': active_transactions,
        'setting': setting
    }
    return render(request, 'librarian.html', context)

@login_required(login_url='login')
def student_portal(request):
    student_id = request.session.get('student_id')
    if not student_id:
        logout(request)
        return redirect('login')

    context = {
        'student': Student.objects.get(id=student_id),
        'books': Book.objects.all(),
        'my_transactions': Transaction.objects.filter(student_id=student_id, status='ACTIVE'),
        'setting': LibrarySetting.objects.first()
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
                # FIX 3: Apply the custom due period!
                setting = LibrarySetting.objects.first()
                issue_days = setting.issue_days if setting else 15
                
                # If 0 (Not Fixed), set due date 100 years into the future
                if issue_days == 0:
                    due_date = timezone.now() + timedelta(days=36500)
                else:
                    due_date = timezone.now() + timedelta(days=issue_days)

                Transaction.objects.create(book=book, student=student, due_date=due_date, status='ACTIVE')
                book.available_copies -= 1
                book.save()
                messages.success(request, f"⚡ Success! '{book.title}' issued to {student.name}.")
            else:
                messages.error(request, f"❌ Sorry, '{book.title}' is out of stock.")
                
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
            transaction.status = 'RETURNED'
            transaction.return_date = timezone.now()
            transaction.save()

            transaction.book.available_copies += 1
            transaction.book.save()
            messages.success(request, f"✅ '{transaction.book.title}' was successfully returned.")
        except Transaction.DoesNotExist:
            messages.error(request, "❌ Transaction not found or already returned.")

    return redirect('manage_issues')

def logout_user(request):
    logout(request)
    request.session.flush() 
    messages.success(request, "You have been securely logged out.")
    return redirect('login')

def setup_admin(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@college.edu', 'admin123')
        return HttpResponse("✅ Admin account created successfully! Username: admin | Password: admin123.")
    return HttpResponse("Admin already exists. You can go log in!")

@login_required(login_url='login')
def manage_books(request):
    if not request.user.is_superuser: return redirect('student')
    if request.method == 'POST':
        try:
            Book.objects.create(
                isbn=request.POST.get('isbn'), title=request.POST.get('title'), 
                author=request.POST.get('author'), total_copies=int(request.POST.get('copies')), 
                available_copies=int(request.POST.get('copies'))
            )
            messages.success(request, "📚 Book added to catalog.")
        except Exception:
            messages.error(request, "❌ Error: A book with this ISBN might already exist.")
        return redirect('manage_books')

    return render(request, 'manage_books.html', {'books': Book.objects.all().order_by('title'), 'setting': LibrarySetting.objects.first()})

@login_required(login_url='login')
def manage_students(request):
    if not request.user.is_superuser: return redirect('student')
    if request.method == 'POST':
        regd_no = request.POST.get('regd_no')
        if User.objects.filter(username=regd_no).exists():
            messages.error(request, "❌ A student with this Registration Number already exists.")
        else:
            User.objects.create_user(username=regd_no, email=request.POST.get('email'), password=request.POST.get('password'))
            Student.objects.create(regd_no=regd_no, name=request.POST.get('name'), email=request.POST.get('email'), department=request.POST.get('department'))
            messages.success(request, "🎓 Student added successfully.")
        return redirect('manage_students')

    return render(request, 'manage_students.html', {'students': Student.objects.all().order_by('name'), 'setting': LibrarySetting.objects.first()})

@login_required(login_url='login')
def delete_student(request, student_id):
    if not request.user.is_superuser: return redirect('student')
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            user_account = User.objects.filter(username=student.regd_no).first()
            if user_account: user_account.delete()
            student.delete()
            messages.success(request, "🗑️ Success: Student and login access permanently removed.")
        except Student.DoesNotExist: pass
    return redirect('manage_students')

@login_required(login_url='login')
def delete_book(request, book_id):
    if not request.user.is_superuser: return redirect('student')
    if request.method == 'POST':
        try:
            Book.objects.get(id=book_id).delete()
            messages.success(request, "🗑️ Book deleted successfully.")
        except Book.DoesNotExist: pass
    return redirect('manage_books')

@login_required(login_url='login')
def manage_issues(request):
    if not request.user.is_superuser: return redirect('student')
    return render(request, 'manage_issues.html', {'active_transactions': Transaction.objects.filter(status='ACTIVE').order_by('due_date'), 'setting': LibrarySetting.objects.first()})

@login_required(login_url='login')
def manage_settings(request):
    if not request.user.is_superuser: return redirect('student')
    setting, _ = LibrarySetting.objects.get_or_create(id=1)
    if request.method == 'POST':
        setting.institute_name = request.POST.get('institute_name')
        setting.issue_days = int(request.POST.get('issue_days')) # Save the due period
        setting.save()
        messages.success(request, "⚙️ Library settings updated successfully.")
        return redirect('manage_settings')
    return render(request, 'manage_settings.html', {'setting': setting})