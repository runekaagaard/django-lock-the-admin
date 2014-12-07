from django.contrib import admin
from .models import Author, Book, Novel

site = admin.AdminSite(name="admin")


class BookInline(admin.TabularInline):
    model = Book


class NovelInline(admin.StackedInline):
    model = Novel


class BookAdmin(admin.ModelAdmin):
    pass


class AuthorAdmin(admin.ModelAdmin):
    inlines = [BookInline, NovelInline]

site.register(Author, AuthorAdmin)
site.register(Book, BookAdmin)
