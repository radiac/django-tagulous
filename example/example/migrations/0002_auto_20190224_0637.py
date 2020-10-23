# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("example", "0001_initial")]

    atomic = False

    operations = [
        migrations.RenameModel(
            old_name="_Tagulous_Person_hobbies", new_name="Tagulous_Person_hobbies"
        ),
        migrations.RenameModel(
            old_name="_Tagulous_Person_title", new_name="Tagulous_Person_title"
        ),
    ]
