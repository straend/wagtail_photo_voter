from django.contrib import admin

# Register your models here.
from .models import Competition, EntryImage, Votes

admin.site.register(Competition)
admin.site.register(EntryImage)
admin.site.register(Votes)
