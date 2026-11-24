from django.db import models

# Create your models here.




class USSDSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user_id = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    current_step = models.CharField(max_length=20, default='feeling')
    feeling = models.CharField(max_length=50, blank=True)
    reason = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.session_id