from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetConfirmView
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View, generic
from django.conf import settings

from users.forms import ACJUserAuthenticationForm, ACJUserCreationForm, ACJUserPasswordResetForm, \
    ACJUserSetPasswordForm, ProfileEditForm
from users.models import EmailConfirmationToken, ACJUser


class ACJUserAuthenticationView(LoginView):
    form_class = ACJUserAuthenticationForm
    template_name = 'auth/authentication.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        return super().form_valid(form)


class ACJUserRegistrationView(CreateView):
    form_class = ACJUserCreationForm
    template_name = 'auth/registration.html'
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

        return render(self.request, 'auth/request_email_confirmation.html', {'user': user})


class EmailConfirmationView(View):
    def get(self, request, token):
        confirmation_token = get_object_or_404(EmailConfirmationToken, token=token)

        if not confirmation_token.is_valid():
            return render(request, 'auth/token_invalid.html')

        user = confirmation_token.user
        user.is_active = True
        user.save()

        login(request, user)
        confirmation_token.delete()

        return redirect('home')


class ACJUserPasswordResetView(generic.View):
    template_name = 'auth/password_reset.html'
    form_class = ACJUserPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return render(request, 'auth/email_not_found.html')

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            password_reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            subject = 'Сброс пароля для ACJ'
            content = (
                f'Здравствуйте!\n\n'
                f'Вы получили это письмо, потому что мы получили запрос на сброс пароля для вашей учетной '
                f'записи в ACJ.\n\n'
                f'Чтобы сбросить пароль, перейдите по следующей ссылке:\n{password_reset_url}\n'
                'Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо и '
                'ваш пароль останется неизменным.\n\n'
                'Спасибо,\n'
                'Команда ACJ.'
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            try:
                send_mail(subject, content, from_email, recipient_list)
                print('Письмо успешно отправлено')
            except Exception as e:
                print(f'Ошибка при отправке письма: {e}')

            return render(request, 'auth/password_reset_done.html')

        return render(request, self.template_name, {'form': form})


class ACJUserPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = ACJUserSetPasswordForm
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class PasswordResetCompleteView(TemplateView):
    template_name = 'auth/password_reset_complete.html'


@login_required(login_url='/auth/login/')
def profile_view(request, username):
    profile_owner = get_object_or_404(ACJUser, username=username)
    is_owner = profile_owner == request.user

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile_owner)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)

    else:
        form = ProfileEditForm(instance=profile_owner)

    context = {
        'profile_owner': profile_owner,
        'is_owner': is_owner,
        'form': form,
    }

    return render(request, 'profiles/profile.html', context)


@login_required(login_url='/auth/login/')
def settings_view(request):
    profile_owner = request.user
    return render(request, 'profiles/settings.html', {"profile_owner": profile_owner})


def statistics_view(request, username):
    profile_owner = get_object_or_404(ACJUser, username=username)
    return render(request, 'profiles/statistics.html', {"profile_owner": profile_owner})
