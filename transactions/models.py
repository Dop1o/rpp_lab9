from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class BudgetCategory(models.Model):
    category = models.OneToOneField(
        Category, 
        on_delete=models.CASCADE,
        related_name='budget'
    )
    monthly_limit = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    spent_current_month = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    warning_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=80.0
    )
    
    def __str__(self):
        return f"Бюджет: {self.category.name} - {self.monthly_limit} ₽"

class TransactionReceipt(models.Model):
    transaction = models.OneToOneField(
        'Transaction', 
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    receipt_number = models.CharField(max_length=50, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Чек №{self.receipt_number}"

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('expense', 'Расход'),
        ('income', 'Доход'),
    ]
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, default='expense')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    
    def __str__(self):
        return f"{self.amount} ₽ - {self.created_at.strftime('%d.%m.%Y %H:%M')}"