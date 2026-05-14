from .models import Category, Favourite


def nav_categories(request):
    return {
        'nav_categories': Category.objects.filter(is_active=True).order_by('name'),
    }


def favourite_ids(request):
    if request.user.is_authenticated:
        ids = set(Favourite.objects.filter(user=request.user).values_list('product_id', flat=True))
        count = len(ids)
    else:
        ids = set()
        count = 0
    return {
        'favourite_ids': ids,
        'favourite_count': count,
    }
