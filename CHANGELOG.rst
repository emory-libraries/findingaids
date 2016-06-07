.. _CHANGELOG:

CHANGELOG
=========

The following is a summary of changes and improvements to the Finding
Aids application.  New features in each version should be listed, with the most
recent version first.  Upgrade or deployment notes should be found in
:ref:`DEPLOYNOTES`.

1.9.1
-----

* Prep step returns an incorrect message for new finding aids.

1.9.0
-----

* As a user, I can see a banner on individual finding aids where
  materials are stored offsite so that I know retrieval of these
  materials will take longer.
* As a user, I can see a scope note at the folder level of the finding
  aid in order to see additional information the archivist has added
  about that folder's contents.
* As an administrator, I can change staff contacts listed in the finding
  aids database website so that I can manage the names and emails displayed
  on the request materials page.
* As an administrator I can initiate a user account from LDAP without
  requiring the person to log in so that I can manage user accounts
  more efficiently.
* bugfix: whitespace inconsistencies in keyword search results
* bugfix: browse by letters label inconsistency in certain rare cases
  (complete label with partial overlap in next label)
* Upgraded to eulexistdb 0.20 and eXist-db 2.2
* Upgrade to current Django 1.9
* Switched from local ldap implementation to django-auth-ldap
* Now configured to use django-debug-toolbar for development, with
  a panel for viewing existdb xqueries.

1.8.3
-----

* Text content changes for MARBL rename to Rose Library, along with
  other contact and name updates.
* Updated home page banner image for Pitts.

1.8.2
-----

* bugfix: correct RDFa for untitled container-level contents with tagged
  creator name.

1.8.1
-----

* bugfix: repeating biographical note in PDFs for documents with RDFa
* bugfix: Names in correspondence series <scopecontent> are no longer
  linked to <origination> in the RDF.

1.8 - RDFa enhancements
-----------------------

* As a researcher, I want to export title information from a finding
  aid so that I can analyze and organize the works in a person’s papers
  according to genre.
* As a researcher, I want to export titles' ISBN, ISSN, or OCLC numbers
  from a finding aid so that I can access the data associated with those
  publications.
* As a researcher, I want to export semantic, relational data from EAD
  so that I can analyze it in network graph software like Gephi.
  [See the new script in scripts/rdfa-to-gexf]
* bugfix: PDF generation display issue for long numbers in box/folder
* bugfix: Request materials button not appearing for appropriate series.
* Replaced current finding aids logo with the standard LITS logo.
* Update Database Group initial fixture data to avoid overwriting
  new production group definitions

1.7.4
-----
* made related_materials repeatable

1.7.3 - Aeon integration
------------------------

* As a user viewing individual finding aids in the finding aids
  database, I can click on a button in a finding aid that takes me into
  the Aeon system in order to request boxes I want to use.


1.7.2
-----

* Minor text corrections on the site home page.
* bugfix: updated the ead_load script so it can be used with the subversion
  architecture for EAD content that we switched to in 1.5

1.7.1
-----

* bugfix: small corrections to itemid_to_dao script for issues
  encountered in production that were not found in testing
* bugfix: RDFa collection resource should be URI instead of string

1.7 - administrative and internal digital archival object support
-----------------------------------------------------------------

* When a logged in administrative user is searching the finding aids
  database, they can optionally restrict results to all collections with
  digital objects.
* Researchers will be able to see identifiers for digitized content that
  can only be accessed in the reading room, so that they can search for
  those items in the kiosk.
* When an administrative user is viewing the web page for a single
  finding aid, they can search for digital objects within that finding
  aid either by entering a keyword/keyword phrase in combination with the
  digital objects only filter or by just searching for all the digital
  objects in the finding aid.
* When an administrative user is logged into the finding aids database,
  they will see an indication that they are logged in on each page of the
  finding aids website in order to remember which view (administrative or
  public) they are seeing.
* When administrative users view webpages for a finding aid with digital
  archival object references in the EAD document, they can distinguish
  when the <dao> display in the administrative view is different from the
  public view and when <dao> information is hidden from the public view
  completely.
