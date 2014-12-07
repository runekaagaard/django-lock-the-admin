from __future__ import unicode_literals

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name + str(self.pk)

class Book(models.Model):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=50)

    def __unicode__(self):
        return self.title + str(self.pk)


class Novel(models.Model):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=50)

    def __unicode__(self):
        return self.title + str(self.pk)
