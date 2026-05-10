from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Transaction, Category, Tag
from .forms import TransactionForm

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='admin').exists()

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Простая проверка
        if not username or not password1:
            messages.error(request, 'Заполните все поля')
        elif password1 != password2:
            messages.error(request, 'Пароли не совпадают')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь уже существует')
        else:
            # Создаем пользователя
            user = User.objects.create_user(username=username, password=password1)
            # Добавляем в группу user
            user_group, _ = Group.objects.get_or_create(name='user')
            user.groups.add(user_group)
            # Сразу входим
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('list')
    
    return render(request, 'transactions/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('list')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'transactions/login.html')

def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')

@login_required
def transaction_list(request):
    if is_admin(request.user):
        transactions = Transaction.objects.all().order_by('-created_at')
    else:
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    total_expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'transactions': transactions,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'balance': total_income - total_expenses,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'transactions/list.html', context)

@login_required
def transaction_create(request):
    form = TransactionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        transaction = form.save(user=request.user)
        messages.success(request, f'Транзакция добавлена!')
        return redirect('list')
    return render(request, 'transactions/create.html', {'form': form})

@login_required
def transaction_update(request, pk):
    if is_admin(request.user):
        obj = get_object_or_404(Transaction, pk=pk)
    else:
        obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    form = TransactionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(user=request.user)
        messages.success(request, 'Транзакция обновлена')
        return redirect('list')
    return render(request, 'transactions/update.html', {'form': form, 'transaction': obj})

@login_required
def transaction_delete(request, pk):
    if is_admin(request.user):
        obj = get_object_or_404(Transaction, pk=pk)
    else:
        obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Транзакция удалена')
        return redirect('list')
    return render(request, 'transactions/delete.html', {'transaction': obj})

@login_required
def transaction_detail(request, pk):
    if is_admin(request.user):
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    context = {
        'transaction': transaction,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'transactions/detail.html', context)

@login_required
def dashboard(request):
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
    
    user_stats = []
    if is_admin(request.user):
        # Статистика по всем пользователям
        from django.contrib.auth.models import User
        for user in User.objects.all():
            expenses = Transaction.objects.filter(user=user, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
            income = Transaction.objects.filter(user=user, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            user_stats.append({
                'username': user.username,
                'transaction_count': Transaction.objects.filter(user=user).count(),
                'total_expenses': expenses,
                'total_income': income,
                'balance': income - expenses,
            })
    
    if is_admin(request.user):
        expenses_by_category = Transaction.objects.filter(
            transaction_type='expense',
            created_at__gte=start_of_month
        ).values('category__name').annotate(total=Sum('amount'))
        
        top_tags = Tag.objects.annotate(usage_count=Count('transaction')).order_by('-usage_count')[:5]
        monthly_expenses = Transaction.objects.filter(transaction_type='expense', created_at__gte=start_of_month).aggregate(Sum('amount'))['amount__sum'] or 0
    else:
        expenses_by_category = Transaction.objects.filter(
            transaction_type='expense',
            user=request.user,
            created_at__gte=start_of_month
        ).values('category__name').annotate(total=Sum('amount'))
        
        top_tags = Tag.objects.filter(transaction__user=request.user).annotate(
            usage_count=Count('transaction')
        ).order_by('-usage_count')[:5]
        monthly_expenses = Transaction.objects.filter(transaction_type='expense', user=request.user, created_at__gte=start_of_month).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'expenses_by_category': expenses_by_category,
        'top_tags': top_tags,
        'monthly_expenses': monthly_expenses,
        'is_admin': is_admin(request.user),
        'user_stats': user_stats,  # Добавлено для админа
    }
    return render(request, 'transactions/dashboard.html', context)

# Админские функции
@login_required
def category_list(request):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    categories = Category.objects.all()
    return render(request, 'transactions/admin_categories.html', {'categories': categories})

@login_required
def category_create(request):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.get_or_create(name=name.strip())
            messages.success(request, 'Категория создана')
            return redirect('category_list')
    return render(request, 'transactions/admin_category_form.html')

@login_required
def category_delete(request, pk):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Категория удалена')
        return redirect('category_list')
    return render(request, 'transactions/admin_confirm_delete.html', {'object': category})

@login_required
def tag_list(request):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    tags = Tag.objects.all()
    return render(request, 'transactions/admin_tags.html', {'tags': tags})

@login_required
def tag_create(request):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Tag.objects.get_or_create(name=name.strip())
            messages.success(request, 'Тег создан')
            return redirect('tag_list')
    return render(request, 'transactions/admin_tag_form.html')

@login_required
def tag_delete(request, pk):
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен')
        return redirect('list')
    
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Тег удален')
        return redirect('tag_list')
    return render(request, 'transactions/admin_confirm_delete.html', {'object': tag})