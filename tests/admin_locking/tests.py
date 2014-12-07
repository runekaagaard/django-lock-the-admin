from __future__ import unicode_literals

from django.test import TestCase, override_settings

# Local test models.
from .models import Author, Book, Novel


@override_settings(
    PASSWORD_HASHERS=('django.contrib.auth.hashers.SHA1PasswordHasher', ),
    ROOT_URLCONF="admin_locking.urls",
)
class TestLocking(TestCase):
    fixtures = ['admin-views-users.xml']

    def setUp(self):
        result = self.client.login(username='super', password='secret')
        self.assertEqual(result, True)

        self.author_add_url = '/admin/admin_locking/author/add/'
        self.author_url = '/admin/admin_locking/author/{}/'
        self.author_list_url = '/admin/admin_locking/author/'
        self.error1 = 'An item on this page have been updated by another user while you were editing it.'
        self.error2 = '5 items on this page have been updated by another user while you were editing it.'

    def tearDown(self):
        self.client.logout()

    def test_main_form(self):
        data = {
            '_save': 'Save',
            'name': 'Homer',

            'book_set-TOTAL_FORMS': 1,
            'book_set-INITIAL_FORMS': 0,
            'book_set-MIN_NUM_FORMS"': 0,

            'novel_set-TOTAL_FORMS': 1,
            'novel_set-INITIAL_FORMS': 0,
            'novel_set-MAX_NUM_FORMS': 0,
        }

        # Add author.
        response = self.client.post(self.author_add_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEqual(Author.objects.count(), 1)
        author = Author.objects.all()[0]
        author_url = self.author_url.format(author.pk)

        # Post without lock version.
        try:
            self.client.post(author_url, data)
        except Exception as e:
            f = e
        self.assertEqual(f.message,
                         'Locking data is missing or has been tampered with.')

        # Post with lock version.
        data.update({'lock_version': 0, 'name': 'Moe'})
        response = self.client.post(author_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEqual(Author.objects.all()[0].name, 'Moe')

        # Post with same lock version.
        data.update({'name': 'Bart'})
        response = self.client.post(author_url, data)
        self.assertContains(response, self.error1, 1)
        self.assertContains(response,
            '<a href="/admin/admin_locking/author/{0}/">Bart{0}</a>'.format(
                author.pk), 1)
        self.assertEqual(Author.objects.all()[0].name, 'Moe')

        # Post with new lock version.
        data['lock_version'] = 1
        response = self.client.post(author_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEqual(Author.objects.all()[0].name, 'Bart')

    def test_inlines(self):
        data = {
            '_save': 'Save',
            'name': 'Homer',

            'book_set-INITIAL_FORMS': 0,
            'book_set-TOTAL_FORMS': 3,
            'book_set-MAX_NUM_FORMS': 0,
            'book_set-0-title': 'bookA',
            'book_set-1-title': 'bookB',
            'book_set-2-title': 'bookC',

            'novel_set-INITIAL_FORMS': 0,
            'novel_set-TOTAL_FORMS': 3,
            'novel_set-MAX_NUM_FORMS': 0,
            'novel_set-0-title': 'novelA',
            'novel_set-1-title': 'novelB',
            'novel_set-2-title': 'novelC',
        }

        # Add author.
        response = self.client.post(self.author_add_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEquals((Book.objects.count(), Novel.objects.count()),
                          (3, 3))
        author = Author.objects.all()[0]
        author_url = self.author_url.format(author.pk)
        book_pks = list(Book.objects.values_list('pk', flat=True))
        novel_pks = list(Novel.objects.values_list('pk', flat=True))
        self.assertEqual(Book.objects.get(pk=book_pks[0]).title, 'bookA')

        # Post without lock versions.
        data.update({
            'lock_version': 0,
            'book_set-INITIAL_FORMS': 3,
            'book_set-TOTAL_FORMS': 6,
            'book_set-0-title': 'bookAA',
            'book_set-0-id': book_pks[0],
            'book_set-0-author': 1,
            'book_set-1-title': 'bookB',
            'book_set-1-id': book_pks[1],
            'book_set-1-author': 1,
            'book_set-2-title': 'bookCC',
            'book_set-2-id': book_pks[2],
            'book_set-2-author': 1,

            'novel_set-INITIAL_FORMS': 3,
            'novel_set-TOTAL_FORMS': 6,
            'novel_set-0-title': 'novelAA',
            'novel_set-0-id': novel_pks[0],
            'novel_set-0-author': 1,
            'novel_set-1-title': 'novelB',
            'novel_set-1-id': novel_pks[1],
            'novel_set-1-author': 1,
            'novel_set-2-title': 'novelCC',
            'novel_set-2-id': novel_pks[2],
            'novel_set-2-author': 1,
        })
        try:
            self.client.post(author_url, data)
        except Exception as e:
            f = e
        self.assertEqual(f.message,
                         'Locking data is missing or has been tampered with.')
        self.assertEqual(Book.objects.get(pk=book_pks[0]).title, 'bookA')

        # Post with lock versions.
        data.update({
            'book_set-0-lock_version': 0,
            'book_set-1-lock_version': 0,
            'book_set-2-lock_version': 0,
            'novel_set-0-lock_version': 0,
            'novel_set-1-lock_version': 0,
            'novel_set-2-lock_version': 0,
        })
        response = self.client.post(author_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEqual(Book.objects.get(pk=book_pks[0]).title, 'bookAA')

        # Post with same lock versions.
        data.update({'book_set-0-title': 'bookAAA'})
        response = self.client.post(author_url, data)
        self.assertEqual(Book.objects.get(pk=book_pks[0]).title, 'bookAA')
        self.assertContains(response, self.error2, 1)
        self.assertContains(response,
            '<a href="/admin/admin_locking/author/{0}/">Homer{0}</a>'.format(
                author.pk), 1)
        self.assertContains(response,
            '<a href="/admin/admin_locking/book/{0}/">bookAAA{0}</a>'.format(
                book_pks[0]), 1)
        self.assertNotContains(response,
            '<a href="/admin/admin_locking/book/{0}/">bookB{0}</a>'.format(
                book_pks[1]))
        self.assertContains(response,
            '<a href="/admin/admin_locking/book/{0}/">bookCC{0}</a>'.format(
                book_pks[2]), 1)
        self.assertContains(response, 'Novel: novelAA{}'.format(novel_pks[0]), 1)
        self.assertNotContains(response, 'Novel: novelB{}'.format(novel_pks[1]))
        self.assertContains(response, 'Novel: novelCC{}'.format(novel_pks[2]), 1)

        # Post with new lock versions.
        data.update({
            'lock_version': 1,
            'book_set-0-lock_version': 1,
            'book_set-1-lock_version': 0,
            'book_set-2-lock_version': 1,
            'novel_set-0-lock_version': 1,
            'novel_set-1-lock_version': 0,
            'novel_set-2-lock_version': 1,
        })
        response = self.client.post(author_url, data)
        self.assertRedirects(response, self.author_list_url)
        self.assertEqual(Book.objects.get(pk=book_pks[0]).title, 'bookAAA')