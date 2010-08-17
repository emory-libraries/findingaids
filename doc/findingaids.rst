:mod:`findingaids` -- Django-based Finding Aids site
====================================================

.. module:: findingaids

:mod:`findingaids` is a django site for search, browse, and display of
EAD xml finding aids, based on the eXist-db xml database.


Models
------

Because finding aids is an eXist/xml-based site, models are based on
:class:`eulcore.xmlmap.XmlObject` and make use of
:class:`eulcore.existdb.query.QuerySet` for easy access to sections of
EAD xml, and for search and retrieval within the eXist database.


Finding Aid (EAD)
^^^^^^^^^^^^^^^^^
.. autoclass:: findingaids.fa.models.FindingAid
   :members:
   :inherited-members:

Series and other Finding Aid sections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: findingaids.fa.models.Series
   :members:
   :inherited-members:

.. autoclass:: findingaids.fa.models.Subseries
   :members:

.. autoclass:: findingaids.fa.models.Subsubseries
   :members:

.. autoclass:: findingaids.fa.models.Index
   :members:

.. autoclass:: findingaids.fa.models.ListTitle
   :members:

Views
-----
.. automodule:: findingaids.fa.views
   :members:

.. 
    NOTE: documentation for views with condition decorator is NOT currently
    working; even though the django code uses the functools.wraps as specified,
    the docstring is getting lost because of the decorator.

Other Functions
---------------
.. automodule:: findingaids.fa.utils
   :members:

Custom Template Filters & Tags
------------------------------
.. automodule:: findingaids.fa.templatetags.ead
   :members:

.. automodule:: findingaids.fa.templatetags.ifurl
   :members:

Admin Site
----------

The admin section of the finding aids site is designed to allow archivists to
manage the finding aids content.


Admin Views
^^^^^^^^^^^
.. automodule:: findingaids.fa_admin.views
   :members:

Admin Functions
^^^^^^^^^^^^^^^
.. automodule:: findingaids.fa_admin.utils
   :members:


Custom manage commands
----------------------
The following management commands are available.  For more details, use
``manage.py help <command>``.  As much as possible, all custom commands honor the
built-in django verbosity options.

 * **check_ead**
    .. autoclass:: findingaids.fa.management.commands.check_ead.Command
       :members:
 * **clean_ead**
    .. autoclass:: findingaids.fa_admin.management.commands.clean_ead.Command
       :members:
 * **load_ead**
    .. autoclass:: findingaids.fa_admin.management.commands.load_ead.Command
       :members:
* **response_times**
    .. autoclass:: findingaids.fa.management.commands.response_times.Command
       :members:
* **check_pdfcache**
    .. autoclass:: findingaids.fa.management.commands.check_pdfcache.Command
       :members:
* **ead_to_xsd**
    .. autoclass:: findingaids.fa.management.commands.ead_to_xsd.Command
       :members:
