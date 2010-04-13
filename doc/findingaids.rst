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

Series
^^^^^^

.. autoclass:: findingaids.fa.models.Series
   :members:
   :inherited-members:

.. autoclass:: findingaids.fa.models.Subseries
   :members:

.. autoclass:: findingaids.fa.models.Subsubseries
   :members:


Views
-----
.. automodule:: findingaids.fa.views
   :members:

.. todo:: use more specific exceptions when object is not found in exist


Custom Template Filters
-----------------------
.. automodule:: findingaids.fa.templatetags.ead
   :members:
