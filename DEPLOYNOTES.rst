.. _DEPLOYNOTES:

DEPLOYNOTES
===========

Installation
------------

Instructions to install required software and systems, configure the application,
and run various scripts to load initial data.

Software Dependencies
~~~~~~~~~~~~~~~~~~~~~

We recommend the use of `pip <http://pip.openplans.org/>`_ and `virtualenv
<http://virtualenv.openplans.org/>`_ for environment and dependency
management in this and other Python projects. If you don't have them
installed, you can get them with ``sudo easy_install pip`` and then ``sudo pip install
virtualenv``.

Bootstrapping a development environment
---------------------------------------

* Copy ``findingaids/localsettings.py.dist`` to ``findingaids/localsettings.py``
  and configure any local settings: **DATABASES**,  **SECRET_KEY**,
  **SOLR_**, **EXISTDB_**,  customize **LOGGING**, etc.
* Create a new virtualenv and activate it.
* Install fabric: ``pip install fabric``
* Install subversion libraries: ``apt-get install libsvn-dev`` on debian/ubuntu, or
  ``brew install subversion`` on OSX.
* Use fabric to run a local build, which will install python dependencies in
  your virtualenv, run unit tests, and build sphinx documentation: ``fab build``
* To generate PDFs, you will need to install
  `Apache FOP <https://xmlgraphics.apache.org/fop/>`_ (``apt-get install fop``
  on debian/ubuntu or ``brew install fop`` on OSX)
* Celery/rabbitmq is only needed for publication and svn checkout, so you
  may not need to set it up.

  - To run celery, use ``python manage.py celeryd -Q findingaids``
  - To trigger an EAD svn checkout, define an archive in django admin.

After configuring your database, run migrate:

    python manage.py migrate

Deploy to QA and Production should be done using ``fab deploy``.

Setup the environment
~~~~~~~~~~~~~~~~~~~~~

When first installing this project, it is recommended to create a virtual environment
for it.  The virtualenv environment is a directory that can be installed anywhere you like,
perhaps adjacent to wherever the source code is deployed. To create your new environment,
simply run the virtualenv command::

  $ virtualenv --no-site-packages /home/findingaids/fa-env

.. Note::
  For Apache/WSGI installations, you should run this command as the apache user.

Source the activation file to invoke your new virtual environment (this requires that you
use the bash shell)::

  $ . /home/findingaids/fa-env

Once the environment has been activated inside a shell, Python programs
spawned from that shell will read their environment only from this
directory, not from the system-wide site packages. Installations will
correspondingly be installed into this environment.

.. Note::
  Installation instructions and upgrade notes below assume that
  you are already in an activated shell.

Install python dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^

FindingAids depends on several python libraries. If you are using pip, you can
install all of the dependencies in an automated fashion that will print status
messages as packages are installed. If there are any errors, pip should display
messages indicating the problem.

To install python dependencies, cd into the repository checkout and::

  $ pip install -r pip-install-req.txt

FindingAids requires a SQL database, but the type does not matter,
so this is not included in the pip-dependencies file.  You may want to
pip install  ``MySQL-python`` or ``psycopg``, depending on the database you
plan to use.

FindingAids requires a SQL database, but the type does not matter,
so this is not included in the pip-dependencies file.  You may want to
pip install  ``MySQL-python`` or ``psycopg``, depending on the database you
plan to use.

If you are a developer or are installing to a continuous ingration server
where you plan to run unit tests, code coverage reports, or build sphinx
documentation, you probably will also want to::

  $ pip install -r pip-dev-req.txt

Known Issues
""""""""""""

* As of 04/2011, installing **python-eulcore** from SVN via pip does not
  install the eulcore template themes correctly.  The easiest way to fix
  this is to manually create a symbolic link from the root of your
  virtualenv to the python-eulcore theme directory::

    $ cd /home/findingaids/fa-env
    $ ln -s src/python-eulcore/themes/


-----


