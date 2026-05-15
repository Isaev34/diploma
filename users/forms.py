import random

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User, UserCard, Address
from .roles import (
    ROLE_CHOICES,
    ROLE_CUSTOMER,
    assign_role_to_user,
    ensure_role_groups,
    get_user_role,
)


class BootstrapPasswordResetForm(PasswordResetForm):
    """Как стандартная форма, но сброс доступен и до подтверждения e-mail (is_active=False)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.setdefault("class", "form-control")

    def get_users(self, email):
        UserModel = get_user_model()
        field = UserModel.get_email_field_name()
        users = UserModel._default_manager.filter(**{f"{field}__iexact": email})
        return (u for u in users if u.has_usable_password())


class BootstrapSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for the custom User model"""
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Телефон",
        help_text="Необязательное поле"
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        user.is_active = False
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя"""
    
    class Meta:
        model = User
        fields = ('email', 'phone')
        labels = {
            'email': 'Email',
            'phone': 'Телефон',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})


class AddressForm(forms.ModelForm):
    """Форма для добавления/редактирования адреса доставки"""
    
    class Meta:
        model = Address
        fields = ('city', 'street', 'house', 'block', 'entrance', 'floor', 'apartment', 'is_default')
        labels = {
            'city': 'Город',
            'street': 'Улица',
            'house': 'Дом',
            'block': 'Корпус/Строение',
            'entrance': 'Подъезд',
            'floor': 'Этаж',
            'apartment': 'Квартира/Офис',
            'is_default': 'Основной адрес',
        }
        widgets = {
            'city': forms.TextInput(attrs={'placeholder': 'Москва'}),
            'street': forms.TextInput(attrs={'placeholder': 'Ленина'}),
            'house': forms.TextInput(attrs={'placeholder': '1'}),
            'block': forms.TextInput(attrs={'placeholder': 'А'}),
            'entrance': forms.TextInput(attrs={'placeholder': '1'}),
            'floor': forms.NumberInput(attrs={'placeholder': '5'}),
            'apartment': forms.TextInput(attrs={'placeholder': '10'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_default':
                field.widget.attrs.update({'class': 'form-control'})
            if field_name in ['city', 'street', 'house']:
                field.required = True


class UserCardForm(forms.ModelForm):
    """Форма для добавления карты пользователя"""
    
    # Поле для ввода полного номера (будет обработано для генерации рандомных данных)
    card_number = forms.CharField(
        max_length=19,
        label="Номер карты",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0000 0000 0000 0000',
            'pattern': r'[0-9\s]{13,19}',
            'maxlength': '19'
        }),
        help_text="Введите номер карты (будет сохранен только последние 4 цифры для демонстрации)"
    )
    
    class Meta:
        model = UserCard
        fields = ('card_type', 'cardholder_name', 'is_default')
        labels = {
            'card_type': 'Тип карты',
            'cardholder_name': 'Имя держателя карты',
            'is_default': 'Использовать по умолчанию',
        }
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-control'}),
            'cardholder_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IVAN IVANOV'
            }),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_card_number(self):
        """Обработка номера карты - извлекаем последние 4 цифры"""
        card_number = self.cleaned_data.get('card_number', '').replace(' ', '').replace('-', '')
        if len(card_number) < 13 or len(card_number) > 19:
            raise forms.ValidationError("Номер карты должен содержать от 13 до 19 цифр")
        if not card_number.isdigit():
            raise forms.ValidationError("Номер карты должен содержать только цифры")
        # Берем последние 4 цифры
        return card_number[-4:]
    
    def save(self, commit=True):
        """Сохранить карту с последними 4 цифрами"""
        card = super().save(commit=False)
        # Используем уже обработанное значение из clean_card_number (последние 4 цифры)
        card_number_clean = self.cleaned_data.get('card_number', '')
        if card_number_clean and len(card_number_clean) == 4:
            card.last_four_digits = card_number_clean
        else:
            # Если по какой-то причине номер не был обработан, генерируем случайные 4 цифры
            card.last_four_digits = str(random.randint(1000, 9999)).zfill(4)
        
        # Если это карта по умолчанию, снимаем флаг с других карт
        if card.is_default and commit and card.user:
            UserCard.objects.filter(user=card.user, is_default=True).exclude(id=card.id if card.id else None).update(is_default=False)
        
        if commit:
            card.save()
        return card


ROLE_FIELD_HELP = (
    'Администратор и менеджер — доступ к админ-панели. '
    'Курьер и сборщик — мобильные приложения. Покупатель — сайт.'
)


class AdminUserCreationForm(UserCreationForm):
    """Форма создания пользователя в админке с выбором роли."""

    role = forms.ChoiceField(
        label='Роль',
        choices=ROLE_CHOICES,
        initial=ROLE_CUSTOMER,
        help_text=ROLE_FIELD_HELP,
    )
    email = forms.EmailField(required=False, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    bonus_points = forms.IntegerField(required=False, initial=0, label='Бонусные баллы')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'bonus_points')

    def __init__(self, *args, **kwargs):
        ensure_role_groups(verbose=False)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.phone = self.cleaned_data.get('phone', '')
        user.bonus_points = self.cleaned_data.get('bonus_points') or 0
        if commit:
            user.save()
            assign_role_to_user(user, self.cleaned_data['role'])
        return user


class AdminUserChangeForm(UserChangeForm):
    """Форма редактирования пользователя в админке с выбором роли."""

    role = forms.ChoiceField(
        label='Роль',
        choices=ROLE_CHOICES,
        help_text=ROLE_FIELD_HELP,
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        ensure_role_groups(verbose=False)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['role'].initial = get_user_role(self.instance)
        for name in ('groups', 'user_permissions'):
            self.fields.pop(name, None)

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get('role')
        if role:
            assign_role_to_user(user, role)
        return user