* A logged in findingaids staff user will be able to see links for
  internal-only digitized content, including any that are suppressed
  from display for researchers, so that they can access and manage
  archival digitized content.
* When administrative users view webpages for a finding aid with digital
  archival object references in the EAD document, they can see and click
  on links in order to access all the digital archival objects created
  or owned by Emory University, both public and for internal use only.
* A developer or system administrator can run a script on all EAD finding
  aids to add digital archival object references for container-level items
  that include digital filenames in order to provide administrative access
  to digitized content and prepare for future access options.
* As a researcher, I want to be able to see archivist supplied notes about
  processing at the series and subseries level so that I can understand
  how to locate material within a collection.
* New banners from the home page.

* bugfix: series titles with quotes break RDFa output
* bugfix: As a researcher, I want to be able to see any notes associated
  with index content, so that I have any additional information provided
  by the archivists.
* bugfix: As a researcher, I want to be able to see archivist supplied
  notes about processing at the series and subseries level so that I can
  understand how to locate material within a collection.
* bugfix: correct RDFa relation between collection and creator of the collection.

1.6
---

* Remove dependency on RSS feeds for content pages, home page banners,
  and home page news items.
* Updated organizational logo in the header.
* bugfix: Loading the list of finding aid files from subversion in the
  tabbed display of the administrative interface is too slow.
* bugfix: display repeated <separatedmaterial> sections (formerly
  only the first one was being displayed)
* bugfix: if a login session times out, admin file tabs will not load;
  now redirects user to login again

1.5.1
-----

* bugfix: configure celery task added in 1.5 for svn checkout so it is
  directed to findingaids queue so it gets picked up by the celery worker.

1.5
---

* A superuser can associate an archivist with one or more archives and their
  corresponding subversion repositories so that archivists can preview and
  publish for only the archives they are assigned.
* Superusers of the finding aids database can easily navigate between the
  django administrative module and the finding aids database administrative module.
* When an archivist associated with a single archive logs in to the admin site,
  they see a list of EAD documents in the associated subversion repository and
  are able to prep, preview, and publish finding aids from that repository.
* When an archivist associated with multiple archives logs in to the admin site,
  they see a tab for each corresponding subversion repository, each with a list
  of EAD documents in that subversion repo for prep, preview and publication.
* An archivist with permissions on multiple archives can choose a primary
  archive so they can view EAD documents from that repository by default
  when they log in.
* When an archivist preps an EAD document that requires modifications, they can
  click a button to accept and apply those changes so that updates are automatically
  committed to subversion on their behalf.
* Archivists can only prep, preview, and publish EAD documents from the  subversion
  repositories they have been associated with in the admin site, for security.
* An archivist can only delete a published finding aid from the website if it is
  associated with an archive that they have permission to manage, for security reasons.
* When an archivist with permissions for multiple repositories selects a repository
  tab on the main admin page, that repository tab stays active until they select
  another repository or logout, in order to avoid confusion when prepping,
  previewing, and publishing content from a single repository.
* Deprecated and unused support for publish without preview has been removed.
* New celery task: when an archive is defined or updated, check out (or update)
  a local copy of the subversion repository.
* bugfix: add redirect for top-level /favicon.ico url

1.4.1
-----

* bugfix to correct PDF generation (broken in some cases due to template
  changes relating to RDFa output)

1.4 - RDFa
----------

* When a search engine accesses the web page for a finding aid, it can
  harvest semantic information about the finding aid document, so that
  the document can be related to other embedded semantic content.
* A system or technical user can view RDF XML based on the embedded RDFa
  in a finding aid page, in order to harvest RDF in a more standard format
  or to review the embedded data on the page.
* When a search engine accesses the web page for a finding aid with names
  tagged in the EAD, it can harvest semantic information about the originator
  of the finding aid from the collection description so the embedded data
  can become useful in another context.
* When a search engine accesses the Index of Selected Correspondents for
  a finding aid with names tagged in the EAD, it can harvest semantic
  information about correspondents with the originator of the finding aid
  so the embedded data can become useful in another context.
