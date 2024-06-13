# views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Song
from .tasks import convert_playlist_
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
import json
import redis
from .models import BetaTestingRequest
import logging

logger = logging.getLogger(__name__)




def index(request):
    return render(request, 'sonoshareapp/index.html')

def get_access(request):
    return render(request, 'sonoshareapp/get_access.html')

def about(request):
    return render(request, 'sonoshareapp/about.html')

def contact(request):
    return render(request, 'sonoshareapp/contact.html')

def beta_testing(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Check if the email already exists in the database
        if BetaTestingRequest.objects.filter(email=email).exists():
            return render(request, 'sonoshareapp/beta_testing_exists.html', {'email': email})
        
        BetaTestingRequest.objects.create(email=email)
        
        # Send confirmation email to the user
        subject = 'Beta Testing Request Confirmation'
        message = 'Thank you for your interest in beta testing SonusShare! We have received your request and will review it shortly.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        try:
            send_mail(subject, message, from_email, recipient_list)
            logger.info(f"Confirmation email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending confirmation email to {email}: {str(e)}")
        
        # Send notification email to support@sonusshare.com
        subject = 'New Beta Testing Request'
        message = f'A new beta testing request has been submitted. Email: {email}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['support@sonusshare.com']
        try:
            send_mail(subject, message, from_email, recipient_list)
            logger.info(f"Notification email sent to support@sonusshare.com for {email}")
        except Exception as e:
            logger.error(f"Error sending notification email to support@sonusshare.com for {email}: {str(e)}")
        
        return render(request, 'sonoshareapp/beta_testing_success.html')
    
    return render(request, 'sonoshareapp/get_access.html')

def send_beta_testing_email(recipients=[]):
    subject = 'SonusShare Beta Testing Invitation'
    message = 'Dear user,\n\nWe are excited to invite you to participate in the beta testing of SonusShare! Your access has been granted, and you can now start using the application.\n\nTo get started, please visit our website at https://www.sonusshare.com and log in using your registered email address.\n\nWe appreciate your interest in testing SonusShare and helping us improve the platform. If you have any questions or feedback, please don\'t hesitate to reach out to us at support@sonusshare.com.\n\nBest regards,\nThe SonusShare Team'
    from_email = 'support@sonusshare.com'
    recipient_list = recipients
    
    sent_count = send_mail(subject, message, from_email, recipient_list)
    
    print(f"Email sent to {sent_count} recipient(s).")


def convert_playlist(request):

    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        task = convert_playlist_.delay(playlist_url)

        return JsonResponse({'task_id': task.task_id})
    else:
        return redirect('index')

def progress(request):
    task_id = request.session.get('task_id')
    if task_id:
        return render(request, 'sonoshareapp/progress.html', {'task_id': task_id})
    else:
        return redirect('index')
    
def review_playlist(request):
    data = json.loads(request.GET.get('data', '{}'))
    return render(request, 'sonoshareapp/review_playlist.html', data)

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})

def test_redis_connection(request):
    redis_url = settings.CELERY_BROKER_URL
    try:
        redis_client = redis.from_url(redis_url, ssl_cert_reqs=None)
        redis_client.ping()
        return HttpResponse("Redis connection successful!")
    except redis.exceptions.ConnectionError as e:
        return HttpResponse(f"Redis connection failed: {str(e)}")
