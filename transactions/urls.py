from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Транзакции
    path('', views.transaction_list, name='list'),
    path('create/', views.transaction_create, name='create'),
    path('update/<int:pk>/', views.transaction_update, name='update'),
    path('delete/<int:pk>/', views.transaction_delete, name='delete'),
    path('detail/<int:pk>/', views.transaction_detail, name='detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Управление категориями (НЕ используем admin/ в пути)
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Управление тегами (НЕ используем admin/ в пути)
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/delete/<int:pk>/', views.tag_delete, name='tag_delete'),
]