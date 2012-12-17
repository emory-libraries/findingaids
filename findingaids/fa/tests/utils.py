# file findingaids/fa/tests/utils.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import datetime
from os import path
import re
from time import sleep
from types import ListType
from lxml import etree
from mock import patch
import unittest
from urllib import quote as urlquote

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpRequest
from django.template import RequestContext, Template
from django.test import TestCase as DjangoTestCase


from eulexistdb.db import ExistDB, ExistDBException
from eulexistdb.testutil import TestCase
from eulxml.xmlmap import load_xmlobject_from_file, \
    load_xmlobject_from_string, XmlObject
from eulxml.xmlmap.eadmap import EAD_NAMESPACE

from findingaids.fa.models import FindingAid, Series, Series2, Series3, \
    LocalComponent, Deleted, EadRepository
from findingaids.fa.views import _series_url, _subseries_links, _series_anchor
from datetime import datetime
from os import path

# from django.http import Http404, HttpRequest
# from django.test import TestCase as DjangoTestCase

# from eulexistdb.testutil import TestCase
# from eulxml.xmlmap.eadmap import EAD_NAMESPACE
# from eulexistdb.db import ExistDB, ExistDBException

from findingaids.fa.forms import boolean_to_upper, AdvancedSearchForm
from findingaids.fa.templatetags.ead import format_ead
from findingaids.fa.utils import pages_to_show, ead_lastmodified, ead_etag, \
    collection_lastmodified, exist_datetime_with_timezone, alpha_pagelabels


## unit tests for utility methods, custom template tags, etc

exist_fixture_path = path.join(path.dirname(path.abspath(__file__)), 'fixtures')
exist_index_path = path.join(path.dirname(path.abspath(__file__)), '..', '..', 'exist_index.xconf')


