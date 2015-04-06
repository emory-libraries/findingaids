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
from lxml import etree
from mock import patch
import rdflib

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpRequest
from django.template import RequestContext, Template, Context, loader
from django.test import TestCase as DjangoTestCase

from eulexistdb.db import ExistDB
from eulexistdb.testutil import TestCase
from eulxml.xmlmap import XmlObject, load_xmlobject_from_string
from eulxml.xmlmap.eadmap import EAD_NAMESPACE

from findingaids.fa.models import FindingAid, Deleted, Series, \
    title_rdf_identifier
from findingaids.fa.forms import boolean_to_upper, AdvancedSearchForm
from findingaids.fa.templatetags.ead import format_ead, XLINK_NAMESPACE
from findingaids.fa.templatetags.ark_pid import ark_pid
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
        # NOTE: THIS TEST DEPENDS ON THE LOCAL MACHINE TIME BEING SET CORRECTLY
        self.assertEqual(exist_datetime_with_timezone(record.date), modified,
            'collection last modified should be datetime of most recently deleted document in collection')

        # last-modified should not cause an error when there are no documents in eXist
        # - temporarily change collection so no documents will be found
        with patch.object(settings, 'EXISTDB_ROOT_COLLECTION', new='/db/missing'):
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
    TITLE_QUOT = """<unittitle xmlns="%s"><title render="doublequote">Terminus</title></unittitle>""" % EAD_NAMESPACE
    # NOTE: multi-title mode is now only triggered when a persname with a role is present
    TITLE_MULTI = """<unittitle xmlns="%s" level="file"><persname role="dc:creator">Some Author</persname>: <title render="doublequote">Terminus</title>, <title render="doublequote">Saturday</title></unittitle>""" % EAD_NAMESPACE
    NESTED = """<abstract xmlns="%s">magazine <title>The <emph render="doublequote">Smart</emph> Set</title>...</abstract>""" % EAD_NAMESPACE
    NOTRANS = """<abstract xmlns="%s">magazine <title>The <bogus>Smart</bogus> Set</title>...</abstract>""" % EAD_NAMESPACE
    EXIST_MATCH = """<abstract xmlns="%s">Pitts v. <exist:match xmlns:exist="http://exist.sourceforge.net/NS/exist">Freeman</exist:match>
school desegregation case files</abstract>""" % EAD_NAMESPACE
    EXTREF = '''<p xmlns="%s" xmlns:xlink="%s">Belfast Group sheets may also be found in the
    <extref xlink:href="http://pid.emory.edu/ark:/25593/8zgst">Irish Literary Miscellany</extref>.</p>''' \
    % (EAD_NAMESPACE, XLINK_NAMESPACE)
    EXTREF_NOLINK = '''<p xmlns="%s">Belfast Group sheets may also be found in the
    <extref>Irish Literary Miscellany</extref>.</p>''' % EAD_NAMESPACE

    def setUp(self):
        self.content = XmlObject(etree.fromstring(self.ITALICS))    # place-holder node

    def test_italics(self):
        self.content.node = etree.fromstring(self.ITALICS)
        fmt = format_ead(self.content)
        self.assert_('<span class="ead-italic">Pitts v. Freeman</span> school desegregation' in fmt,
            "render italic converted correctly to span class ead-italic")

    def test_bold(self):
        self.content.node = etree.fromstring(self.BOLD)
        fmt = format_ead(self.content)
        self.assert_('<span class="ead-bold">Pitts v. Freeman</span> school desegregation' in fmt,
            "render bold converted correctly to span class ead-bold")

    def test_title(self):
        self.content.node = etree.fromstring(self.TITLE)
        fmt = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span> from' in fmt,
                     "title tag converted correctly to span class ead-title")

        # title variants
        # - doublequotes
        self.content.node = etree.fromstring(self.TITLE_QUOT)
        fmt = format_ead(self.content)
        self.assertEqual('"Terminus"', fmt)
        # - multiple
        self.content.node = etree.fromstring(self.TITLE_MULTI)
        fmt = format_ead(self.content)
        self.assertEqual('Some Author: "Terminus", "Saturday"', fmt)

        # - multiple titles + RDFa
        fmt = format_ead(self.content, rdfa=True)
        self.assertEqual('<span rel="dc:creator"><span typeof="schema:Person"><span property="schema:name">Some Author</span></span></span>: "<span inlist="inlist" property="dc:title">Terminus</span>", "<span inlist="inlist" property="dc:title">Saturday</span>"',
                         fmt)

    def test_title_emph(self):
        self.content.node = etree.fromstring(self.TITLE_EMPH)
        fmt = format_ead(self.content)
        self.assert_('<em>Biographical source:</em> "Shaw, George' in fmt,
            "emph tag rendered correctly in section with title")
        self.assert_('<span class="ead-title">Contemporary Authors Online</span>, Gale' in fmt,
            "title rendered correctly in sectino with emph tag")

    def test_nested(self):
        self.content.node = etree.fromstring(self.NESTED)
        fmt = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The "Smart" Set</span>...' in fmt,
            "nested format rendered correctly")

    def test_notrans(self):
        self.content.node = etree.fromstring(self.NOTRANS)
        fmt = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span>...' in fmt,
            "nested format rendered correctly")

    def test_exist_match(self):
        self.content.node = etree.fromstring(self.EXIST_MATCH)
        fmt = format_ead(self.content)
        self.assert_('Pitts v. <span class="exist-match">Freeman</span>'
            in fmt, 'exist:match tag converted to span for highlighting')

    def test_extref(self):
        self.content.node = etree.fromstring(self.EXTREF)
        fmt = format_ead(self.content)
        self.assert_('<a href="http://pid.emory.edu/ark:/25593/8zgst">Irish Literary Miscellany</a>'
            in fmt, 'extref tag converted to a href')

        self.content.node = etree.fromstring(self.EXTREF_NOLINK)
        fmt = format_ead(self.content)
        self.assert_('<a>Irish Literary Miscellany</a>'
            in fmt, 'formatter should not fail when extref has no href')

