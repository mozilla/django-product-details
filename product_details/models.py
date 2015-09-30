from django.db import models


class ProductDetailsFile(models.Model):
    name = models.CharField(max_length=250, primary_key=True)
    content = models.TextField(blank=True)
    last_modified = models.CharField(max_length=50,
                                     help_text='Value of Last-Modified HTTP header')