class UtilsTest(TestCase):
    exist_fixtures = {'files': [
            path.join(exist_fixture_path, 'abbey244.xml'),
    ]}

    def test_pages_to_show(self):
        paginator = Paginator(range(300), 10)
        # range of pages at the beginning
        pages = pages_to_show(paginator, 1)
        self.assertEqual(7, len(pages), "show pages returns 7 items for first page")
        self.assert_(1 in pages, "show pages includes 1 for first page")
        self.assert_(6 in pages, "show pages includes 6 for first page")

        pages = pages_to_show(paginator, 2)
        self.assert_(1 in pages, "show pages for page 2 includes 1")
        self.assert_(2 in pages, "show pages for page 2 includes 2")
        self.assert_(3 in pages, "show pages for page 2 includes 3")

        # range of pages in the middle
        pages = pages_to_show(paginator, 15)
        self.assertEqual(7, len(pages), "show pages returns 7 items for middle of page result")
        self.assert_(15 in pages, "show pages includes current page for middle of page result")
        self.assert_(12 in pages,
            "show pages includes third page before current page for middle of page result")
        self.assert_(18 in pages,
            "show pages includes third page after current page for middle of page result")

        # range of pages at the end
        pages = pages_to_show(paginator, 30)
        self.assertEqual(7, len(pages), "show pages returns 7 items for last page")
        self.assert_(30 in pages, "show pages includes last page for last page of results")
        self.assert_(24 in pages,
            "show pages includes 6 pages before last page for last page of results")

    def test_alpha_pagelabels(self):
        # create minimal object and list of items to generate labels for
        class item:
            def __init__(self, title):
                self.title = title
        titles = ['Abigail', 'Abner', 'Adam', 'Allen', 'Amy', 'Andy', 'Annabelle', 'Anne', 'Azad']
        items = [item(t) for t in titles]
        paginator = Paginator(items, per_page=2)
        labels = alpha_pagelabels(paginator, items, label_attribute='title')
        self.assertEqual('Abi - Abn', labels[1])
        self.assertEqual('Ad - Al', labels[2])
        self.assertEqual('Am - And', labels[3])
        self.assertEqual('Anna - Anne', labels[4])
        self.assertEqual('Az', labels[5])

    def test_ead_lastmodified(self):
        modified = ead_lastmodified('rqst', 'abbey244')
        self.assert_(isinstance(modified, datetime),
                     "ead_lastmodified should return a datetime object")
        date_format = '%Y-%m-%d'
        expected = datetime.now().strftime(date_format)
        value = modified.strftime(date_format)
        self.assertEqual(expected, value,
                     'ead lastmodified should be today, expected %s, got %s' % (expected, value))

        # invalid eadid
        self.assertRaises(Http404, ead_lastmodified, 'rqst', 'bogusid')

        db = ExistDB()
        # preview document - load fixture to preview collection
        fullpath = path.join(exist_fixture_path, 'raoul548.xml')
        db.load(open(fullpath, 'r'), settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml',
                overwrite=True)
        preview_modified = ead_lastmodified('rqst', 'raoul548', preview=True)
        self.assert_(isinstance(preview_modified, datetime),
                     "ead_lastmodified should return a datetime object")
        # clean up
        db.removeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml')

    def test_ead_etag(self):
        checksum = ead_etag('rqst', 'abbey244')
        self.assert_(re.match('[0-9a-f]{40}$', checksum),
                     'ead etag should be 40-character hex checksum, got %s' % checksum)
        # invalid eadid
        self.assertRaises(Http404, ead_etag, 'rqst', 'bogusid')

    def test_collection_lastmodified(self):
        modified = collection_lastmodified('rqst')
        self.assert_(isinstance(modified, datetime),
                     "collection_lastmodified should return a datetime object")

        # should equal last modified of abbey244 (last document loaded)
        fa = FindingAid.objects.only('last_modified').get(eadid='abbey244')
        self.assertEqual(exist_datetime_with_timezone(fa.last_modified), modified,
            'collection last modified should be datetime of most recently modified document in collection')

        # delete something after eXist document last-modified
        sleep(1)  # ensure deleted record is picked up as most recent
        Deleted(eadid='eadid', title='test deleted record', date=datetime.now()).save()
        record = Deleted.objects.get(eadid='eadid')     # retrieve datetime from DB
        modified = collection_lastmodified('rqst')
        #NOTE: THIS TEST DEPENDS ON THE LOCAL MACHINE TIME BEING SET CORRECTLY
        self.assertEqual(exist_datetime_with_timezone(record.date), modified,
            'collection last modified should be datetime of most recently deleted document in collection')

        # last-modified should not cause an error when there are no documents in eXist
        # - temporarily change collection so no documents will be found
        real_collection = settings.EXISTDB_ROOT_COLLECTION
        settings.EXISTDB_ROOT_COLLECTION = '/db/missing'
        # no exist data, but deleted record - should not cause any errors
        modified = collection_lastmodified('rqst')
        self.assertEqual(exist_datetime_with_timezone(record.date), modified,
            'collection last-modified should return most recently deleted document when no data is in eXist')
        # no exist data, no deleted records
        record = Deleted.objects.get(eadid='eadid')     # retrieve datetime from DB
        record.delete()
        modified = collection_lastmodified('rqst')
        self.assertEqual(None, modified,
            'collection last-modified should return None when no data is in eXist or deleted')

        settings.EXISTDB_ROOT_COLLECTION = real_collection




