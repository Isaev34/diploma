from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import date
from .models import Banner, Category, Favourite, Feature, Product, Promotion, Review


def home_view(request):
    """Главная страница с акциями"""
    banners = Banner.objects.filter(is_active=True).order_by('order', 'pk')

    sale_products = Product.objects.filter(
        is_active=True,
        in_stock=True,
        discount_percent__gt=0
    )[:8]

    new_products = Product.objects.filter(
        is_active=True,
        in_stock=True
    )[:8]

    categories = Category.objects.filter(is_active=True)[:6]
    features = Feature.objects.filter(is_active=True)

    context = {
        'banners': banners,
        'features': features,
        'sale_products': sale_products,
        'new_products': new_products,
        'categories': categories,
    }
    return render(request, 'catalog/home.html', context)


def category_list_view(request):
    """Список всех категорий"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    context = {
        'categories': categories,
    }
    return render(request, 'catalog/category_list.html', context)


def category_detail_view(request, category_slug):
    """Детальная страница категории с товарами"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    products = Product.objects.filter(
        category=category,
        is_active=True,
        in_stock=True,
    ).select_related('category')
    
    # Поиск по названию и описанию
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'catalog/category_detail.html', context)


def product_list_view(request):
    """Список всех товаров"""
    products = Product.objects.filter(is_active=True, in_stock=True)
    
    # Поиск по названию и описанию (форма на главной передаёт q, страница товаров — search)
    search_query = (request.GET.get('q') or request.GET.get('search') or '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Фильтрация по категории
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Сортировка
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Категории для фильтра
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail_view(request, product_slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    reviews = product.reviews.select_related('user').all()[:20]

    related_products = (
        Product.objects.filter(
            category=product.category,
            is_active=True,
            in_stock=True,
        )
        .exclude(id=product.id)
        .select_related('category')[:4]
    )

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
    }
    return render(request, 'catalog/product_detail.html', context)


def promotions_view(request):
    """Страница акций: именованные акции + прочие скидки"""
    today = date.today()
    category_slug = request.GET.get('category', '')

    # Активные акции в текущем периоде
    active_promotions = list(
        Promotion.objects.filter(
            is_active=True,
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=today)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=today)
        ).order_by('order', 'name')
    )

    # Для каждой акции — отфильтрованный список товаров
    base_qs = Product.objects.filter(is_active=True, in_stock=True).select_related('category')
    for promo in active_promotions:
        qs = promo.products.filter(is_active=True, in_stock=True).select_related('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        promo.filtered_products = list(qs)

    # Убрать акции без видимых товаров при фильтре по категории
    if category_slug:
        active_promotions = [p for p in active_promotions if p.filtered_products]

    # ID товаров, уже входящих в активные акции
    promoted_ids = set(
        Promotion.objects.filter(
            is_active=True,
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=today)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=today)
        ).values_list('products__id', flat=True)
    )
    promoted_ids.discard(None)

    # "Другие скидки" — товары со скидкой вне именованных акций
    other_qs = Product.objects.filter(
        is_active=True,
        in_stock=True,
        discount_percent__gt=0,
    ).exclude(id__in=promoted_ids)
    if category_slug:
        other_qs = other_qs.filter(category__slug=category_slug)
    other_qs = other_qs.order_by('-discount_percent', 'name')

    paginator = Paginator(other_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Категории с любыми акционными товарами
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True,
        products__in_stock=True,
        products__discount_percent__gt=0,
    ).distinct().order_by('name')

    context = {
        'promotions': active_promotions,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
    }
    return render(request, 'catalog/promotions.html', context)


def delivery_view(request):
    """Страница доставки и оплаты"""
    return render(request, 'catalog/delivery.html')


def bonus_program_view(request):
    """Страница с информацией о бонусной программе"""
    bonus_points = 0
    if request.user.is_authenticated:
        bonus_points = request.user.bonus_points
    return render(request, 'catalog/bonus_program.html', {'bonus_points': bonus_points})


@login_required
def favourites_view(request):
    """Страница избранных товаров"""
    favourites = Favourite.objects.filter(user=request.user).select_related('product__category').order_by('-created_at')
    return render(request, 'catalog/favourites.html', {'favourites': favourites})


@login_required
@require_POST
def toggle_favourite(request, product_id):
    """AJAX: добавить/убрать товар из избранного"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    fav, created = Favourite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
        is_favourite = False
    else:
        is_favourite = True
    count = Favourite.objects.filter(user=request.user).count()
    return JsonResponse({'is_favourite': is_favourite, 'count': count})


@login_required
@require_POST
def add_review_view(request, product_slug):
    """Добавить отзыв к товару (только авторизованные, один отзыв на товар)."""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    rating = request.POST.get('rating')
    text = (request.POST.get('text') or '').strip()

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError('Оценка от 1 до 5')
    except (TypeError, ValueError):
        messages.error(request, 'Выберите оценку от 1 до 5 звёзд.')
        return redirect('catalog:product_detail', product_slug=product_slug)

    review, created = Review.objects.get_or_create(
        product=product,
        user=request.user,
        defaults={'rating': rating, 'text': text}
    )
    if not created:
        review.rating = rating
        review.text = text
        review.save()
        messages.success(request, 'Ваш отзыв обновлён.')
    else:
        messages.success(request, 'Спасибо за отзыв!')

    return redirect('catalog:product_detail', product_slug=product_slug)