from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('stores/create/', views.create_store, name='create_store'),
    path('stores/my/', views.my_stores, name='my_stores'),
    path('stores/edit/<int:store_id>/', views.edit_store, name='edit_store'),
    path('stores/delete/<int:store_id>/', views.delete_store, name='delete_store'),

    path('products/create/', views.create_product, name='create_product'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),

    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('review/add/<int:product_id>/', views.add_review, name='add_review'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
]