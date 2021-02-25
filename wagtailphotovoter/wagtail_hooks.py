from wagtail.core.signals import page_published
from .models import Competition
from django.contrib.auth.models import Group
from wagtail.core.models import Collection

def receiver(sender, **kwargs):
    instance = kwargs['instance']
    # Get voting group_id, it will automatically create the new group
    _ = instance.voting_group_id()
    
    # Create a collection
    if Collection.objects.filter(name=instance.title).count() == 0:
        root_coll = Collection.get_first_root_node()
        root_coll.add_child(name=instance.title)
        root_coll.save()
    

page_published.connect(receiver, sender=Competition)