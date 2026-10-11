# pharmacies/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from pharmacies.models import Pharmacy, CashRegister
from sales.forms import CashRegisterOpenForm, CashRegisterCloseForm
from activity_logs.models import ActivityLog, Notification
from .forms import PharmacyForm
from accounts.forms import AgentCreationForm, AgentEditForm
from accounts.models import User
from accounts.decorators import admin_required


@login_required
@admin_required
def pharmacy_list_create(request):
    """Permet à l'Admin de voir toutes les pharmacies et d'en ajouter une nouvelle."""
    if request.method == 'POST':
        form = PharmacyForm(request.POST)
        if form.is_valid():
            pharmacy = form.save()
            messages.success(request, f"La pharmacie '{pharmacy.name}' a été créée avec succès.")
            return redirect('pharmacies:pharmacy_list_create')
    else:
        form = PharmacyForm()

    pharmacies = Pharmacy.objects.all()
    agents = User.objects.filter(role=User.Role.AGENT).select_related('pharmacy')
    agent_form = AgentCreationForm()

    context = {
        'form': form,
        'agent_form': agent_form,
        'pharmacies': pharmacies,
        'agents': agents,
    }
    return render(request, 'pharmacies/pharmacy_management.html', context)


@login_required
@admin_required
def edit_pharmacy(request, pk):
    """Modification d'une pharmacie existante."""
    pharmacy = get_object_or_404(Pharmacy, pk=pk)
    if request.method == 'POST':
        form = PharmacyForm(request.POST, instance=pharmacy)
        if form.is_valid():
            form.save()
            messages.success(request, f"La pharmacie '{pharmacy.name}' a été modifiée avec succès.")
            return redirect('pharmacies:pharmacy_list_create')
    return redirect('pharmacies:pharmacy_list_create')


@login_required
@admin_required
def delete_pharmacy(request, pk):
    """Suppression d'une pharmacie."""
    pharmacy = get_object_or_404(Pharmacy, pk=pk)
    if request.method == 'POST':
        name = pharmacy.name
        pharmacy.delete()
        messages.success(request, f"La pharmacie '{name}' a été supprimée.")
    return redirect('pharmacies:pharmacy_list_create')


@login_required
@admin_required
def create_agent(request):
    """Création d'un agent/vendeur et affectation à une pharmacie."""
    if request.method == 'POST':
        form = AgentCreationForm(request.POST)
        if form.is_valid():
            agent = form.save()
            messages.success(
                request,
                f"L'agent '{agent.username}' a été créé et affecté à '{agent.pharmacy.name}'."
            )
            return redirect('pharmacies:pharmacy_list_create')
        else:
            messages.error(request, "Erreur lors de la création de l'agent. Vérifiez les données saisies.")
    return redirect('pharmacies:pharmacy_list_create')


@login_required
@admin_required
def edit_agent(request, pk):
    """Modification d'un agent (réaffectation de pharmacie, username, password)."""
    agent = get_object_or_404(User, pk=pk, role=User.Role.AGENT)
    if request.method == 'POST':
        form = AgentEditForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, f"Les informations de l'agent '{agent.username}' ont été mises à jour.")
        else:
            messages.error(request, "Erreur lors de la modification de l'agent.")
    return redirect('pharmacies:pharmacy_list_create')


@login_required
@admin_required
def delete_agent(request, pk):
    """Suppression d'un agent."""
    agent = get_object_or_404(User, pk=pk, role=User.Role.AGENT)
    if request.method == 'POST':
        username = agent.username
        agent.delete()
        messages.success(request, f"L'agent '{username}' a été supprimé.")
    return redirect('pharmacies:pharmacy_list_create')


@login_required
def open_cash_register(request):
    """Ouverture de caisse pour l'agent connecté"""
    user = request.user
    if not user.pharmacy:
        messages.error(request, "Vous n'êtes affecté à aucune pharmacie.")
        return redirect('accounts:login')

    # Vérifier s'il y a déjà une caisse ouverte
    active_register = CashRegister.objects.filter(
        pharmacy=user.pharmacy,
        agent=user,
        status=CashRegister.Status.OPEN
    ).first()

    if active_register:
        return redirect('sales:pos_terminal')

    if request.method == 'POST':
        form = CashRegisterOpenForm(request.POST)
        if form.is_valid():
            register = form.save(commit=False)
            register.pharmacy = user.pharmacy
            register.agent = user
            register.status = CashRegister.Status.OPEN
            register.save()

            # Traces d'activités & Notification
            ActivityLog.objects.create(
                user=user,
                pharmacy=user.pharmacy,
                action_type=ActivityLog.ActionType.OPEN_CASH,
                description=f"Ouverture de caisse avec un montant initial de {register.opening_amount}"
            )
            Notification.objects.create(
                pharmacy=user.pharmacy,
                category=Notification.Category.CASH_EVENT,
                title="Ouverture de caisse",
                message=f"Caisse ouverte par {user.username} avec {register.opening_amount}."
            )

            messages.success(request, "Caisse ouverte avec succès. Bonnes ventes !")
            return redirect('sales:pos_terminal')
    else:
        form = CashRegisterOpenForm()

    return render(request, 'pharmacies/open_cash.html', {'form': form})


@login_required
def close_cash_register(request):
    """Clôture de caisse avec calcul automatique de l'écart"""
    user = request.user
    active_register = get_object_or_404(
        CashRegister,
        pharmacy=user.pharmacy,
        agent=user,
        status=CashRegister.Status.OPEN
    )

    if request.method == 'POST':
        form = CashRegisterCloseForm(request.POST, instance=active_register)
        if form.is_valid():
            register = form.save(commit=False)
            register.status = CashRegister.Status.CLOSED
            register.closed_at = timezone.now()
            register.save()

            # Traces & Notification
            gap = register.gap_amount
            gap_msg = f" (Écart: {gap})" if gap != 0 else " (Aucun écart)"

            ActivityLog.objects.create(
                user=user,
                pharmacy=user.pharmacy,
                action_type=ActivityLog.ActionType.CLOSE_CASH,
                description=f"Clôture de caisse. Réel: {register.closing_amount_real}, Théorique: {register.theoretical_amount}{gap_msg}"
            )
            Notification.objects.create(
                pharmacy=user.pharmacy,
                category=Notification.Category.CASH_EVENT,
                title="Clôture de caisse",
                message=f"Caisse clôturée par {user.username}. Montant réel: {register.closing_amount_real}. Théorique: {register.theoretical_amount}."
            )

            messages.success(request, f"Caisse clôturée. Écart enregistré : {gap}")
            return redirect('accounts:login')
    else:
        form = CashRegisterCloseForm(instance=active_register)

    context = {
        'form': form,
        'register': active_register,
    }
    return render(request, 'pharmacies/close_cash.html', context)

