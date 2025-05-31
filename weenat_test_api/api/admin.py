from django.contrib import admin
from .models import Datalogger, Measurement

admin.site.register(Datalogger)
admin.site.register(Measurement)