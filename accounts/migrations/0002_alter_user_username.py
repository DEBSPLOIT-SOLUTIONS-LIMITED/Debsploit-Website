# Generated by Django 5.2.2 on 2025-06-09 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, help_text='Optional. Will be generated automatically if left blank.', max_length=150, null=True, unique=True),
        ),
    ]
