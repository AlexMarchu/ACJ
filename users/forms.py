from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, SetPasswordForm, \
    PasswordChangeForm

from users.models import ACJUser


class ACJUserAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин',
            'required': 'required',
            'autofocus': 'autofocus'
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль',
            'required': 'required',
        })
    )

    class Meta:
        model = ACJUser
        fields = ('username', 'password')


class ACJUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин',
            'required': 'required',
            'autofocus': 'autofocus',
        })
    )

    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль',
            'required': 'required',
        })
    )

    password2 = forms.CharField(
        label='Пароль (подтверждение)',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль',
            'required': 'required',
        })
    )

    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Электронная почта',
            'required': 'required',
        })
    )

    class Meta:
        model = ACJUser
        fields = ('username', 'password1', 'password2', 'email')


class ACJUserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Адрес электронной почты',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ваш email',
            'required': 'required'
        })
    )


class ACJUserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Новый пароль',
            'required': 'required',
            'autofocus': 'autofocus'
        })
    )

    new_password2 = forms.CharField(
        label='Новый пароль (подтверждение)',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Подтвердите новый пароль',
            'required': 'required'
        })
    )


class ACJPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['old_password'].widget.attrs.pop('autofocus', None)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = ACJUser
        fields = ('first_name', 'last_name', 'country', 'city', 'institution', 'birth_date')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'country': 'Страна',
            'city': 'Город / регион',
            'institution': 'Учебное заведение',
            'birth_date': 'Дата рождения'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
        }
