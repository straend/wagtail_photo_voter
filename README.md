# Wagtail-photo-voter

A Wagtail module for creating Photo competitions with voting.

## How to install

Install using pip:

```
pip install wagtail-photo-voter
```

Also needs ExifTool from https://exiftool.org/install.html installed

### Settings

In your settings file, add `wagtailphotovoter` and `wagtail.contrib.routable_page`  to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'wagtail.contrib.routable_page',
    'wagtailphotovoter',
    # ...
]
```

## How to use

### The basics

To add a competition create a new page of typ `Competition` enter title and rules (shown on submission page). You can enter dates for when submissions are allowed (if empty always allowed) and voting dates (empty, always allowed).
 
Templates are extending `base.html` which should have blocks for `content` `extra_css` `extra_js`. 
 
And Bootstrap, and jQuery loaded (for example via `django-bootstrap4`)
 
You can modify the point-system with commasepareted values and `allow same points`.
0 points can always be given to any entry.
 
Voting is allowed for users in the group with name `competition-id-slug` and available at: `competition-page/vote` results available at `competition-page/result`.