* When a search engine accesses a finding aid series describing correspondence
  for a finding aid with names tagged in the EAD, it can harvest semantic
  information about correspondents with the originator of the finding aid
  so the embedded data can become useful in another context
* When a search engine accesses the finding aid series for the Belfast Group
  Worksheets for a finding aid with names tagged in the EAD, it can harvest
  semantic information about participants in the group so the embedded data
  can become useful in another context.
* When a search engine accesses the finding aid series for the Belfast Group
  Worksheets for a finding aid with names tagged in the EAD, it can harvest
  group sheet titles in order so that title sequence can be preserved.

1.3
---

* When a researcher is viewing web pages or PDF documents for a finding aid
  with digital archival object references in the EAD document, they can see and
  click on links in order to access digital items associated with the
  collection.
* A researcher searching within a single finding aid can optionally restrict
  results to items that include digital objects in order to find digital content
  by keyword or all digital objects in one finding aid.
* A researcher searching all finding aids by keyword can optionally restrict
  results to collections with publicly accessible digital objects in order to make
  use of archival items available online.
* A researcher viewing the web page or PDF for a finding aid with
  digital archival object references in the EAD can see that the
  finding aid includes digital content by a header at the top of the
  page, so that they are aware some of the materials may be available
  online.
* Users can view PDF documents from within a browser so they can view,
  print, and save the entire finding aid quickly and easily.
* Configurable beta warning to be displayed in test/staging sites; turn on
  via **ENABLE_BETA_WARNING** setting.

1.2
---

* Updated to Django 1.5.
* When a user is viewing web pages for a finding aid with external references (extref tags)
  in the EAD document, they can see and click on links in order to access
  external webpages.
* When a user downloads the PDF for a finding aid with external references
  in the EAD document, they can click on links in case they want to access
  related content from the PDF.
* Automated tools, such as search engine robots or site crawlers, can find
  machine-readable site maps for findingaids and content pages, in order to
  improve search engine harvesting of finding aids site content.
* Bug fix: related material section should be displayed when present at series level

1.1
---

* When an admin is logged in, they will see a link to the admin page at
  the top of the left sidebar, so that they can always get back to the
  main admin page.
* A researcher viewing the HTML or PDF version of a finding aid can see
  the processing information from the EAD, so that they know who is responsible
  for the content.
* Updated to Django 1.4.2
* Updates to follow team best practices for Django project code organization:

  * Moved media directory to top-level sitemedia directory
  * Moved templates directory to top-level and moved app-specific templates
    into their respective apps.
  * Renamed localsettings.py example from ``localsettings-sample.py`` to
    ``localsettings.py.dist``

.. NOTE:

  Due to the upgrade to Django 1.4, ``manage.py`` is now in the top-level directory rather
  than included in the ``findingaids`` app directory.


1.0 micro releases
------------------

1.0.12
~~~~~~

* Catch exceptions when reloading cached content feed data.

1.0.11
~~~~~~

* Adjust the XQuery for single-document searches to be more efficient
  for large documents, in order to address a time-out issue identified
  in SCLC1083.

1.0.10
~~~~~~

* Better error-handling for empty list title in EAD when prepping for
  preview/load.
* Require eulxml 0.17.1 for improved xpath parser handling.

1.0.9
~~~~~

* Now compatible with Python 2.7
* Upgrade to Django 1.3 and the latest released versions of the
  broken-out eulcore modules (:mod:`eulxml`, :mod:`eulexistdb`, and
  :mod:`eulcommon`).
* Minor error-handling and search-engine optimization for the feedback
  page.
* Rewrite rule to handle non-existent URL
  ('-Libraries-EmoryFindingAids') that search engines follow from
  other Emory sites.
* Add a reset button to the advanced search form so that a selected
  repository can be unselected.

1.0.8
~~~~~

* bugfix: allow admin publication of documents with a ``<title>`` at
  the beginning of the document ``<unittitle>``
