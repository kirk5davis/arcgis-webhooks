# Generated by Django 4.0.1 on 2022-04-08 18:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webhook_listener', '0003_jobkind_job'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Job',
            new_name='Task',
        ),
        migrations.RenameModel(
            old_name='JobKind',
            new_name='TaskKind',
        ),
    ]