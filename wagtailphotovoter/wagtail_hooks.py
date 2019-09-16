from wagtail.core.signals import page_published
from .models import Competition
from django.contrib.auth.models import Group

def receiver(sender, **kwargs):
    instance = kwargs['instance']
    # Get voting group_id, it will automatically create the new group
    _ = instance.voting_group_id()

page_published.connect(receiver, sender=Competition)