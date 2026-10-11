from django import forms
from pharmacies.models import CashRegister
from sales.models import Credit

class CashRegisterOpenForm(forms.ModelForm):
    class Meta:
        model = CashRegister
        fields = ['opening_amount']
        widgets = {
            'opening_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: 50000',
                'min': '0',
                'step': '500'
            })
        }
        labels = {
            'opening_amount': "Montant initial présent en caisse"
        }


class CashRegisterCloseForm(forms.ModelForm):
    class Meta:
        model = CashRegister
        fields = ['closing_amount_real']
        widgets = {
            'closing_amount_real': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Saisissez le montant réellement compté',
                'min': '0',
                'step': '500'
            })
        }
        labels = {
            'closing_amount_real': "Montant réel compté en caisse"
        }


class CreditDetailsForm(forms.ModelForm):
    class Meta:
        model = Credit
        fields = ['client_name', 'reason']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet du client'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motif du crédit...'}),
        }