* As of 04/2011, installing **python-eulcore** from SVN via pip does not
  install the eulcore template themes correctly.  The easiest way to fix
  this is to manually create a symbolic link from the root of your
  virtualenv to the python-eulcore theme directory::

    $ cd /home/findingaids/fa-env
    $ ln -s src/python-eulcore/themes/


-----

If you are **not** using pip to install python libraries, you will need the
following python libraries:

 * python-dateutil library `downloadable package
   <http://labix.org/python-dateutil>`_ or install via ``easy_install
   python-dateutil``
 * `zc.icp <http://pypi.python.org/pypi/zc.icp>`_ for querying cache status;
   install via ``easy_install zc.icp``
 * django-celery installed via ``easy_install django-celery``
 * feedparser -  ``easy_install feedparser``
 * `recaptcha-client <http://pypi.python.org/pypi/recaptcha-client>`_
   ``easy_install recaptcha-client``
 * `Beautiful Soup <http://www.crummy.com/software/BeautifulSoup/>`_
   ``easy_install beautifulsoup``
 * PIDmanager REST client - http://waterhouse.library.emory.edu:8080/hudson/job/pidman-rest-client-1.1.x
 * eulxml, eulexistdb, eulcommon, and eullocal


System Dependencies
~~~~~~~~~~~~~~~~~~~

Celery/RabbitMQ
^^^^^^^^^^^^^^^

We use celery for asynchronous tasks (currently for generating PDFs of Finding
Aids and populate them in the web cache), which requires a task broker.  We
recommend RabbitMQ.   On Ubuntu, RabbitMQ can be installed via::

  $ sudo easy_install django-celery
  $ sudo apt-get install rabbitmq-server

For more information on configuring this, please see
http://celeryq.org/docs/getting-started/broker-installation.html

FOP
^^^
Install `Apache FOP <http://xmlgraphics.apache.org/fop/>`_ for PDF generation.
On Ubuntu systems, ``sudo apt-get install fop``.  You will need to configure
the **XSLFO_PROCESSOR** setting with the full path to the command-line version of fop.
Note that running Fop requires a valid JAVA_HOME be set in the environment.

Squid Cache
^^^^^^^^^^^
To address certain performance issues (in particular, dynamic PDF generation),
this site should be set up behind a Squid Cache, which should be configured as a
transparent proxy.  Sample configuration::

    http_port 170.140.223.20:80 transparent vhost defaultsite=findingaids.library.emory.edu

Because PDFs will not be changing frequently, and because the django application
will refresh cached PDFs on when new or updated documents are published, Squid
should be configured to retain PDFs for longer than it normally would::

    refresh_pattern /documents/.*/printable/        10080   90%     10080

Other parts of the website include Last-Modified and ETag headers which should
make caching more effective.  This includes all single-document finding aid pages
as well as search and browse pages.  Browse and Search page urls are indicated
via query string, e.g.::

        /titles/B?page=2
        /search?keywords=ciaran+carson

In the transparent cache set up, Squid should automatically cache these documents
as users access them.  If possible, Squid should be configured so that cached
PDFs will be kept in preference to search and browse pages (the custom refresh
pattern for printable urls above may be sufficient for this).

Install the Application
~~~~~~~~~~~~~~~~~~~~~~~

Apache
^^^^^^
It is recommended to set up FindingAids up under Apache using mod_wsgi. Because
of a locking issue with a python library we use, the site `must` be configured as
a WSGI daemon using the **WSGIDaemonProcess** and **WSGIProcessGroup** settings.

The admin section of the site is found at ``/admin/`` under the base site url.
This uses Emory LDAP for login, so the admin site should be configured to run
under SSL.

Sample wsgi and apache configuration files are located in the apache directory
inside the source code checkout.  Copy them and edit them to adjust
for installation paths and IP addresses.

Configuration
^^^^^^^^^^^^^
Configure the application settings by copying localsettings.py.dist to
localsettings.py and editing settings for local database, LDAP, fedora, PID
manager, eXist-DB and key configuration.

eXist-DB
""""""""

