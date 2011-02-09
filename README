README
======

Overview
--------

This project is a Django web application for providing access to and limited
administration for Archival Finding Aid XML documents in the Encoded Archival
Description format (`EAD <http://www.loc.gov/ead/>`_ ).

Components
----------

fa
~~
Functionality for searching, browsing, and displaying Finding Aid objects.
Includes PDF version of Finding Aid and mulitple views for complex, multi-part
Finding Aids with series, subseries, and indexes.  Also includes a 'preview' mode
for use with the :mod:`~findingaids.fa_admin` component, so that unpublished
documents can be previewed exactly as they will appear when published.

fa_admin
~~~~~~~~
This is a custom administration component for managing Finding Aid documents
and the Finding Aids site.  Includes some user account management, but the bulk
of the functionality revolves around preparing EAD files for publication on the
main site, via the 'prep', 'preview', and 'publish' functions.

content
~~~~~~~
Functionality for displaying the few non-EAD-based pages that are part of the
Finding Aids website.  Includes the site home page, content pages that are
populated via RSS feeds to allow leveraging existing content management tools,
and some simple email forms.

System Dependencies
-------------------

findingaids requires the following network resources:

  * LDAP for user authentication
  * A relational database for user and session information, task result status,
    and deleted Finding Aids
  * Persistent ID manager for minting ARKs to use as permanent URLs for Finding
    Aid documents
  * `eXist-db XML database <http://exist.sourceforge.net>`_ (1.4 or greater) for
    loading, searching, browsing, & displaying EAD Finding Aid XML documents
  * `RabbitMQ <http://www.rabbitmq.com/>`_ for brokering asynchronous tasks
  * Squid Web Cache

-----

For more detailed information, including installation instructions and upgrade
notes, see :ref:`DEPLOYNOTES`.  For details about the features included in each release,
see :ref:`CHANGELOG`.


