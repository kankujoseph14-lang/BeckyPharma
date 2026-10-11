# pharmacies/forms.py
from django import forms
from .models import Pharmacy

class PharmacyForm(forms.ModelForm):
    class Meta:
        model = Pharmacy
        fields = ['name', 'address', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la boutique'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse complète'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +243... / +221...'}),
        }
