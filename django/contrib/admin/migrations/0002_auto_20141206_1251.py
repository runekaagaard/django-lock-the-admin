# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.TextField(verbose_name='Object id')),
                ('version', models.IntegerField(default=0, verbose_name='Version Number')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Lock',
                'verbose_name_plural': 'Locks',
            },
            bases=None,
        ),
        migrations.AlterUniqueTogether(
            name='lock',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
