from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    Home,
    productPage,
    AddToCart,
    cart_detail,
    DecrementProductFromCart,
    RemoveCartProduct,
    ThankYouPage,
    signupView,
    signinView,
    signoutView,
    OrderHistory,
    ViewOrder,
    Search,
    user_profile,
    )


urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('category/<slug:category_slug>', Home.as_view(), name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', productPage, name='product_detail'),
    path('cart/add/<int:product_id>', AddToCart.as_view(), name='add_cart'),
    path('cart', cart_detail, name='cart_detail'),
    path('cart/remove/<int:product_id>', DecrementProductFromCart.as_view(), name='cart_remove'),
    path('cart/remove_product/<int:product_id>', RemoveCartProduct.as_view(), name='cart_remove_product'),
    path('thankyou/<int:order_id>', ThankYouPage.as_view(), name='thanks_page'),
    path('account/create/', signupView, name='signup'),
    path('account/signin/', signinView, name='signin'),
    path('account/signout/', signoutView, name='signout'),
    path('order_history/', OrderHistory.as_view(), name='order_history'),
    path('order/<int:order_id>', ViewOrder.as_view(), name='order_detail'),
    path('search/', Search.as_view(), name='search'),
    path('profile/', user_profile, name='profile'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]