class FormatEadTestCase(DjangoTestCase):
# test ead_format template tag explicitly
    ITALICS = """<titleproper xmlns="%s"><emph render="italic">Pitts v. Freeman</emph> school desegregation case files,
1969-1993</titleproper>""" % EAD_NAMESPACE
    BOLD = """<titleproper xmlns="%s"><emph render="bold">Pitts v. Freeman</emph> school desegregation case files,
1969-1993</titleproper>""" % EAD_NAMESPACE
    TITLE = """<abstract xmlns="%s">A submission for the magazine <title>The Smart Set</title> from
    Irish writer Oliver St. John Gogarty to author Ernest Augustus Boyd.</abstract>""" % EAD_NAMESPACE
    TITLE_EMPH = """<bibref xmlns="%s"><emph>Biographical source:</emph> "Shaw, George Bernard."
    <title>Contemporary Authors Online</title>, Gale, 2003</bibref>""" % EAD_NAMESPACE
    NESTED = """<abstract xmlns="%s">magazine <title>The <emph render="doublequote">Smart</emph> Set</title>...</abstract>""" % EAD_NAMESPACE
    NOTRANS = """<abstract xmlns="%s">magazine <title>The <bogus>Smart</bogus> Set</title>...</abstract>""" % EAD_NAMESPACE
    EXIST_MATCH = """<abstract xmlns="%s">Pitts v. <exist:match xmlns:exist="http://exist.sourceforge.net/NS/exist">Freeman</exist:match>
school desegregation case files</abstract>""" % EAD_NAMESPACE

    def setUp(self):
        self.content = XmlObject(etree.fromstring(self.ITALICS))    # place-holder node

    def test_italics(self):
        self.content.node = etree.fromstring(self.ITALICS)
        format = format_ead(self.content)
        self.assert_('<span class="ead-italic">Pitts v. Freeman</span> school desegregation' in format,
            "render italic converted correctly to span class ead-italic")

    def test_bold(self):
        self.content.node = etree.fromstring(self.BOLD)
        format = format_ead(self.content)
        self.assert_('<span class="ead-bold">Pitts v. Freeman</span> school desegregation' in format,
            "render bold converted correctly to span class ead-bold")

    def test_title(self):
        self.content.node = etree.fromstring(self.TITLE)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span> from' in format,
            "title tag converted correctly to span class ead-title")

    def test_title_emph(self):
        self.content.node = etree.fromstring(self.TITLE_EMPH)
        format = format_ead(self.content)
        self.assert_('<em>Biographical source:</em> "Shaw, George' in format,
            "emph tag rendered correctly in section with title")
        self.assert_('<span class="ead-title">Contemporary Authors Online</span>, Gale' in format,
            "title rendered correctly in sectino with emph tag")

    def test_nested(self):
        self.content.node = etree.fromstring(self.NESTED)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The "Smart" Set</span>...' in format,
            "nested format rendered correctly")

    def test_notrans(self):
        self.content.node = etree.fromstring(self.NOTRANS)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span>...' in format,
            "nested format rendered correctly")

    def test_exist_match(self):
        self.content.node = etree.fromstring(self.EXIST_MATCH)
        format = format_ead(self.content)
        self.assert_('Pitts v. <span class="exist-match">Freeman</span>'
            in format, 'exist:match tag converted to span for highlighting')


# test custom template tag ifurl
class IfUrlTestCase(DjangoTestCase):

    def test_ifurl(self):
        template = Template("{% load ifurl %}{% ifurl preview fa:full-findingaid fa:findingaid id=id %}")
        urlopts = {'id': 'docid'}
        context = RequestContext(HttpRequest(), {'preview': False, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:findingaid', kwargs=urlopts), url,
            "when condition is false, url is generated from second named url")

        context = RequestContext(HttpRequest(), {'preview': True, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:full-findingaid', kwargs=urlopts), url,
            "when condition is true, url is generated from first named url")

    def test_ifurl_asvar(self):
        # store ifurl output in a context variable and then render it for testing
        template = Template("{% load ifurl %}{% ifurl preview fa:full-findingaid fa:findingaid id=id as myurl %}{{ myurl }}")
        urlopts = {'id': 'docid'}
        context = RequestContext(HttpRequest(), {'preview': False, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:findingaid', kwargs=urlopts), url,
            "ifurl correctly stores resulting url in context when 'as' is specified")


class BooleanToUpperTest(TestCase):
    def test_boolean_to_upper(self):
        #should capitalize and or not when they are separate words and not parts of other words
        input = "not cookies and ice cream or oreos they make anderson sick and he eats nothing except hot dogs and hamburgers"
        expected = "NOT cookies AND ice cream OR oreos they make anderson sick AND he eats nothing except hot dogs AND hamburgers"

        result = boolean_to_upper(input)
        self.assertEqual(result, expected)


class AdvancedSearchFormTest(TestCase):
    # load fixtures so we have repo choices
    exist_fixtures = {'directory': exist_fixture_path}

    def test_validation(self):
        # no data - not valid
        form = AdvancedSearchForm(data={})
        self.assertFalse(form.is_valid(),
            'advanced search form is not valid when no fields are specified')
        self.assertTrue(form.non_field_errors(),
            'a non-field error is displayed when no search terms are entered')
        # any one field - valid
        form = AdvancedSearchForm(data={'keywords': 'foo'})
        self.assertTrue(form.is_valid(),
            'advanced search form is valid when only keywords are specified')
        form = AdvancedSearchForm(data={'subject': 'bar'})
        self.assertTrue(form.is_valid(),
            'advanced search form is valid when only subject is specified')
        # FIXME: this could break due to caching when testing & running a dev site at the same time
        # adjust the test to clear the cache or use a separate cache for tests

        # grab a valid choice from the current options in the form:
        repo = form.fields['repository'].choices[0][0]  # id value of first option tuple
        form = AdvancedSearchForm(data={'repository': repo})
        self.assertTrue(form.is_valid(),
            'advanced search form is valid when only repository is specified')
