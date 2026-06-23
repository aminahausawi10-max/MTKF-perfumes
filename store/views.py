from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from urllib.parse import quote
from decimal import Decimal
from .models import Brand, Category, Product, Order, OrderItem
from django import forms

# --- Helper function for checking if a user is staff/admin ---
def is_admin(user):
    return user.is_authenticated and user.is_staff

# --- Custom Forms ---
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'brand', 'category', 'image', 'stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'brand': forms.Select(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'image': forms.FileInput(attrs={'class': 'form-input-file'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
        }

class CheckoutForm(forms.Form):
    delivery_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}))
    delivery_phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number (e.g. +234...)'}))
    delivery_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Delivery Address', 'rows': 3}))

# --- Authentication Views ---
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('catalog')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MTKF Perfumes, {user.username}!")
            return redirect('catalog')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('catalog')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# --- Store Catalog & Detail Views ---
@login_required
def catalog_view(request):
    products = Product.objects.all().select_related('brand', 'category')
    categories = Category.objects.all()
    brands = Brand.objects.all()

    # Search & Filters
    search_query = request.GET.get('search', '')
    category_slug = request.GET.get('category', '')
    brand_slug = request.GET.get('brand', '')

    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_brand': brand_slug,
    }
    return render(request, 'catalog.html', context)

@login_required
def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Get standard related products from the same category
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'product_detail.html', {'product': product, 'related_products': related_products})

# --- Session Cart Views ---
# Session cart structure: request.session['cart'] = {str(product_id): quantity}
@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')

    for prod_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(prod_id))
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            continue

    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    quantity = int(request.POST.get('quantity', 1))
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
        
    request.session['cart'] = cart
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect('cart')

@login_required
def update_cart_view(request, product_id):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            cart.pop(str(product_id), None)
        request.session['cart'] = cart
        messages.success(request, "Cart updated successfully.")
    return redirect('cart')

@login_required
def remove_from_cart_view(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

# --- WhatsApp Checkout ---
@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('catalog')

    cart_items = []
    total = Decimal('0.00')
    for prod_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(prod_id))
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price
            })
        except Product.DoesNotExist:
            continue

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 1. Create order
            order = Order.objects.create(
                user=request.user,
                total_price=total,
                delivery_name=form.cleaned_data['delivery_name'],
                delivery_phone=form.cleaned_data['delivery_phone'],
                delivery_address=form.cleaned_data['delivery_address']
            )
            # 2. Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                # Deduct stock if possible
                if item['product'].stock >= item['quantity']:
                    item['product'].stock -= item['quantity']
                    item['product'].save()

            # Clear session cart
            request.session['cart'] = {}

            # 3. Format WhatsApp Message
            # Let's specify a premium store number or let user redirect to any
            store_whatsapp_number = settings.WHATSAPP_PHONE_NUMBER
            
            message_header = f"🛍️ *MTKF PERFUMES ORDER CONFIRMATION*\n"
            message_header += f"----------------------------------\n"
            message_header += f"*Order ID:* #{order.id}\n"
            message_header += f"*Customer Name:* {order.delivery_name}\n"
            message_header += f"*Contact Phone:* {order.delivery_phone}\n"
            message_header += f"*Delivery Address:* {order.delivery_address}\n\n"
            
            message_items = "*ITEMS ORDERED:*\n"
            for item in cart_items:
                message_items += f"- {item['quantity']} x {item['product'].name} (@ ${item['price']} each)\n"
            
            message_total = f"\n*TOTAL VALUE:* ${total}\n"
            message_total += f"----------------------------------\n"
            message_total += f"Hello MTKF Perfumes! I have placed my order #{order.id} via the app and would like to complete my payment."

            full_msg = message_header + message_items + message_total
            encoded_msg = quote(full_msg)
            
            whatsapp_url = f"https://wa.me/{store_whatsapp_number}?text={encoded_msg}"
            
            return render(request, 'checkout_success.html', {
                'order': order,
                'whatsapp_url': whatsapp_url
            })
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total': total
    })

# --- In-App Admin/Staff Dashboard CRUD ---
@user_passes_test(is_admin, login_url='login')
def admin_dashboard_view(request):
    products = Product.objects.all().select_related('brand', 'category')
    orders = Order.objects.all().order_by('-created_at')[:10]
    total_sales = sum(o.total_price for o in Order.objects.filter(status='COMPLETED'))
    
    context = {
        'products': products,
        'orders': orders,
        'total_sales': total_sales,
        'total_products': products.count(),
        'total_orders': Order.objects.count(),
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(is_admin, login_url='login')
def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.name)
            product.save()
            messages.success(request, f"Product '{product.name}' added successfully.")
            return redirect('admin_dashboard')
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form, 'title': 'Add New Perfume'})

@user_passes_test(is_admin, login_url='login')
def admin_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.name)
            product.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('admin_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'product_form.html', {'form': form, 'title': f'Edit {product.name}', 'product': product})

@user_passes_test(is_admin, login_url='login')
def admin_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted successfully.")
        return redirect('admin_dashboard')
    return render(request, 'product_confirm_delete.html', {'product': product})

# --- Additional Pages Views ---
@login_required
def about_view(request):
    return render(request, 'about.html')

@login_required
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # In a real app, send email or save in database.
        messages.success(request, f"Thank you, {name}! Your message has been sent. Our team will contact you shortly.")
        return redirect('contact')
    return render(request, 'contact.html')

@login_required
def profile_view(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items__product')
    return render(request, 'profile.html', {
        'orders': user_orders,
        'total_orders': user_orders.count()
    })

