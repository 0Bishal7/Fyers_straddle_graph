from celery import shared_task
from .utils import get_fyers_access_token

@shared_task
def refresh_fyers_token():
    get_fyers_access_token()
