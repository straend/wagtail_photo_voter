# Generated by Django 3.0.3 on 2020-03-03 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailphotovoter', '0002_auto_20200215_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='votes',
            name='comments',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