* bugfix: Revised logic for celery PDF caching task, to ensure cache is
  cleared and reloaded with the new version of a published document.
* Plain HTML page with a list of all published findingaids, with a
  link to the full EAD xml for each, as a simple way to allow
  harvesting content.


1.0.6
~~~~~
* Newer version of :mod:`eulcore.existdb` that adds a configurable
  timeout on queries made to the eXist database.

1.0.5
~~~~~
* Fix response-time issue for series/subseries page with highlighted search
  terms.
* Rework admin site preview mode logic so site cannot get stuck in preview
  mode.
* Use pip+virtualenv to manage dependencies like eulcore.

1.0.4
~~~~~
* Fix preview subseries link so it stays in series mode
* Update to eulcore to try to improve xpath error reporting for errors that
  are being generated on the prodution site by web spiders.

1.0.3
~~~~~
Minor usability and display tweaks:
* Show all alpha-browse page labels instead of only 9
* Brief search tips on the main page

1.0.2
~~~~~
* Fix character corruption issue in origination field on main finding aid
  page.

1.0.1
~~~~~
* Correct single-doucment search for simple finding aids with no series.

1.0 Site Design & Content
-------------------------

* Users can view additional pages maintained by the finding aids administrator
  which contain helpful information for regarding searching, defining terms,
  participating institutions, etc.
* User visiting the homepage sees one of several archivist-selected images
  (rotate randomly on page refresh) to market unique items in MARBL's collections.
* A user visiting the Finding Aids home page will see the most recent archivist-
  entered/created announcement (if any), in order to receive up-to-date news
  about special events or notifications about site downtime.
* Researchers can submit feedback relating to the website site from the main
  homepage to help improve content and functionality.
* When a researcher is viewing a single finding aid, they can submit feedback to
  help correct typos and errors in the text or provide additional information
  which may be helpful to future researchers.
* Prospective visitors/researchers can submit a request for materials to
  facilitate retrieval prior to their arrival, which will be routed to the
  appropriate repository via email.
* Researchers can select a repository (other than 'All') on the advanced search
  form and submit the form without entering any other search terms, in order to
  browse all finding aids from a single repository.
* Users view html and PDF versions of finding aids that are consistently and
  cleanly formatted and displayed according to MARBL formatting requirements.

0.4.1 Unitid Identifiers
------------------------

* Custom manage command to add machine-readable identifiers to the top-level
  unitid tag.

0.4 Persistent IDs
------------------

* A system administrator can run a command that will generate ARKs for
  all existing EAD documents that do not already have ARKs to update the
  documents and store the ARK in the appropriate eadid attribute.
* When an archivist runs the 'prep' step in the Finding Aid admin
  site, an ARK will be generated and added to the 'prepared' EAD.
* When an archivist runs the 'prep' step on a Finding Aid with no ARK
  stored in the EADID, but for which an ARK has already been generated,
  the existing ARK will be used and the archivist will see an
  explanatory message.
* When an archivist attempts to publish a Finding Aid without an ARK
  stored in the EADID, the document will not be published and the
  archivist will see an explanatory message.
* A researcher or search engine accessing a Finding Aid document has
  access to view and bookmark the permanent url for that document.
* When researchers try to use the Emory Finding Aids Database and it
  is down, they will see a message about the problem and who to contact.


0.3 Enhanced Search
-------------------

* When viewing a finding aid after a search, a researcher can easily find search
  terms and exact phrases because they are highlighted.
* When viewing a finding aid after a search, a researcher sees an indicator of
  which sections of the finding aid include their search terms.
* A system administrator can run a script to migrate EAD files in the
  configured source directory from EAD DTD format to EAD XSD schema.
* When an admin cleans, publishes, or previews an schema-based EAD document,
  the application validates against the XSD schema.
* Researchers can retrieve an alphabetical browse list in less than 5 seconds,
  based on the first letter of a stakeholder specified field.
* Researchers receive their search results in less than 5 seconds.
* Researchers can see how many pages of search results there are, and jump to
  any section of search results from any page in the search results.
