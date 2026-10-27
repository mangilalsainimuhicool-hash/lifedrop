from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from lifedrop.models import UserRole
from lifedrop.forms import UserRegisterForm
from lifedrop.services.audit import record_audit


def register_view(request):
    """Handles new user onboarding across donor, requester, and staff roles."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            record_audit(
                action="USER_REGISTRATION",
                actor=user,
                details=f"User {user.username} registered with role {user.role}.",
                request=request
            )
            messages.success(request, f"Welcome to LifeDrop, {user.first_name}! Your account has been created.")

            # If user registered as a donor, guide them to complete their medical donor profile
            if user.role == UserRole.DONOR:
                messages.info(request, "Please complete your Donor Profile to activate emergency matching.")
                return redirect('donor_register')

            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        initial_role = request.GET.get('role', UserRole.DONOR)
        form = UserRegisterForm(initial={'role': initial_role})

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """Custom login view with security audit logging."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            record_audit(
                action="USER_LOGIN_SUCCESS",
                actor=user,
                details=f"User {user.username} logged in successfully.",
                request=request
            )
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            username_attempt = request.POST.get('username', '')
            record_audit(
                action="USER_LOGIN_FAILED",
                details=f"Failed login attempt for username '{username_attempt}'.",
                request=request
            )
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm(request)

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Logs the user out securely."""
    if request.user.is_authenticated:
        record_audit(
            action="USER_LOGOUT",
            actor=request.user,
            details=f"User {request.user.username} logged out.",
            request=request
        )
        logout(request)
        messages.info(request, "You have been logged out safely.")
    return redirect('home')


@login_required
def profile_view(request):
    """User account details update."""
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone_number = request.POST.get('phone_number', '').strip()
        user.save()

        record_audit(
            action="USER_PROFILE_UPDATED",
            actor=user,
            details=f"User {user.username} updated personal profile information.",
            request=request
        )
        messages.success(request, "Your profile details have been updated successfully.")
        return redirect('profile')

    return render(request, 'auth/profile.html', {'user': user})
