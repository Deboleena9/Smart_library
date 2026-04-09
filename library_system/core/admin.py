from django.contrib import admin
from .models import Book, Student, Transaction, LibrarySetting

admin.site.register(Book)
admin.site.register(Student)
admin.site.register(Transaction)
admin.site.register(LibrarySetting)