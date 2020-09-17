from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.views import View
from django.db.models import Q
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
from .forms import SignUpForm, EditUserProfileForm
import stripe


class Home(View):

    def get(self, request, category_slug=None):
        category_page = None
        products_list = None
        if category_slug is not None:
            category_page = get_object_or_404(Category, slug=category_slug)
            products_list = Product.objects.filter(category=category_page, available=True)
        else:
            products_list = Product.objects.filter(available=True)

        paginator = Paginator(products_list, 4)

        try:
            page = int(request.GET.get('page', '1'))
        except Exception:
            page = 1

        try:
            products = paginator.page(page)
        except(EmptyPage, InvalidPage):
            products = paginator.page(paginator.num_pages)

        return render(request, 'home.html', {'category': category_page, 'products': products})


def productPage(request, category_slug, product_slug):
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(product=product,
                              user=request.user,
                              content=request.POST['content'])

    reviews = Review.objects.filter(product=product)

    return render(request, 'product.html', {'product': product, 'reviews': reviews})


class AddToCart(View):

    @method_decorator(login_required(redirect_field_name='next', login_url='signin'))
    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(cart_id=request.user)

        try:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
            )
        return redirect('cart_detail')


class DecrementProductFromCart(View):

    def get(self, request, product_id):
        cart = Cart.objects.get(cart_id=request.user)
        product = get_object_or_404(Product, id=product_id)
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
        return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=request.user)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'Z-Store - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']
            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']
            customer = stripe.Customer.create(
                email=email,
                source=token
            )
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='usd',
                description=description,
                customer=customer.id
            )
            # Creating the order
            try:
                order_details = Order.objects.create(
                    token=token,
                    total=total,
                    emailAddress=email,
                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostcode=billingPostcode,
                    billingCountry=billingCountry,
                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostcode=shippingPostcode,
                    shippingCountry=shippingCountry
                )

                for order_item in cart_items:
                    OrderItem.objects.create(
                        product=order_item.product.name,
                        quantity=order_item.quantity,
                        price=order_item.product.price,
                        order=order_details
                    )

                    # reduce stock
                    products = Product.objects.get(id=order_item.product.id)
                    products.stock = int(order_item.product.stock - order_item.quantity)
                    products.save()
                    order_item.delete()

                    # print a message when the order is created
                    print('the order has been created')
                return redirect('thanks_page', order_details.id)

            except ObjectDoesNotExist:
                pass

        except stripe.error.CardError as e:
            return False, e
    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter, data_key=data_key, stripe_total=stripe_total, description=description))


class RemoveCartProduct(View):

    def get(self, request, product_id):
        cart = Cart.objects.get(cart_id=request.user)
        product = get_object_or_404(Product, id=product_id)
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.delete()
        return redirect('cart_detail')


class ThankYouPage(View):

    def get(self, request, order_id):
        if order_id:
            customer_order = get_object_or_404(Order, id=order_id)
        return render(request, 'thankyou.html', {'customer_order': customer_order})


def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            login(request, signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('home')


class OrderHistory(View):

    @method_decorator(login_required(redirect_field_name='next', login_url='signin'))
    def get(self, request):
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
        return render(request, 'orders_list.html', {'order_details': order_details})


class ViewOrder(View):

    @method_decorator(login_required(redirect_field_name='next', login_url='signin'))
    def get(self, request, order_id):
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
        return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})


class Search(View):

    def get(self, request):
        query = request.GET.get('query')
        products = Product.objects.all()
        products = products.filter(Q(category__name__icontains=query) | Q(name__icontains=query))
        return render(request, 'home.html', {'products': products})


def user_profile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = EditUserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                messages.success(request, 'Profile Updated!!')
                form.save()
        else:
            form = EditUserProfileForm(instance=request.user)
        return render(request, 'profile.html', {'name': request.user, 'form': form})
    else:
        return render('home.html')
