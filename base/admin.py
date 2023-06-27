from django.contrib import admin
from .models import *

# Register your models here.

models = [Room, Topic, Message]

admin.site.register(models)