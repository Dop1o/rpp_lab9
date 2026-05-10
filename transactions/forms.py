from django import forms
from .models import Transaction, Category, Tag

class TransactionForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100, 
        required=False,
        label="Новая категория (или выберите существующую)",
        widget=forms.TextInput(attrs={'placeholder': 'Введите название новой категории'})
    )
    tags_names = forms.CharField(
        max_length=200, 
        required=False,
        label="Теги (через запятую)",
        widget=forms.TextInput(attrs={'placeholder': 'еда, транспорт, развлечения'})
    )
    
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'category', 'description', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['tags'].required = False
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('Сумма должна быть больше 0')
        return amount
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or len(description.strip()) == 0:
            raise forms.ValidationError('Описание не может быть пустым')
        if len(description) < 3:
            raise forms.ValidationError('Описание слишком короткое (минимум 3 символа)')
        return description
    
    def save(self, user=None, commit=True):
        instance = super().save(commit=False)
        
        if user:
            instance.user = user
        
        category_name = self.cleaned_data.get('category_name')
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name.strip())
            instance.category = category
        
        if commit:
            instance.save()
            self.save_m2m()
            
            tags_names = self.cleaned_data.get('tags_names')
            if tags_names:
                tag_list = [tag.strip() for tag in tags_names.split(',') if tag.strip()]
                for tag_name in tag_list:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    instance.tags.add(tag)
        
        return instance