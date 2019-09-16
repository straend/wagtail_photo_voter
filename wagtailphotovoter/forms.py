from django import forms

class ImageForm(forms.Form):
    title = forms.CharField(max_length=128)
    location = forms.CharField(max_length=128)
    gear = forms.CharField(max_length=128)
    photo = forms.ImageField()

class AuthorForm(forms.Form):
    name = forms.CharField(max_length=128)
    email = forms.EmailField()

class PhotosFormset(forms.BaseFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields['name'] = forms.CharField(max_length=128)
        form.fields['email'] = forms.EmailField()
        form.fields['permission'] = forms.BooleanField()    