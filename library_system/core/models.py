from django.db import models
from django.utils import timezone
import uuid

class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    regd_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.regd_no})"

class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    isbn = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    def __str__(self):
        return self.title

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.book.title} issued to {self.student.name}"