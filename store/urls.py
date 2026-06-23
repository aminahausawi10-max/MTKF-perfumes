from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Shop Catalog
    path('', views.catalog_view, name='catalog'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_view, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart_view, name='remove_from_cart'),

    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),

    # Additional Pages
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('profile/', views.profile_view, name='profile'),

    # Admin CRUD Dashboard
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/add/', views.admin_add_product, name='admin_add_product'),
    path('admin-dashboard/edit/<int:pk>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-dashboard/delete/<int:pk>/', views.admin_delete_product, name='admin_delete_product'),
]
