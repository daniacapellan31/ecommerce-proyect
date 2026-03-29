from decimal import Decimal
from datetime import timedelta
import secrets

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import RegisterForm, StoreForm, ProductForm, ReviewForm
from .models import Store, Product, Order, OrderItem, Review, PasswordResetToken


def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']

            if role == 'vendor':
                group, created = Group.objects.get_or_create(name='Vendors')
                user.groups.add(group)
            else:
                group, created = Group.objects.get_or_create(name='Buyers')
                user.groups.add(group)

            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def create_store(request):
    if not request.user.groups.filter(name='Vendors').exists():
        return HttpResponseForbidden("Only vendors can create stores.")

    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user
            store.save()
            return redirect('my_stores')
    else:
        form = StoreForm()

    return render(request, 'store/create_store.html', {'form': form})


@login_required
def my_stores(request):
    stores = Store.objects.filter(owner=request.user)
    return render(request, 'store/my_stores.html', {'stores': stores})


@login_required
def edit_store(request, store_id):
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            return redirect('my_stores')
    else:
        form = StoreForm(instance=store)

    return render(request, 'store/edit_store.html', {'form': form})


@login_required
def delete_store(request, store_id):
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    if request.method == 'POST':
        store.delete()
        return redirect('my_stores')

    return render(request, 'store/delete_store.html', {'store': store})


@login_required
def create_product(request):
    if not request.user.groups.filter(name='Vendors').exists():
        return HttpResponseForbidden("Only vendors can create products.")

    if request.method == 'POST':
        form = ProductForm(request.POST)
        form.fields['store'].queryset = Store.objects.filter(owner=request.user)
        if form.is_valid():
            product = form.save()
            return redirect('home')
    else:
        form = ProductForm()
        form.fields['store'].queryset = Store.objects.filter(owner=request.user)

    return render(request, 'store/create_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, store__owner=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        form.fields['store'].queryset = Store.objects.filter(owner=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductForm(instance=product)
        form.fields['store'].queryset = Store.objects.filter(owner=request.user)

    return render(request, 'store/edit_product.html', {'form': form})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, store__owner=request.user)

    if request.method == 'POST':
        product.delete()
        return redirect('home')

    return render(request, 'store/delete_product.html', {'product': product})


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    product_id_str = str(product.id)

    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('view_cart')


@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required
def checkout(request):
    if not request.user.groups.filter(name='Buyers').exists():
        return HttpResponseForbidden("Only buyers can checkout.")

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')

    order = Order.objects.create(buyer=request.user, total_price=Decimal('0.00'))
    total = Decimal('0.00')
    invoice_lines = []

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)

        if product.stock < quantity:
            messages.error(request, f'Not enough stock for {product.name}.')
            order.delete()
            return redirect('view_cart')

        subtotal = product.price * quantity
        total += subtotal

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_purchase=product.price
        )

        product.stock -= quantity
        product.save()

        invoice_lines.append(
            f"{product.name} - Quantity: {quantity} - Price: {product.price} - Subtotal: {subtotal}"
        )

    order.total_price = total
    order.save()

    request.session['cart'] = {}
    request.session.modified = True

    if request.user.email:
        invoice_message = "Thank you for your purchase.\n\nInvoice:\n" + "\n".join(invoice_lines) + f"\n\nTotal: {total}"
        send_mail(
            subject='Your Invoice',
            message=invoice_message,
            from_email='test@example.com',
            recipient_list=[request.user.email],
            fail_silently=True,
        )

    return render(request, 'store/checkout_success.html', {'order': order})


@login_required
def add_review(request, product_id):
    if not request.user.groups.filter(name='Buyers').exists():
        return HttpResponseForbidden("Only buyers can leave reviews.")

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            verified = OrderItem.objects.filter(
                order__buyer=request.user,
                product=product
            ).exists()

            review = form.save(commit=False)
            review.buyer = request.user
            review.product = product
            review.verified_purchase = verified
            review.save()

            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'store/add_review.html', {'form': form, 'product': product})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(minutes=15)

            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )

            reset_link = request.build_absolute_uri(
                reverse('reset_password', args=[token])
            )

            send_mail(
                subject='Password Reset',
                message=f'Use this link to reset your password: {reset_link}',
                from_email='test@example.com',
                recipient_list=[user.email],
                fail_silently=True,
            )

            messages.success(request, 'Password reset email sent.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')

    return render(request, 'store/forgot_password.html')


def reset_password(request, token):
    reset_token = get_object_or_404(
        PasswordResetToken,
        token=token,
        used=False
    )

    if timezone.now() > reset_token.expires_at:
        messages.error(request, 'This reset link has expired.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            reset_token.used = True
            reset_token.save()

            messages.success(request, 'Password changed successfully.')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'store/reset_password.html', {'token': token})