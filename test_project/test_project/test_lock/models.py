from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=24)

    def __unicode__(self):
        return self.name


class Book(models.Model):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=24)

    def __unicode__(self):
        return self.title