# Generated by Django 5.1.4 on 2024-12-26 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_configitemvalue_unique_item_per_environment'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdapterConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cls', models.CharField(help_text='Dotted path of adapter class', max_length=255)),
                ('conifg', models.JSONField()),
            ],
        ),
    ]
