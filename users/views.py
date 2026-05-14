from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .emailing import send_verification_email
from .forms import CustomUserCreationForm, ProfileEditForm, UserCardForm, AddressForm
from .models import UserCard, Address
from .tokens import email_verification_token
from .utils import log_user_activity


def login_view(request):
    if request.method == 'POST':
        from django.contrib.auth import authenticate

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_user_activity(
                user,
                'login',
                f'Успешный вход в систему: {username}',
                request,
            )
            return redirect('catalog:home')

        UserModel = get_user_model()
        try:
            u = UserModel.objects.get(username=username)
            if u.check_password(password) and not u.is_active:
                messages.warning(
                    request,
                    'Аккаунт не подтверждён. Проверьте почту или запросите новое письмо.',
                )
                log_user_activity(
                    None,
                    'login',
                    f'Вход отклонён (не подтверждён e-mail): {username}',
                    request,
                )
                return render(request, 'users/login.html')
        except UserModel.DoesNotExist:
            pass

        log_user_activity(
            None,
            'login',
            f'Неудачная попытка входа: {username}',
            request,
        )
        messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'users/login.html')

def logout_view(request):
    user = request.user
    logout(request)
    # Логируем выход
    if user.is_authenticated:
        log_user_activity(
            user,
            'logout',
            f'Выход из системы: {user.username}',
            request
        )
    return redirect('catalog:home')

@login_required
def profile_view(request):
    from cart.models import Order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]  # Последние 5 заказов
    return render(request, 'users/profile.html', {'orders': orders})

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_user_activity(
                request.user,
                'profile_update',
                f'Обновление профиля пользователя: {request.user.username}',
                request
            )
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:signup_done')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        self.object = form.save()
        log_user_activity(
            self.object,
            'register',
            f'Регистрация (ожидает e-mail): {self.object.username}',
            self.request,
        )
        try:
            send_verification_email(self.request, self.object)
            messages.success(
                self.request,
                'На указанный e-mail отправлена ссылка для подтверждения аккаунта.',
            )
        except Exception:
            messages.warning(
                self.request,
                'Аккаунт создан, но письмо не удалось отправить. '
                'Попробуйте «Выслать письмо снова» на странице входа.',
            )
        return HttpResponseRedirect(self.get_success_url())


def signup_done_view(request):
    return render(request, 'users/signup_done.html')


def activate_view(request, uidb64, token):
    UserModel = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        messages.success(request, 'E-mail подтверждён. Теперь можно войти.')
        return redirect('users:login')

    messages.error(request, 'Ссылка недействительна или устарела. Запросите новое письмо.')
    return redirect('users:login')


def resend_verification_view(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        if not email:
            messages.error(request, 'Введите адрес e-mail.')
            return render(request, 'users/resend_verification.html')
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            messages.success(
                request,
                'Если указанный адрес зарегистрирован и не подтверждён, вам отправлено письмо.',
            )
            return redirect('users:login')

        if user.is_active:
            messages.info(request, 'Этот аккаунт уже подтверждён. Войдите или восстановите пароль.')
            return redirect('users:login')

        try:
            send_verification_email(request, user)
            messages.success(request, 'Письмо с подтверждением отправлено.')
        except Exception:
            messages.error(
                request,
                'Не удалось отправить письмо. Проверьте настройки почты на сервере или попробуйте позже.',
            )
        return redirect('users:login')

    return render(request, 'users/resend_verification.html')


@login_required
def cards_view(request):
    """Страница управления картами"""
    cards = UserCard.objects.filter(user=request.user)
    return render(request, 'users/cards.html', {'cards': cards})


@login_required
def add_card_view(request):
    """Добавление новой карты"""
    if request.method == 'POST':
        form = UserCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            # Если это первая карта или выбрана как карта по умолчанию
            if card.is_default or not UserCard.objects.filter(user=request.user, is_default=True).exists():
                UserCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
                card.is_default = True
            card.save()
            messages.success(request, 'Карта успешно добавлена!')
            log_user_activity(
                request.user,
                'profile_update',
                f'Добавлена карта {card.get_display_number()}',
                request
            )
            return redirect('users:cards')
    else:
        form = UserCardForm()
    
    return render(request, 'users/add_card.html', {'form': form})


@login_required
def delete_card_view(request, card_id):
    """Удаление карты"""
    card = get_object_or_404(UserCard, id=card_id, user=request.user)
    if request.method == 'POST':
        card_display = card.get_display_number()
        card.delete()
        messages.success(request, f'Карта {card_display} удалена!')
        log_user_activity(
            request.user,
            'profile_update',
            f'Удалена карта {card_display}',
            request
        )
        return redirect('users:cards')
    return render(request, 'users/delete_card.html', {'card': card})


@login_required
def set_default_card_view(request, card_id):
    """Установить карту по умолчанию"""
    card = get_object_or_404(UserCard, id=card_id, user=request.user)
    UserCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
    card.is_default = True
    card.save()
    messages.success(request, f'Карта {card.get_display_number()} установлена по умолчанию!')
    return redirect('users:cards')


@login_required
def addresses_view(request):
    """Страница управления адресами"""
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'users/addresses.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    """Добавление нового адреса"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # Если это первый адрес или выбран как основной
            if address.is_default or not Address.objects.filter(user=request.user, is_default=True).exists():
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                address.is_default = True
            address.save()
            messages.success(request, 'Адрес успешно добавлен!')
            log_user_activity(
                request.user,
                'profile_update',
                f'Добавлен адрес: {address.get_full_address()}',
                request
            )
            return redirect('users:profile')
    else:
        form = AddressForm()
    
    return render(request, 'users/add_address.html', {'form': form})


@login_required
def delete_address_view(request, address_id):
    """Удаление адреса"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address_display = address.get_full_address()
        address.delete()
        messages.success(request, f'Адрес {address_display} удален!')
        log_user_activity(
            request.user,
            'profile_update',
            f'Удален адрес {address_display}',
            request
        )
        return redirect('users:profile')
    return render(request, 'users/delete_address.html', {'address': address})


@login_required
def set_default_address_view(request, address_id):
    """Установить адрес по умолчанию"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, f'Адрес {address.get_full_address()} установлен по умолчанию!')
    return redirect('users:profile')
