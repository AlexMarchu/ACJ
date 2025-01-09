from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_mail_async(subject, content, from_email, recipient_list):
    try:
        send_mail(subject, content, from_email, recipient_list)
        print("Письмо успешно отправлено")
    except Exception as e:
        print(f"Ошибка при отправке письма: {str(e)}")
