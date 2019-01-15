API
===


.. automodule:: bonfig
    :members: Bonfig, Store

Fields
------

NOTE
~~~~

You will notice in the `Field` and `Section` parameters for `__init__` which start with `'_'`, these parameters
are not intended to be set directly. Instead these classes should be accessed by either parent `Stores` or `Sections`.

.. automodule:: bonfig.fields
    :members: Section, Field, make_sub_field, FieldDict