FindingAids requires access to an eXist Database to publish, search, and displya
EAD Finding Aid documents.  All **EXISTDB_** settings in the localsettings example file
should be configured for access to an eXist 1.4.x instance.  It is recommended
to use this applicatoni to manage the eXist index configuration; if you plan to
do this, your configured **EXISTDB_SERVER_USER** should be in the DBA group.

The **EXISTDB_PREVIEW_COLLECTION** should be set to an eXist collection `outside`
of the main Finding Aids collection in eXist; it is used for admin functionality
only.  The preview collection should be present in eXist, and the configured
eXist user should have permission to write to this collection.

Proxy/Cache
"""""""""""

The celery task that loads the PDFs in the cache requires configuration
settings for **PROXY_HOST** and **SITE_BASE_URL**.

If you want to be able to check the status of PDFs in the cache, you must
also configure **PROXY_ICP_PORT**.  If you are using Squid, you may need
to adjust the ``icp_port`` and ``icp_access`` settings to allow this.

Celery Broker
"""""""""""""
The **BROKER_** settings in should be configured to match where your RabbitMQ
instance is installed and running.

PID Manager
"""""""""""

The configured **PIDMAN_USER** must have permission inside the pid manager to add
pids and targets.

Email Addresses & Notifications
"""""""""""""""""""""""""""""""

When this application is deployed to production, the Django **ADMINS** setting
should be populated with contact information for technical administators; when
any views raise an exception, these people will be emailed with the error.
Optionally, **SEND_BROKEN_LINK_EMAILS** can also be configured for additional
error reporting to either **ADMINS** or **MANAGERS**.  See `Django Error Reporting
<http://docs.djangoproject.com/en/1.2/howto/error-reporting/>`_ for more details.

There are feedback forms on the site that generate and send emails.  This
makes use of the Django settings for **SERVER_EMAIL** and **EMAIL_SUBJECT_PREFIX**
and also requires some custom configurations:

* **FEEDBACK_EMAIL** should be configured with list of one or more email addresses
  to receive emails from the main feedback form.
* **REQUEST_MATERIALS_CONTACTS** should be a list of email & Archive pairs
  to be used with the request materials web form.

If the server where this site is deployed is not configured to act as an SMTP
server, you should make use of the Django EMAIL settings to specify the SMTP
server host and port (see `Django Email settings
<http://docs.djangoproject.com/en/1.2/ref/settings/#email-host>`_).

reCAPTCHA
"""""""""

This application includes email forms that make use of `reCAPTCHA
<http://www.google.com/recaptcha>`_ to avoid spam. reCAPTCHA requires the use of
keys restricted to your domain.  These can be generated for free on the reCAPTCHA
website.

The **RECAPTCHA_PUBLIC_KEY** and **RECAPTCHA_PRIVATE_KEY** settings are required
for the reCAPTCHA and feedback forms to work.  You may also set **RECAPTCHA_OPTIONS**,
to customize the way the CAPTCHA widget is displayed.

Django Cache
""""""""""""

A few small items within the site that are expected not to change frequently
(browse starting letters, RSS feeds for content) are cached with Django's internal
cache framework.  This should be configured with the **CACHE_BACKEND** setting.
Where caching is used, it will use the configured cache timeout, so it is
recommended to configure this explicitly.  The items being cached are not expected
to change frequently, so a timeout of 30 minutes or more may be reasonable; the
Django default timeout is 5 minutes.

For more details, see the documentation for `Django's cache framework
<http://docs.djangoproject.com/en/1.2/topics/cache/>`_.

Misc
""""

The **FINDINGAID_EAD_SOURCE** configuration should be set to the directory path
for the EAD files that will be accessible for loading to eXist via the admin
interface.  For normal operations, this directory does not need to be writable
by this application; however, some migration scripts expect to be able
to update the EAD documents in this configured directory.

The **CONTENT_RSS_FEEDS** configuration should be populated with URLs
for RSS feeds with content to populate the front-page site banner, announcements,
and non-EAD content pages.

