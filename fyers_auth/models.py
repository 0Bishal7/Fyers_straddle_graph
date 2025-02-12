from django.db import models

class FyersToken(models.Model):
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fyers Token (Created at {self.created_at})"
