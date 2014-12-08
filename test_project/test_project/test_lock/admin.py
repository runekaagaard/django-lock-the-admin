from django.contrib import admin

from .models import Author, Book

from django.apps import AppConfig


class TestLockConfig(AppConfig):
    name = 'test_lock'
    verbose_name = "Test Lock"


class BookAdmin(admin.ModelAdmin):
    pass


class BookInline(admin.TabularInline):
    model = Book
    fields = ('title', )


class AuthorAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ('name', )}),)
    list_display = ('id', 'name')
    list_editable = ('name', )
    inlines = (BookInline, )


admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)