class RdfaTemplateTest(DjangoTestCase):
    # test RDFa output for file-level items

    # rdf namespaces for testing
    DC = rdflib.Namespace('http://purl.org/dc/terms/')
    BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
    SCHEMA_ORG = rdflib.Namespace('http://schema.org/')

    def setUp(self):
        self.item_tmpl = loader.get_template('fa/snippets/file_item.html')
        self.ctxt = Context({'DEFAULT_DAO_LINK_TEXT': 'Resource Available Online'})

    def _render_item_to_rdf(self, xmlstring):
        # convenience method for testing ead file component rdf output

        # load xml as an ead series item
        component = load_xmlobject_from_string(xmlstring, Series)
        # render with the file_item template used in findingaid display
        self.ctxt.update({'component': component})
        result = self.item_tmpl.render(self.ctxt)
        # parse as RDFa and return the resulting rdflib graph
        # - patch in namespaces before parsing as rdfa
        result = '<html xmlns:schema="%s" xmlns:bibo="%s">%s</html>' % \
            (self.SCHEMA_ORG, self.BIBO, result)
        g = rdflib.Graph()
        g.parse(data=result, format='rdfa')
        return g

    def test_bg_groupsheet(self):
        # sample belfast group sheet from simmons759
        bg_groupsheet = '''<c03 level="file" xmlns="%s" xmlns:xlink="%s">
            <did>
              <container type="box">63</container>
              <container type="folder">6</container>
              <unittitle>
                <corpname source="viaf" authfilenumber="123393054" role="schema:publisher">Belfast Group</corpname> Worksheet,
                <persname authfilenumber="39398205" role="dc:creator" source="viaf">Michael Longley</persname>:
                    <title render="doublequote">To the Poets</title>,
                    <title render="doublequote">Mountain Swim</title>,
                    <title render="doublequote">Gathering Mushrooms</title>
                </unittitle>
                <dao xlink:href="http://pid.emory.edu/ark:/25593/17m8g"/>
            </did>
        </c03>''' % (EAD_NAMESPACE, XLINK_NAMESPACE)

        g = self._render_item_to_rdf(bg_groupsheet)

        # there should be a manuscript in the output (blank node)
        ms_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Manuscript)))

        self.assert_(ms_triples, 'RDFa output should include an item with type manuscript')
        # first element of the first triple should be our manuscript node
        ms_node = ms_triples[0][0]
        # manuscript should be related to BG (right now uses schema.org/mentions, but could change)
        self.assert_(list(g.triples((ms_node, None, rdflib.URIRef('http://viaf.org/viaf/123393054')))),
            'manuscript should be related to belfast group')
        # manuscript should have an author
        self.assert_((ms_node, self.DC.creator, rdflib.URIRef('http://viaf.org/viaf/39398205')),
            'manuscript should have author as dc:creator')
        titles = list(g.triples((ms_node, self.DC.title, None)))
        # manuscript should have a title
        self.assert_(titles, 'manuscript should have a dc:title')
        # should actually be an RDF sequence
        # first triple, third term (subject) should be the title node
        title_node = titles[0][2]
        self.assert_(isinstance(title_node, rdflib.BNode),
            'multiple titles should be related via blank node for rdf list')
        # first title
        self.assertEqual(u'To the Poets', unicode(g.value(title_node, rdflib.RDF.first)),
            'first title should be part of rdf list')
        # rest of the list
        rest = g.value(title_node, rdflib.RDF.rest)
        # second title
        self.assertEqual(u'Mountain Swim', unicode(g.value(rest, rdflib.RDF.first)))
        # second rest of the list
        rest2 = g.value(rest, rdflib.RDF.rest)
        # third title
        self.assertEqual(u'Gathering Mushrooms', unicode(g.value(rest2, rdflib.RDF.first)))

    def test_book_title(self):
        # book title
        book_title = '''<c03 level="file" xmlns="%s">
            <did>
              <container type="box">63</container>
              <container type="folder">6</container>
              <unittitle>Various poems, <title type="poetry" source="isbn" authfilenumber="0882580159">The Forerunners: Black Poets in America</title>, 1981</unittitle>
             </did>
        </c03>''' % EAD_NAMESPACE
        g = self._render_item_to_rdf(book_title)

        # there should be a book in the output
        book_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Book)))

        self.assert_(book_triples, 'RDFa output should include an item with type bibo:Book')
        # first element of the first triple should be our book node
        book_node = book_triples[0][0]
        self.assertEqual(rdflib.URIRef('urn:ISBN:0882580159'), book_node,
            'book identifier should be an ISBN URN')
        self.assertEqual(u'The Forerunners: Black Poets in America',
            unicode(g.value(book_node, self.DC.title)),
            'book title should be set as dc:title')
        self.assertEqual(u'poetry', unicode(g.value(book_node, self.SCHEMA_ORG.genre)),
            'title type "poetry" should be set as schema.org genre')
        self.assertEqual(u'0882580159', unicode(g.value(book_node, self.SCHEMA_ORG.isbn)),
            'isbn authfilenumber should be set as schema.org/isbn')

        # OCLC book should be treated similarly
        oclc_title = '''<c02 xmlns="%s" level="file">
            <did>
              <container type="box">10</container>
              <container type="folder">24</container>
              <unittitle>
                <title type="scripts" source="OCLC" authfilenumber="434083314">Bayou Legend</title>
                , notes
                </unittitle>
            </did>
        </c02>''' % EAD_NAMESPACE
        g = self._render_item_to_rdf(oclc_title)
        # there should be a book in the output
        book_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Book)))

        self.assert_(book_triples, 'RDFa output should include an item with type bibo:Book')
        # first element of the first triple should be our book node
        book_node = book_triples[0][0]
        self.assertEqual(rdflib.URIRef('http://www.worldcat.org/oclc/434083314'), book_node,
            'book identifier should be a worldcat URI')
        self.assertEqual(u'Bayou Legend',
            unicode(g.value(book_node, self.DC.title)),
            'book title should be set as dc:title')
        self.assertEqual(u'scripts', unicode(g.value(book_node, self.SCHEMA_ORG.genre)),
            'title type "scripts" should be set as schema.org genre')

    def test_periodical_title(self):
        # test article in a periodical
        article_title = '''<c03 level="file" xmlns="%s">
            <did>
              <container type="box">63</container>
              <container type="folder">6</container>
              <unittitle><title type="article" render="doublequote">The Special Wonder of the Theater</title>,
                <title source="ISSN" authfilenumber="0043-0897">The Washingtonian</title>, February 1966</unittitle>
             </did>
        </c03>''' % EAD_NAMESPACE
        g = self._render_item_to_rdf(article_title)

        # there should be an article in the output
        article_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Article)))
        self.assert_(article_triples, 'RDFa output should include an item with type bibo:Article')
        # first element of the first triple should be the article node
        article_node = article_triples[0][0]
        self.assertEqual(u'The Special Wonder of the Theater',
            unicode(g.value(article_node, self.DC.title)),
            'article title should be set as dc:title')

        # article should be related to a periodical
        article_rels = list(g.triples((article_node, self.DC.isPartOf, None)))
        self.assert_(article_rels, 'article should be part of related periodical')
        # first triple, third term
        periodical_node = article_rels[0][2]
        self.assert_((periodical_node, rdflib.RDF.type, self.BIBO.Periodical) in g,
            'title with an ISSN should be a periodical')
        self.assertEqual(rdflib.URIRef('urn:ISSN:0043-0897'), periodical_node,
            'periodical identifier should be an ISSN URN')

        self.assertEqual(u'The Washingtonian', unicode(g.value(periodical_node, self.DC.title)),
            'periodical title should be set as dc:title')
        self.assertEqual(u'0043-0897', unicode(g.value(periodical_node, self.SCHEMA_ORG.issn)),
            'authfilenumber should be set as schema.org/issn')

    def test_related_titles(self):
        # if two titles, one with a type and the other with an id, first should
        # be part of the second
        # sample from hughes-edwards1145
        two_titles = '''<c01 level="file" xmlns="%s">
            <did>
                <container type="box">1</container>
                <container type="folder">6</container>
                <unittitle><title type="poetry" render="doublequote">Mother to Son</title>,
                        poem in
                        <title source="oclc" authfilenumber="10870853">The People's Voice</title>,
                        May 9, 1942
                </unittitle>
            </did>
        </c01>''' % EAD_NAMESPACE
        g = self._render_item_to_rdf(two_titles)

        # there should be a manuscript in the output
        ms_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Manuscript)))
        self.assert_(ms_triples, 'RDFa output should include an item with type bibo:Manuscript')
        # first element of the first triple should be the article node
        ms_node = ms_triples[0][0]
        self.assertEqual(u'Mother to Son',
            unicode(g.value(ms_node, self.DC.title)),
            'poem title should be set as dc:title')
        self.assertEqual(u'poetry',
            unicode(g.value(ms_node, self.SCHEMA_ORG.genre)),
            'genre should be set as poetry')
        book_uriref = rdflib.URIRef(title_rdf_identifier('oclc', '10870853'))
        self.assertTrue((ms_node, self.DC.isPartOf, book_uriref) in  g,
            'poem should be part of document with an id')
        self.assertTrue((book_uriref, rdflib.RDF.type, self.BIBO.Document),
            'document with id should be a bibo:Document')
        self.assert_(g.triples((None, self.SCHEMA_ORG.mentions, book_uriref)),
            'document with id should be mentioned by context (i.e. collection)')

    def test_extra_titles(self):
        # more than two titles in a unittitle
        # sample from hughes-edwards1145
        two_titles = '''<c01 level="file" xmlns="%s">
            <did>
                <container type="box">1</container>
                <container type="folder">7</container>
                <unittitle><title type="essays" render="doublequote">The Need for Heroes</title>,
                   essay in <title source="ISSN" authfilenumber=" 2169-1010">The Crisis</title>,
                   June 1941 [includes pages in which poems
                   <title type="poetry" render="doublequote">The Negro Speaks of Rivers</title>
                   and <title type="poetry" render="doublequote">NAACP</title> appear]
                </unittitle>
            </did>
        </c01>''' % EAD_NAMESPACE
        g = self._render_item_to_rdf(two_titles)

        # first two titles should work roughly as related title does above

        # there should be *three* manuscripts in the output
        ms_triples = list(g.triples((None, rdflib.RDF.type, self.BIBO.Manuscript)))
        self.assertEqual(3, len(ms_triples),
            'RDFa output should include three items with type bibo:Manuscript')

        # since rdf is unsorted, we have to find them by title
        ms_by_title = {}
        for ms in ms_triples:
            s, p, o = ms
            if unicode(g.value(s, self.DC.title)) == unicode('The Need for Heroes'):
                ms_by_title['Need'] = s
            if unicode(g.value(s, self.DC.title)) == unicode('The Negro Speaks of Rivers'):
                ms_by_title['Negro'] = s
            if unicode(g.value(s, self.DC.title)) == unicode('NAACP'):
                ms_by_title['NAACP'] = s

        self.assertEqual(u'essays',
            unicode(g.value(ms_by_title['Need'], self.SCHEMA_ORG.genre)),
            'essay title genre should be set as essays')
        self.assertEqual(u'poetry',
            unicode(g.value(ms_by_title['Negro'], self.SCHEMA_ORG.genre)),
            'poem title genre should be set as poetry')
        self.assertEqual(u'poetry',
            unicode(g.value(ms_by_title['NAACP'], self.SCHEMA_ORG.genre)),
            'poem title genre should be set as poetry')
        book_uriref = rdflib.URIRef(title_rdf_identifier('issn', '2169-1010'))

        # things that should be consistent for each of the typed titles
        for ms_node in ms_by_title.itervalues():
            # each item should be part of the book with title
            self.assertTrue((ms_node, self.DC.isPartOf, book_uriref) in  g,
                'item should be part of document with an id')
            # each item should be mentioned in context (i.e. collection)
            self.assert_(g.triples((None, self.SCHEMA_ORG.mentions, ms_node)),
                'item should be mentioned by context (i.e. collection)')

        self.assertTrue((book_uriref, rdflib.RDF.type, self.BIBO.Periodical),
            'document with issn should be a bibo:Periodical')
        self.assert_(g.triples((None, self.SCHEMA_ORG.mentions, book_uriref)),
            'document with id should be mentioned by context (i.e. collection)')



# test custom template tag ifurl
class IfUrlTestCase(DjangoTestCase):

    def test_ifurl(self):
        template = Template("{% load ifurl %}{% ifurl preview 'fa:full-findingaid' 'fa:findingaid' id=id %}")
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
        template = Template("{% load ifurl %}{% ifurl preview 'fa:full-findingaid' 'fa:findingaid' id=id as myurl %}{{ myurl }}")
        urlopts = {'id': 'docid'}
        context = RequestContext(HttpRequest(), {'preview': False, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:findingaid', kwargs=urlopts), url,
            "ifurl correctly stores resulting url in context when 'as' is specified")

class ArkPidTestCase(DjangoTestCase):

    def test_ark_pid(self):
        self.assertEqual('17kjg', ark_pid('http://pid.emory.edu/ark:/25593/17kjg'))
        self.assertEqual(None, ark_pid('http://example.com/not/an/ark'))

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
