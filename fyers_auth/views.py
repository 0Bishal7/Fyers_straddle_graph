from django.shortcuts import render
from .models import FyersToken

def get_token_view(request):
    token = FyersToken.objects.first()
    return render(request, "token.html", {"token": token.access_token})
