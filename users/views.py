from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.conf import settings

from users.forms import SyscallUserAuthenticationForm, SyscallUserCreationForm
from users.models import EmailConfirmationToken


class SyscallUserAuthenticationView(LoginView):
    form_class = SyscallUserAuthenticationForm
    template_name = 'users/authentication.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        return super().form_valid(form)


class SyscallUserRegistrationView(CreateView):
    form_class = SyscallUserCreationForm
    template_name = 'users/registration.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        token_instance = EmailConfirmationToken.objects.create(user=user)
        confirmation_url = self.request.build_absolute_uri(
            reverse('confirm_email', kwargs={'token': token_instance.token})
        )

        subject = 'Подтверждение почты'
        content = f'Подтвердите свою почту по ссылке: {confirmation_url}'

        try:
            send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, [user.email])
            print('Письмо успешно отправлено')
        except Exception as e:
            print(f'Ошибка при отправке: {e}')

        return render(self.request, 'users/request_email_confirmation.html', {'user': user})


class EmailConfirmationView(View):
    def get(self, request, token):
        confirmation_token = get_object_or_404(EmailConfirmationToken, token=token)

        if not confirmation_token.is_valid():
            return render(request, 'users/token_invalid.html')

        user = confirmation_token.user
        user.is_active = True
        user.save()

        login(request, user)
        confirmation_token.delete()

        return redirect('home')
