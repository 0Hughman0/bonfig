.. _api:

API
===


.. automodule:: bonfig
    :members: Bonfig, Store

Fields
------

NOTE
~~~~

You will notice in the `Field` and `Section` parameters for `__init__` which start with `'_'`, these arguments
are not intended to be set directly. Instead these classes should be accessed by either parent `Stores` or `Sections`,
and these arguments will be implicitly set.

.. automodule:: bonfig.fields
    :members: Section, Field, make_sub_field, FieldDict
