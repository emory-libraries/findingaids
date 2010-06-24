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
The following management commands are available.
For more details, use manage.py help <command>

 * **check_eadids**
    .. autoclass:: findingaids.fa.management.commands.check_eadids.Command
       :members:
 * **clean_ead**
    .. autoclass:: findingaids.fa_admin.management.commands.clean_ead.Command
       :members:
