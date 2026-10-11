# inventory/forms.py
from django import forms
from .models import Product
from pharmacies.models import Pharmacy

class ProductForm(forms.ModelForm):
    pharmacy = forms.ModelChoiceField(
        queryset=Pharmacy.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Pharmacie / Boutique d'affectation"
    )

    class Meta:
        model = Product
        fields = ['pharmacy', 'name', 'stock_quantity', 'purchase_price', 'selling_price', 'expiration_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom commercial et dosage'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'name': 'Nom du produit',
            'stock_quantity': 'Quantité en stock',
            'purchase_price': "Prix d'achat unitaire",
            'selling_price': 'Prix de vente unitaire',
            'expiration_date': 'Date de péremption',
        }

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        selling_price = cleaned_data.get('selling_price')

        if purchase_price and selling_price and selling_price < purchase_price:
            self.add_error('selling_price', "Le prix de vente ne peut pas être inférieur au prix d'achat !")
        return cleaned_data

