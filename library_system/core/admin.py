from django.contrib import admin
from .models import Book, Student, Transaction

admin.site.register(Book)
admin.site.register(Student)
admin.site.register(Transaction)