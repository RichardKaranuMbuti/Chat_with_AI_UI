from django.db import models
import random
import string
from datetime import datetime

# Create your models here.

# User Model
class UserSignup(models.Model):
    user_id = models.CharField(max_length=13, unique=True, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.user_id:
            # Generate a 13-character user_id with a mix of 7 numbers and 6 letters
            numbers = ''.join(random.choices(string.digits, k=7))
            letters = ''.join(random.choices(string.ascii_letters, k=6))
            user_id_list = list(numbers + letters)
            random.shuffle(user_id_list)
            user_id = ''.join(user_id_list)

            # Check if the generated user_id already exists in the database
            while UserSignup.objects.filter(user_id=user_id).exists():
                random.shuffle(user_id_list)
                user_id = ''.join(user_id_list)

            self.user_id = user_id

        super(UserSignup, self).save(*args, **kwargs)

