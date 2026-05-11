from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Transaction, Category, Tag, BudgetCategory, TransactionReceipt
from .forms import TransactionForm
from django.db import IntegrityError


class ModelTests(TestCase):
    """Тесты моделей базы данных"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.category = Category.objects.create(name='Еда')
        self.tag1 = Tag.objects.create(name='обед')
        self.tag2 = Tag.objects.create(name='ресторан')

    def test_category_str(self):
        """Тест строкового представления категории"""
        self.assertEqual(str(self.category), 'Еда')

    def test_tag_str(self):
        """Тест строкового представления тега"""
        self.assertEqual(str(self.tag1), 'обед')

    def test_category_unique_name(self):
        """Тест уникальности названия категории"""
        with self.assertRaises(Exception):
            Category.objects.create(name='Еда')

    def test_create_transaction(self):
        """Тест создания транзакции"""
        transaction = Transaction.objects.create(
            amount=1500.50,
            description='Обед в ресторане',
            transaction_type='expense',
            category=self.category,
            user=self.user
        )
        transaction.tags.add(self.tag1, self.tag2)
        
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.amount, 1500.50)
        self.assertEqual(transaction.tags.count(), 2)
        self.assertEqual(transaction.transaction_type, 'expense')

    def test_income_transaction(self):
        """Тест создания доходной транзакции"""
        transaction = Transaction.objects.create(
            amount=50000,
            description='Зарплата',
            transaction_type='income',
            user=self.user
        )
        self.assertEqual(transaction.transaction_type, 'income')

    def test_budget_category_one_to_one(self):
        """Тест связи one-to-one BudgetCategory с Category"""
        budget = BudgetCategory.objects.create(
            category=self.category,
            monthly_limit=50000,
            warning_threshold=80.0
        )
        self.assertEqual(budget.category, self.category)
        self.assertEqual(self.category.budget, budget)

    def test_transaction_receipt_one_to_one(self):
        """Тест связи one-to-one TransactionReceipt с Transaction"""
        transaction = Transaction.objects.create(
            amount=2000,
            description='Покупка',
            user=self.user
        )
        receipt = TransactionReceipt.objects.create(
            transaction=transaction,
            receipt_number='RCPT-001'
        )
        self.assertEqual(receipt.transaction, transaction)
        self.assertEqual(transaction.receipt, receipt)

    def test_transaction_ordering(self):
        """Тест сортировки транзакций по дате"""
        from django.utils import timezone
        from datetime import timedelta
        
        t1 = Transaction.objects.create(
            amount=100, 
            description='T1', 
            user=self.user,
            created_at=timezone.now()
        )
        t2 = Transaction.objects.create(
            amount=200, 
            description='T2', 
            user=self.user,
            created_at=timezone.now() + timedelta(seconds=10)
        )
        transactions = Transaction.objects.all().order_by('-created_at')
        self.assertEqual(transactions.first(), t2)
        self.assertEqual(transactions.last(), t1)

    def test_transaction_negative_amount(self):
        """Тест валидации отрицательной суммы"""
        from django.core.exceptions import ValidationError
        from django.core.validators import MinValueValidator
        
        transaction = Transaction(amount=-100, description='Тест', user=self.user)
        with self.assertRaises(Exception):
            transaction.full_clean()


class ViewTests(TestCase):
    """Тесты представлений"""
    
    def setUp(self):
        self.client = Client()
        
        # Обычный пользователь
        self.user = User.objects.create_user(username='testuser', password='test123')
        user_group, _ = Group.objects.get_or_create(name='user')
        self.user.groups.add(user_group)
        
        # Администратор
        self.admin = User.objects.create_user(username='admin', password='admin123')
        admin_group, _ = Group.objects.get_or_create(name='admin')
        self.admin.groups.add(admin_group)
        
        self.category = Category.objects.create(name='Транспорт')

    # Тесты аутентификации
    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_register_new_user(self):
        """Тест регистрации нового пользователя"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login(self):
        """Тест входа в систему"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'test123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        """Тест входа с неверными данными"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """Тест выхода из системы"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)

    # Тесты доступа
    def test_transaction_list_requires_login(self):
        """Тест: неавторизованный пользователь перенаправляется на логин"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_transaction_list_authenticated(self):
        """Тест: авторизованный пользователь видит список"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # Тесты CRUD
    def test_create_transaction(self):
        """Тест создания транзакции"""
        self.client.login(username='testuser', password='test123')
        response = self.client.post('/create/', {
            'amount': 500,
            'transaction_type': 'expense',
            'description': 'Такси',
            'category': self.category.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_read_transaction(self):
        """Тест просмотра транзакции"""
        transaction = Transaction.objects.create(
            amount=300, description='Тест', user=self.user
        )
        self.client.login(username='testuser', password='test123')
        response = self.client.get(f'/detail/{transaction.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '300')

    def test_update_transaction(self):
        """Тест обновления транзакции"""
        transaction = Transaction.objects.create(
            amount=300, description='Старое', user=self.user
        )
        self.client.login(username='testuser', password='test123')
        response = self.client.post(f'/update/{transaction.id}/', {
            'amount': 400,
            'transaction_type': 'expense',
            'description': 'Новое описание',
        })
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, 400)
        self.assertEqual(transaction.description, 'Новое описание')

    def test_delete_transaction(self):
        """Тест удаления транзакции"""
        transaction = Transaction.objects.create(
            amount=150, description='Удалить', user=self.user
        )
        self.client.login(username='testuser', password='test123')
        response = self.client.post(f'/delete/{transaction.id}/')
        self.assertEqual(Transaction.objects.count(), 0)

    # Тесты разграничения прав
    def test_user_sees_only_own_transactions(self):
        """Тест: пользователь видит только свои транзакции"""
        Transaction.objects.create(amount=100, description='T1', user=self.user)
        Transaction.objects.create(amount=200, description='T2', user=self.admin)
        
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/')
        self.assertEqual(len(response.context['transactions']), 1)

    def test_admin_sees_all_transactions(self):
        """Тест: админ видит все транзакции"""
        Transaction.objects.create(amount=100, description='T1', user=self.user)
        Transaction.objects.create(amount=200, description='T2', user=self.admin)
        
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/')
        self.assertEqual(len(response.context['transactions']), 2)

    def test_user_cannot_manage_categories(self):
        """Тест: пользователь не может управлять категориями"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_manage_categories(self):
        """Тест: админ может управлять категориями"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_manage_tags(self):
        """Тест: пользователь не может управлять тегами"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/tags/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_manage_tags(self):
        """Тест: админ может управлять тегами"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/tags/')
        self.assertEqual(response.status_code, 200)

    # Тест дашборда
    def test_dashboard(self):
        """Тест дашборда"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    # Тест admin-панели Django
    def test_admin_panel(self):
        """Тест доступа к админ-панели Django"""
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)


class FormTests(TestCase):
    """Тесты форм"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.category = Category.objects.create(name='Тест')

    def test_transaction_form_valid(self):
        """Тест валидной формы"""
        form_data = {
            'amount': 1000,
            'transaction_type': 'expense',
            'description': 'Тестовое описание',
            'category': self.category.id,
        }
        form = TransactionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_transaction_form_empty(self):
        """Тест пустой формы"""
        form = TransactionForm(data={})
        self.assertFalse(form.is_valid())

    def test_transaction_form_negative_amount(self):
        """Тест отрицательной суммы"""
        form_data = {
            'amount': -100,
            'transaction_type': 'expense',
            'description': 'Тест',
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_transaction_form_zero_amount(self):
        """Тест нулевой суммы"""
        form_data = {
            'amount': 0,
            'transaction_type': 'expense',
            'description': 'Тест',
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_transaction_form_short_description(self):
        """Тест короткого описания"""
        form_data = {
            'amount': 100,
            'transaction_type': 'expense',
            'description': 'ab',
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid())


class URLsTest(TestCase):
    """Тесты URL-адресов"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.admin = User.objects.create_user(username='admin', password='admin123')
        admin_group, _ = Group.objects.get_or_create(name='admin')
        self.admin.groups.add(admin_group)
        self.transaction = Transaction.objects.create(amount=100, description='Тест', user=self.user)

    def test_login_url(self):
        """Тест URL входа"""
        self.assertEqual(reverse('login'), '/login/')

    def test_register_url(self):
        """Тест URL регистрации"""
        self.assertEqual(reverse('register'), '/register/')

    def test_list_url(self):
        """Тест URL списка"""
        self.assertEqual(reverse('list'), '/')

    def test_create_url(self):
        """Тест URL создания"""
        self.assertEqual(reverse('create'), '/create/')

    def test_dashboard_url(self):
        """Тест URL дашборда"""
        self.assertEqual(reverse('dashboard'), '/dashboard/')

    def test_detail_url(self):
        """Тест URL деталей"""
        url = reverse('detail', args=[self.transaction.id])
        self.assertEqual(url, f'/detail/{self.transaction.id}/')

    def test_update_url(self):
        """Тест URL обновления"""
        url = reverse('update', args=[self.transaction.id])
        self.assertEqual(url, f'/update/{self.transaction.id}/')

    def test_delete_url(self):
        """Тест URL удаления"""
        url = reverse('delete', args=[self.transaction.id])
        self.assertEqual(url, f'/delete/{self.transaction.id}/')