Developer-specific configuration
""""""""""""""""""""""""""""""""

These settings may only be of interest to developers working on the application,
and are probably not relevant when installing the application to a QA or
production environment.

* eXist query response times are reported on templates in Debug mode
  only.  To view them, set DEBUG = True in your settings, and add any IP
  addresses that should have access to the **INTERNAL_IPS**.
* Logging is now available when running via runserver; logging settings are
  currently configured in localsettings.py.

Initialize/Update the Database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After all settings have been configured, initialize the relational db with all
needed tables and initial data using::

    $ python manage.py migrate

When an upgrade requires new database tables, the same command should be used.

eXist Index
^^^^^^^^^^^

After you have configured all the **EXISTDB_** settings in localsettings.py,
if you are using an eXist-db user in the DBA group, you can use the app
to manage the eXist index.  Load the index configuration using::

     $ python manage.py existdb_index load

This command should also be used when an upgrade requires a change to the eXist
index configuration.  If there is data loaded to eXist, you should reindex it
after loading the index configuration::

    $ python manage.py existdb_reindex

If you have a large number of finding aids loaded to the eXist database,
reindexing can take a while.

Load EAD to eXist
^^^^^^^^^^^^^^^^^

For an initial installation, several migration steps should be run on the EAD
documents found in the configured **FINDINGAID_EAD_SOURCE** directory; these scripts
require write access to the EAD source documents.  After these migration steps,
the documents can be loaded to eXist so they will be accessible in the website.

If you are starting with EAD documents in DTD-format, they must be converted
to the EAD XSD schema format::

    $ python manage.py ead_to_xsd

Prep the documents (automated cleaning, adding IDs, etc)::

    $ python manage.py prep_ead

Run a one-time migration to add machine-readable identifiers::

    $ python manage.py unitid_identifiers

Load the converted & prepared EAD documents to the eXist database::

    $ python manage.py load_ead

By default, ``load_ead`` will start celery tasks to generate and cache the PDFs
in the configured web cache.  This requires the celery daemon process to be
running.  The default behavior can be adjusted with command-line options (use
``--h`` to see available options).  When run in a mode that caches the PDFs,
the load script will wait until all celery tasks have completed in order to
report on the outcome; this can take a long time to finish.

(OPTIONAL) After you have loaded the data, you may want to check that all
eadids and titles in the loaded data are acceptable for the site::

    $ python manage.py check_ead eadid
    $ python manage.py check_ead title

(OPTIONAL) To check response times for searching and browsing the loaded
content with the configured index, run the following::

    $ python manage.py response_times browse
    $ python manage.py response_times search

.. Tip::
 For minimal output with summary information only, use ``-v 0``.

