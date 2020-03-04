from django.contrib import admin

# Register your models here.
from .models import Competition, EntryImage, Votes, EntryUser, ImageVote

admin.site.register(Competition)

admin.site.register(EntryUser)

@admin.register(ImageVote)
class ImageVoteAdmin(admin.ModelAdmin):
    list_filter = ('entry__competition', )
    list_display  = ('entry_id', 'user')

@admin.register(EntryImage)
class EntryImageAdmin(admin.ModelAdmin):
    list_filter = ('competition', 'user')
    list_display  = ('competition', 'user', 'title')

@admin.register(Votes)
class VotesAdmin(admin.ModelAdmin):
    list_filter = ('entry__competition', 'user')
    list_display = ('user', 'entry', 'points',)
    
