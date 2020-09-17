from .models import Category, CartItem, Cart


def counter(request):
    item_count = 0
    if 'admin' in request.path:
        return {}
    else:
        user = request.user.is_authenticated
        if user:
            try:
                cart = Cart.objects.filter(cart_id=request.user)
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
                for cart_item in cart_items:
                    item_count += cart_item.quantity
            except Cart.DoesNotExist:
                item_count = 0
        return dict(item_count=item_count)


def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)