* When viewing a finding aid with series or sub-series, a researcher can use
  breadcrumbs to navigate within the hierarchy of the document.
* Researchers can search for an exact phrase in all indexed fields in the full
  text of the finding aid, to allow targeted discovery.
* Researchers can search using wildcards to match partial or variant words.
* Researchers can use grouping and boolean operators in the main search input,
  to generate very precise, relevant search results.
* Researchers find finding aids with matches in stake-holder specified fields
  at the top of search results.
* When viewing a finding aid, a researcher can search within that one document,
  to find relevant folder contents in a large finding aid.
* Researchers can click on a subject heading (any of the controlaccess terms)
  in a single finding aid to discover other finding aids with the same subject headings.
* When browsing finding aids by any first letter, a researcher can jump to
  alphabetical groupings within that letter, to enable identifying and accessing
  a particular portion of that browse listing (e.g., A-Ar, As-Ax, etc.).
* When viewing a finding aid found via search, a researcher can get back to the
  last page of search results they were on.
* Researchers can filter their search by repository (MARBL, Pitts, University
  Archives, etc.), to find resources available at a specific location.
* Users interact with a site that has a consistent look and feel across
  Emory Libraries websites.

**Minor changes**

* Pisa/ReportLab PDF generation has been replaced with XSL-FO and Apache FOP.
* Logging now available in runserver
* Clean urls for series/subseries/index (without redundant eadid)
* Includes a prototype version simplepages for editable site content

0.2 Data Preparation / Admin site
---------------------------------

Replaces the legacy command-line ant process for validating EAD xml
data and loading it to the eXist database.

* An authorized archivist can log in to an admin section of the
  finding aids site inaccessible to other users.
* Logged in admins can view a list of finding aid files recently
  modified on F:\ and ready for upload, sorted by last modified.
* Logged in admins can select files from the recently modified list
  for upload directly to publication.
* Logged in admins can select a file from the recently modified list
  for preparing, see a list of changes made, and optionally download
  the prepared version if changes were made, in order to safely
  prepare the canonical copy of the EAD xml files.
* Logged in admins can select files from the recently modified list
  for preview; multiple admins can preview different documents
  simultaneously.
* An admin previewing a finding aid can click a link (on any page in a
  multi-page finding aid) to publish that document.
* When an admin tries to publish or preview an invalid finding aid,
  the user sees a meaningful error message directing them how to fix
  it.
* When the web application is unable to save a finding aid, the user
  sees a meaningful message describing the problem and how to proceed.
* Logged in admins can view a minimal alphabetical list of published
  finding aids.
* Logged in admins can select a finding aid for deletion from the
  alphabetical list of published finding aids.
* When a collection is removed from the production site, patrons
  accessing their URLs are referred to MARBL staff for collection
  status.
* Researchers can receive a pdf of a finding aid in less than 10
  seconds.
* A search engine or web crawler can harvest descriptive metadata
  based on the EAD contents along with the HTML data, to improve
  google-ability.
* A system administrator can run a command to prepare all or specified
  EAD xml files in the configured directory, in order to easily update
  all existing files to new standards.
* A system administrator can run a command to load all or specified
  EAD xml files in the configured source directory to the configured
  eXist collection, in order to easily populate a new eXist collection


0.1 Port to Django
------------------

Reimplementation of the functionality of the existing PHP Finding Aids
site in django and eXist 1.4.

* Researchers can browse finding aids alphabetically by first letter
  of title.
* Researchers can click on the title of a finding aid in search or
  browse results to view more details about what resources are
  available in that collection.
* Researchers can search finding aids by keyword.
* Developers can access EAD XML objects in an eXist-backed Django
  Model workalike.
* Researchers can click 'download PDF' when viewing a single finding
  aid to download a PDF version of the entire finding aid.
* Researchers can navigate through finding aid site with the same look
  and feel of the library site.
* When a researcher clicks on an old link to a drupal or pre-drupal
  finding aid URL, they are automatically redirected to new finding
  aid URLs.
