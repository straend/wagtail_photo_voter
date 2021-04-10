from django.db import models
from django.db.models import F

from django.conf import settings
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login, logout_then_login
from django.utils.decorators import method_decorator

from django.contrib import messages
from django.forms.formsets import formset_factory
from django.forms import Form

from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Sum

from wagtail.core.models import Page, Collection
from wagtail.core.fields import RichTextField

from wagtail.images.models import AbstractImage, Image, AbstractRendition
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, FieldRowPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from pathlib import Path
import json
import csv
from .forms import AuthorForm, ImageForm

from simple_history.models import HistoricalRecords
from exiffield.fields import ExifField
from exiffield.getters import get_datetaken

def get_path_for_entry(instance, filename):
    ext = filename.split('.')[-1]
    p = Path('competition') / "{}".format(instance.competition.slug)
    x = EntryImage.objects.all().count()+1
    
    f = p/"{}.{}".format(x, ext)
    while f.is_file():
        x+=1
        f = p/"{}.{}".format(x, ext)
    
    return "{}".format(f)

def check_dates(start, end):
    '''
    returns a tuple, between, in-the-future
    '''
    now = timezone.now()
    if start is not None and start > now:
        return False, True
    if end is not None and end < now:
        return False, False

    return True, False


class Competition(RoutablePageMixin, Page):
    rules = RichTextField()
    allowed_points = models.CharField(max_length=128, default="0,1,2,3,4,5,6,7,8,9,10")
    allow_same_points = models.BooleanField(default=False, help_text='Not working, don\'t enable')

    entries_per_person = models.PositiveIntegerField(default=2)
    entries_in_rating = models.PositiveIntegerField(default=1)
    
    submission_start = models.DateTimeField(blank=True, null=True)
    submission_end = models.DateTimeField(blank=True, null=True)
        
    voting_start = models.DateTimeField(blank=True, null=True)
    voting_end = models.DateTimeField(blank=True, null=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('rules'),
        FieldPanel('allowed_points'),
        FieldPanel('allow_same_points'),
        FieldRowPanel([FieldPanel('entries_per_person'), FieldPanel('entries_in_rating')]),
        FieldRowPanel([FieldPanel('submission_start'), FieldPanel('submission_end')]),
        FieldRowPanel([FieldPanel('voting_start'), FieldPanel('voting_end')]),
    ]

    def voting_group_id(self):
        group,_ = Group.objects.get_or_create(name="competition-{}-{}".format(self.id, self.slug))
        return group.id

    def user_has_vote_access(self, user):
        if user is None or isinstance(user, AnonymousUser):
            return False
        try:
            x = user.groups.get(id=self.voting_group_id())
            return True
        except:
            return False

    @route(r'^vote/v/(\d+)/comment/$')
    @method_decorator(login_required)
    def make_comment(self, request, entry_id=None):
        if not self.user_has_vote_access(request.user):
            return logout_then_login(request)
        
        votes =  get_object_or_404(Votes, entry_id=entry_id)
        comments = request.POST.get('comments')
        votes.comments = comments
        votes.save()
        
        print(votes, comments)
        
        return JsonResponse({'comment': votes.comments})
        
    
    @route(r'^vote/v/(\d+)/$')
    @route(r'^vote/v/$')
    @method_decorator(login_required)
    def my_votes_for(self, request, entry_id=None):
        if not self.user_has_vote_access(request.user):
            return logout_then_login(request)
        
        if entry_id is None:
            votes = Votes.objects.filter(entry__competition=self, user=request.user)
            res = []
            for x in votes:
                res.append({'id': x.entry.id, 'points': x.points, 'name': x.entry.title, 'comments': x.comments} )
            return JsonResponse(res, safe=False)
        else:
            entry = get_object_or_404(EntryImage, id=entry_id)

            votes, _ = Votes.objects.get_or_create(entry=entry, user=request.user)
            if request.method == 'POST':
                now = timezone.now()
                between, _ = check_dates(
                    entry.competition.voting_start, 
                    entry.competition.voting_end
                )
                if not between:
                    return HttpResponseForbidden()
                
                points = request.POST.get('points')
                
                # See if voted points are allowed
                if int(points) > 0 and not entry.competition.allow_same_points:
                    v = Votes.objects.filter(entry__competition=self, user=request.user, points=points)
                    if v.count() > 0:
                        return HttpResponseForbidden()
                
                votes.points = points
                votes.save()
            return JsonResponse({'id': entry_id, 'points': votes.points})
    
    
    @route(r'^vote/$', name='vote')
    @method_decorator(login_required)
    def show_vote_form(self, request):
        if not self.user_has_vote_access(request.user):
            messages.error(request, 'You lack permissions for this Competition')
            
            return logout_then_login(request, login_url="{}vote".format(self.url))

        context = {}
        between, future = check_dates(
            self.voting_start, 
            self.voting_end
        )
        if not between:
            if future:
                messages.error(request, 'Voting starts {}'.format(self.voting_start))
            else:
                messages.error(request, 'Voting ended {}'.format(self.voting_end))
        else:
            context['entries'] = self.entries.all()
            context['points'] = self.allowed_points.split(",")
        
        context['page'] = self
        return render(
            request, 
            'wagtailphotovoter/vote.html', 
            context
        )   
    
    @route(r'^choice/$', name='choice')
    @method_decorator(login_required)
    def show_choice_form(self, request):
        if not self.user_has_vote_access(request.user):
            messages.error(request, 'You lack permissions for this Competition')
            
            return logout_then_login(request, login_url="{}vote".format(self.url))

        context = {}
        context['page'] = self

        between, future = check_dates(
            self.voting_start, 
            self.voting_end
        )

        if not between:
            if future:
                messages.error(request, 'Voting starts {}'.format(self.voting_start))
            else:
                messages.error(request, 'Voting ended {}'.format(self.voting_end))
             
        elif request.method == 'POST':
            for user_id in request.POST:
                if user_id.startswith("user_"):
                    u_id = user_id.split("_")[1]
                    i_id = request.POST.get(user_id)
                    entry = EntryImage.objects.get(pk=i_id)
                    iv, created = ImageVote.objects.get_or_create(user=request.user, entry=entry)
                    # Find and delete other
                    ImageVote.objects.filter(entry__user=entry.user).exclude(entry=entry).delete()
            return JsonResponse({"OK": "fo"})
        else:
            votes = {}
            for e in ImageVote.objects.filter(user=request.user).all():
                votes[e.entry.user.id] = e.entry.id

            context['users'] = EntryUser.objects.filter(entries__competition=self).distinct()
            context['votes'] = votes
            print(votes)

        return render(
            request, 
            'wagtailphotovoter/image_choice.html', 
            context
        )

    @route(r'^result/$')
    @method_decorator(login_required)
    def show_result(self, request):
        if not self.user_has_vote_access(request.user):
            return logout_then_login(request, login_url="{}result".format(self.url))

        context = {}
        q = self.entries.annotate(total_points=Sum('votes__points')).order_by(F('total_points').desc(nulls_last=True)).all()
        context['entries'] = q
        #print(context['entries'])
        context['page'] = self
        return render(
            request, 
            'wagtailphotovoter/result.html', 
            context
        )   
    
    @route(r'^result/csv/$')
    @method_decorator(login_required)
    def some_view(self, request):
        if not self.user_has_vote_access(request.user):
            return logout_then_login(request, login_url="{}result/csv".format(self.url))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}-{}.csv"'.format(
            self.id, self.slug
        )
        writer = csv.writer(response)
        writer.writerow(['link', 'points', 'title', 'author', 'email', 'location', 'gear', 'comments'])
        q = self.entries.annotate(total_points=Sum('votes__points')).order_by(F('total_points').desc(nulls_last=True)).all()
        for e in q:
            comments = ""
            for v in e.votes.all():
                if v.comments is not None:
                    comments += "{}: {}\n".format(v.user, v.comments)
            writer.writerow(["{}{}".format(
                settings.BASE_URL, e.link)
                , e.points, e.title, e.user.name, e.user.email, e.location, e.gear, comments
            ])

        return response
    
    @route(r'^$')
    def show_add_form(self, request):
        context = {
            'page': self
        }

        between, future = check_dates(
            self.submission_start, 
            self.submission_end
        )
        
        if not between:
            if future:
                messages.error(request, 'Submissions opens {}'.format(self.submission_start))
            else:
                messages.error(request, 'Sumbissions closed {}'.format(self.submission_end))
            return render(
                request, 
                'wagtailphotovoter/add.html', 
                context
            )
        
        imageFormSet = formset_factory(ImageForm,extra=self.entries_per_person, max_num=self.entries_per_person, min_num=1)
        
        if request.method == 'POST':
            iform = imageFormSet(request.POST, request.FILES)
            aform = AuthorForm(request.POST, request.FILES)
            if iform.is_valid() and aform.is_valid():
                name = aform.cleaned_data.get('name')
                email = aform.cleaned_data.get('email')
                user, created = EntryUser.objects.get_or_create(email=email)
                user.name = name
                user.save()
                # get collection
                c = Collection.objects.filter(name=self.title).first()
                
                for i in iform:
                    gear = i.cleaned_data.get('gear')
                    title = i.cleaned_data.get('title')
                    location = i.cleaned_data.get('location')
                    # Skip if not 
                    if gear is None and title is None and location is None:
                        continue
                    img = EntryImage.objects.create(
                        file=i.cleaned_data.get('photo'),
                        title=title,
                        competition = self,
                        gear = gear,
                        location = location,
                        user=user,
                        collection=c,
                    )
                    messages.success(request, "Your entry '{}' has been submitted".format(title))
                # Both forms valid, so redirect to avoid multiple submissions of same
                return HttpResponseRedirect(self.get_url())
           
        else:
            iform = imageFormSet()
            aform = AuthorForm()
        
        context['author'] = aform
        context['images'] = iform
        return render(
            request, 
            'wagtailphotovoter/add.html', 
            context
        )

class ImageVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_votes', blank=True, null=True)
    entry = models.ForeignKey('EntryImage', on_delete=models.CASCADE, related_name='image_votes', blank=True, null=True)
    

class Votes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voters', blank=True, null=True)
    entry = models.ForeignKey('EntryImage', on_delete=models.CASCADE, related_name='votes', blank=True, null=True)
    points = models.PositiveSmallIntegerField(default=0)
    first = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    comments = models.CharField(max_length=300, blank=True, null=True)
    
    history = HistoricalRecords()
    class Meta:
        unique_together = [['user', 'entry']]

    def __str__(self):
        return "{}, {} points, {} in {} [{}]".format(self.user, self.points, self.entry, self.entry.competition, self.comments)

class EntryUser(models.Model):
    name = models.CharField(max_length=256)
    email = models.EmailField()
    
    def __str__(self):
        return "{}: {}".format(self.name, self.email)

class EntryImage(AbstractImage):
    competition = models.ForeignKey(
        Competition, 
        on_delete=models.CASCADE,
        related_name='entries',
        null=True
    )
    title = models.CharField(max_length=256)
    gear = models.CharField(max_length=256)
    location = models.CharField(max_length=256)
    submitted = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(EntryUser, on_delete=models.CASCADE, related_name='entries', null=True)
    vote_count = models.PositiveIntegerField(default=0)

    taken = models.DateTimeField(blank=True, null=True, editable=False)
    exif = ExifField(
        source='file',
        denormalized_fields={
            'taken': get_datetaken,
        },
    )
    
    @property
    def my_vote_count(self):
        return self.image_votes.count()

    def get_my_path(self):
        return Path('competition') / "{}".format(self.competition.id)

    def get_upload_to(instance, filename):
        ext = filename.split('.')[-1]
        x = EntryImage.objects.all().count()+1
        p = instance.get_my_path()

        f = p/"{}-{}.{}".format(x, slugify(instance.title), ext)
        while f.is_file():
            x+=1
            f = p/"{}-{}.{}".format(x, slugify(instance.title), ext)
        return "{}".format(f)
    
    @property
    def points(self):
        return self.votes.aggregate(Sum('points'))['points__sum']

    @property
    def link(self):
        p = self.get_my_path() / self.filename
        return "{}/{}".format("/media", p)

class EntryImageRendition(AbstractRendition):
    image = models.ForeignKey(EntryImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )
