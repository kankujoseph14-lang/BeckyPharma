# accounts/forms.py
from django import forms
from .models import User

class AdminSetupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe administrateur'}),
        label="Mot de passe"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le mot de passe'}),
        label="Confirmation du mot de passe"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur Admin"}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse email'}),
        }
        labels = {
            'username': "Nom d'utilisateur",
            'first_name': "Prénom",
            'last_name': "Nom",
            'email': "Adresse email",
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True  # Octroie les droits complets pour le premier compte
        if commit:
            user.save()
        return user


class AgentCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe sécurisé'}),
        label="Mot de passe"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'pharmacy', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur unique"}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse email (optionnel)'}),
            'pharmacy': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'username': "Nom d'utilisateur",
            'pharmacy': "Pharmacie d'affectation",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = User.Role.AGENT
        user.is_staff = False
        if commit:
            user.save()
        return user


class AgentEditForm(forms.ModelForm):
    """Formulaire permettant de modifier un agent existant (affectation, username, email, mot de passe)."""
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Laissez vide pour conserver le mot de passe actuel'}),
        label="Nouveau mot de passe (optionnel)"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'pharmacy']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'pharmacy': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'pharmacy': "Pharmacie d'affectation",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user

