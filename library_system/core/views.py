from django.shortcuts import render

def login_view(request):
    return render(request, 'index.html')

def librarian_dashboard(request):
    return render(request, 'librarian.html')

def student_portal(request):
    return render(request, 'student.html')