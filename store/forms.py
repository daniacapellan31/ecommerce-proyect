from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Store, Product, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[('vendor', 'Vendor'), ('buyer', 'Buyer')])

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'description']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['store', 'name', 'description', 'price', 'stock']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']