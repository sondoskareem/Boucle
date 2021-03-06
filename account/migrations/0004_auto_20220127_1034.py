# Generated by Django 3.2.8 on 2022-01-27 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_remove_user_address2'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='company_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='company_website',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