Cached PDFs
"""""""""""

To check the status of PDFs in the cache, use::

    $ python manage.py check_pdfcache

This uses Internat Cache Protocol (ICP) to query the configured cache, and
requires that **PROXY_ICP_PORT** is set and the cache is configured to allow
ICP access.  See `Proxy/Cache`_ instructions in the `Configuration`_ section.

Celery Daemon
^^^^^^^^^^^^^
The celery worker needs to be running for asynchronous tasks.  To run through
django do::

    $ python manage.py celeryd

See http://ask.github.com/celery/cookbook/daemonizing.html for instructions
on configuring celery to run as a daemon.


Upgrade Notes
-------------

1.9
---

* Upgrade to Django 1.8 includes a switch from South to Django migrations.
  For a brand new deploy, you should run ``python manage.py migrate``
  normally.  To update an **existing** database, you will need to run
  migrations in this order (if you are prompted to remove
  `emory_ldap | emoryldapuserprofile` say no until after migrations
  are complete)::

      # migrate content types, required by everything else
      python manage.py migrate contenttypes --fake-initial
      # explicitly fake initial auth migration
      # (can't use fake initial fails because auth_user doesn't exist yet)
      python manage.py migrate auth 0001 --fake
      # fake emory_ldap migrations to avoid blanking out existing content
      python manage.py migrate emory_ldap --fake
      # fake-initial not working on fa_admin migrations
      python manage.py migrate fa_admin 0001 --fake
      # repeat if you get an error the first time
      python manage.py migrate fa_admin
      # run all other migrations, faking initial migrations where tables exist
      python manage.py migrate --fake-initial

* **SEND_BROKEN_LINK_EMAILS** setting has been removed in Django 1.8
  and should be removed from ``localsettings.py``.

* The configuration for LDAP has changed; update ``localsettings.py``
  based on the example LDAP configuration in ``localsettings.py.dist``.

1.7.3
-----

* This release adds integrations with Aeon, which requires the
  addition of two settings in localsettings.py:

  1. REQUEST_MATERIALS_URL
  2. REQUEST_MATERIALS_REPOS


1.7
---

* A new custom permission has been added to allow admins to view internal
  digital archival object (dao) links.  Run ``python manage.py syncdb``
  to create the new permission and add it to the Finding Aids Administrator
  group.
* Configure **KEEP_SOLR_SERVER_URL** to point to the Solr core used by the
  instance of the Keep corresponding to the findingaids site (e.g., QA or Production),
  so that item ids can be looked up and converted to ARK identifiers.
* Run a script to update findingaids in subversion, converting item ids
  in text notes to <dao>::

    python manage.py itemid_to_dao -c

  Note that this will update the EAD documents in subversion (the -c specifies
  to commit changes to subversion when the processing is complete).  Use
  the -n (dry run) option or run without -c if you wish to test first.


1.6
---

* **CONTENT_RSS_FEEDS** configuration is no longer used and can be removed
  from localsettings.


1.5 - svn admin release
-----------------------

* This release adds a dependency on subversion python bindings; installation
  requires that subversion libraries be installed on the system (on
  debian/ubuntu installe the ``libsvn-dev`` package; on OSX running
  ``brew install subversion`` should be sufficient).
* Run ``python manage.py migrate emory_ldap`` to convert the user accounts
  in the database to the new custom user model.
* Run ``python manage.py syncdb`` to create new database tables and update
  permissions.
* Configure subversion admin user and base working directory in localsettings.py
  with **SVN_USERNAME**, **SVN_PASSWORD**, and **SVN_WORKING_DIR**
* Remove **FINDINGAID_EAD_SOURCE** from localsettings since it is no longer used.
* Celery daemons should be restarted to pick up a newly added celery task.


1.3
---

* Adds a new configuration **DEFAULT_DAO_LINK_TEXT** in ``localsettings.py`` which
  can be used to specify the default link text for digital archival objects referenced
  in the EAD.  See the commented out example in ``localsettings.py.dist``; default
  value should be fine.
* When the code is deployed to staging the **ENABLE_BETA_WARNING** configuration
  should be set to True on ``localsettings.py```

1.2
~~~~

* The logging configuration for sending error messages to site admins has been updated
  for Django 1.5; it is recommended to update the logging configuration in
  ``localsettings.py`` based on the latest version of ``localsettings.py.dist``

1.1
~~~~

.. NOTE:

  Due to the upgrade to Django 1.4, ``manage.py`` is now in the top-level directory rather
  than in the ``findingaids`` application subdirectory, and the default WSGI file has been
  moved to ``findingaids/wsgi.py``

* If Apache is configured to use the included wsgi script, update the **WSGIScriptAlias**
  to the new location (``findingaids/wsgi.py``).

* Static files to be served out by Apache have been consolidated to a single
  directory; apache configuration files should be updated to serve out
  the ``static`` directory as ``/static`` and other references to the media directories
  should be removed.

* Update site and database to work with celery 3.0.

  * Add database tables for :mod:`south` migrations and update the database
    for the newest version of :mod:`celery`.

    * python manage.py syncdb
    * python manage.py migrate djcelery --fake 0001
    * python manage.py migrate djcelery

  * Celery broker should now be configured using **BROKER_URL** instead of
    individual **BROKER_** settings; see ``localsettings.py.dist`` for
    an example.

  * The celery worker should now be started via::

      python manage.py celery worker -Q findingaids

    Be sure to update any init scripts that use the old ``celeryd`` syntax.

  * If not using the WSGI script included with the source code, add the
    following to your wsgi script::

      import djcelery
      djcelery.setup_loader()

* Recommended: update emory_ldap database tables for :mod:`south` migrations
  using ``python manage.py migrate emory_ldap``.  If you get an error on the last
  migration, it is fine to fake it using ``python manage.py migrate emory_ldap 0004 --fake``

1.0.9
~~~~~

This update requires an upgrade to Django 1.3 and broken-out eulcore
modules (:mod:`eulxml`, :mod:`eulexistdb`, and :mod:`eulcommon`). To
update to the latest versions of Python dependencies, activate the
virtualenv environment and run::

    $ pip install -r pip-install-req.txt

If you wish to remove the old version of :mod:`eulcore`::

    $ pip uninstall eulcore

Logging must now be configured in ``localsettings.py`` in the Django
1.3 logging config format; see ``localsettings-sample.py`` for an
example configuration, and
http://docs.djangoproject.com/en/dev/topics/logging for more details.

Previous, custom logging configurations (**LOGGING_LEVEL**,
**LOGGING_FORMAT**, and **LOGGING_FILENAME**) will no longer be used,
so you may want to remove them from your ``localsettings.py`` file.

1.0.8
~~~~~

Because the PDF caching celery task has been modified, the FindingAids
celery daemon process should be restarted after updating the code.


1.0.6
~~~~~

To update to the latest version of :mod:`eulcore`, activate the
virtualenv environment and run::

    $ pip install -r pip-dependencies

This update requires a slight modification in the **EXISTDB**
configuration values in django settings and adds a new timeout
configuration.  You should update ``localsettings.py`` to split out
the eXist-db username and password from the **EXISTDB_SERVER_URL**
setting.  See ``localsettings-sample.py`` for an example.

You may now configure a timeout for eXist XML-RPC connections via the
new **EXISTDB_TIMEOUT** setting in ``localsettings.py``.  See
``localsettings-sample.py`` for an example and additional information.


1.0.5 bugfix release
~~~~~~~~~~~~~~~~~~~~

FindingAids has been updated for deploy with pip+virtualenv.  All dependencies
are now managed through pip, rather than using svn externals for local
dependencies.  To get the latest version of the software::

    $ . /home/findingaids/fa-env/bin/activate
    $ pip install -r pip-dependencies

There is currently a problem with automatic installation of eulcore themes.
Please follow the work-around instructions described under `Known Issues`_.

Because of this change, the CSS and images for the genlib theme are now
located under the ``themes`` directory in the virtualenv.  You should either
create a symbolic link to the genlib_media directory under the project media
director, or add a new apache alias to the virtualenv location, e.g.::

  Alias /static/genlib_media /home/findingaids/env/themes/genlib/genlib_media

Make sure that the apache configuration specifies the virtualenv in the
WSGI python-path and edit your django.wsgi file to set the **VIRTUAL_ENV**
environment variable, eg.::

    os.environ['VIRTUAL_ENV'] = '/home/httpd/findingaids/env/'


1.0 Site Design & Content
~~~~~~~~~~~~~~~~~~~~~~~~~

To get the latest database changes and fixtures, run ``syncdb`` as documented in
`Initialize/Update the Database`_.

The eXist index configuration has changed slightly.  Please reload and reindex
as described in `eXist Index`_.

New python libraries are required for reCAPTCHA (recaptcha-client) and RSS feed
parsing (feedparser).  The easiest way to install them is using the
pip-dependencies file as documented in `Install python dependencies`_.

Non-EAD content pages are now populated with RSS feeds; configure the expected
feeds in the new **CONTENT_RSS_FEEDS**  setting as documented in `Misc`_.

RSS feeds are cached using Django's internal caching framework; see `Django
Cache`_ in the `Configuration`_ documentation for details on what should be
configured in local settings.

There are new two web-based forms that generate emails.  In support of this,
several new configurations are required in localsettings.py.  New fields are
**FEEDBACK_EMAIL** and **REQUEST_MATERIALS_CONTACTS**.  See `Email Addresses &
Notifications`_. These forms also make use of reCAPTCHA, which requires that
you set reCAPTHCA public and private keys in localsettings.py as documented
in `reCAPTCHA`_.

Now using the BeautifulSoup python library for some minimal processing of RSS
feed HTML content; install using the pip-dependencies file as documented in
`Install python dependencies`_.

0.4.1 Unitid Identifiers
~~~~~~~~~~~~~~~~~~~~~~~~

There is a new one-time migration script that is now part of the initial
data load process.  Run the new command and then reload documents
as documented in `Load EAD to eXist`_::

  $ python manage.py unitid_identifiers

.. Note::
 The unitid_identifiers script requires write access to the EAD source documents.

0.4 Persistent IDs
~~~~~~~~~~~~~~~~~~

Finding Aids now relies on the PID manager for generating ARKs.
(Requires at least 0.9.x, with REST API).  See the `PID Manager`_ section
in the `Configuration`_ section of the installation instructions, and
see localsettings-sample.py for the required settings.

Re-run the prep and load steps documented in `Load EAD to eXist`_ to
create ARKs for all EADs (shis is now part of the prep step) and load the
updated documents to eXist.

.. Note::
 The prep script requires write-access to the EAD source files.

0.3 Enhanced Search
~~~~~~~~~~~~~~~~~~~

Pisa/ReportLab PDF generation has been replaced with XSL-FO and Apache FOP.
See `FOP`_ section under `System Dependencies`_ .
Pisa and ReportLab are no longer in use and can be uninstalled.

To get the latest database changes and fixtures, run ``syncdb`` (documented in
`Initialize/Update the Database`_).

Search and browse pages now include a last-modified header to enable caching.
There may be no additional configuration required to take advantage of this;
see `Squid Cache`_ for more details.

The eXist index configuration has changed.  Load the new version as documented
in `eXist Index`_ (reindex is not required).

The FindingAids site now requires EAD documents in EAD schema format instead
of the DTD-format we were using previously.  Migrate and reload all documents
as documented in `Load EAD to eXist`_.

Logging is now available when running via runserver; it is currently NOT
enabled when running through mod wsgi.  See `Developer-specific configuration`_.

0.2 Data Preparation / Admin site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are a few new external dependencies; see `Install python dependencies`_
for details.

The application now requires a `Celery/RabbitMQ`_ task broker and requires that
the celery daemon be running to handle asynchronous tasks (caching PDFs).  See
`Celery Daemon`_ for details.

Update localsettings.py with configuration settings that have been
added since the last version (see examples in localsettings-sample.py and
documentation in the `Configuration`_ instructions).

* **EXISTDB_SERVER_TIMEZONE** and **EXISTDB_PREVIEW_COLLECTION** - see `eXist-DB`_
* **FINDINGAID_EAD_SOURCE** - see `Misc`_
* Proxy/cache settings: **PROXY_HOST** & **SITE_BASE_URL** - see `Proxy/Cache`_
* Celery Broker/RabbitMQ settings - see `Celery Broker`_

The Finding Aids site now requires a sql database for user
management and tracking deleted finding aids.  You should set up a
database, configure it in localsettings.py, and run ``migrate`` to
initialize required tables, as documented in `Initialize/Update the Database`_.

There are new manage.py scripts to clean up EAD documents and load them to eXist.
Follow the steps documented in `Load EAD to eXist`_.

The new admin section of the site is at ``/admin/`` under the base site url.
This uses Emory LDAP for login, so it should be configured to run under SSL.
See the `Apache`_ section of `Install the Application`_.

eXist query response times can be reported on web pages for developers; see
`Developer-specific configuration`_ for details.

There is a new script to check the status of PDFs in the configured cache.  See
`Cached PDFs`_ for details.
