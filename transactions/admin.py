from django.contrib import admin
from .models import Category, Tag, Transaction, TransactionReceipt, BudgetCategory

class TransactionReceiptInline(admin.StackedInline):
    model = TransactionReceipt
    extra = 0

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'transaction_type', 'category', 'description_short', 'created_at']
    list_filter = ['transaction_type', 'category', 'created_at', 'user']
    search_fields = ['description', 'category__name', 'user__username']
    readonly_fields = ['created_at']
    inlines = [TransactionReceiptInline]
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Описание'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(TransactionReceipt)
class TransactionReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'transaction', 'generated_at']

@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'monthly_limit', 'warning_threshold']