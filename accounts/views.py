# accounts/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, get_user_model
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from activity_logs.models import ActivityLog, Notification
from .forms import AdminSetupForm

User = get_user_model()


class AdminSetupView(View):
    """Vue d'initialisation du premier compte administrateur (Onboarding)."""
    template_name = 'accounts/setup.html'

    def dispatch(self, request, *args, **kwargs):
        # Si un admin existe déjà, la page de configuration est verrouillée
        if User.objects.filter(role=User.Role.ADMIN).exists():
            messages.warning(request, "La configuration initiale a déjà été réalisée.")
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = AdminSetupForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AdminSetupForm(request.POST)
        if form.is_valid():
            admin_user = form.save()
            login(request, admin_user)  # Connecte directement le propriétaire
            messages.success(request, "Compte Administrateur configuré avec succès !")
            return redirect('pharmacies:pharmacy_list_create')  # Redirige vers la gestion des pharmacies/agents
        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # Si aucun administrateur n'existe dans le système, redirection forcée vers le setup
        if not User.objects.filter(role=User.Role.ADMIN).exists():
            return redirect('accounts:setup')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user

        # Journal d'activité & Notification
        ActivityLog.objects.create(
            user=user,
            pharmacy=user.pharmacy,
            action_type=ActivityLog.ActionType.LOGIN,
            description=f"Connexion de l'utilisateur {user.username}"
        )

        if user.is_agent_role():
            Notification.objects.create(
                pharmacy=user.pharmacy,
                category=Notification.Category.AGENT_EVENT,
                title="Connexion Agent",
                message=f"L'agent {user.username} s'est connecté."
            )
            return reverse_lazy('sales:pos_terminal')

        return reverse_lazy('pharmacies:pharmacy_list_create')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            ActivityLog.objects.create(
                user=request.user,
                pharmacy=request.user.pharmacy,
                action_type=ActivityLog.ActionType.LOGOUT,
                description=f"Déconnexion de l'utilisateur {request.user.username}"
            )
            if request.user.is_agent_role():
                Notification.objects.create(
                    pharmacy=request.user.pharmacy,
                    category=Notification.Category.AGENT_EVENT,
                    title="Déconnexion Agent",
                    message=f"L'agent {request.user.username} s'est déconnecté."
                )
        return super().dispatch(request, *args, **kwargs)

