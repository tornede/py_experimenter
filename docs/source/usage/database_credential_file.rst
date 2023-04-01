.. _database_credential_file:

------------------------
Database Credential File
------------------------

When working with ``MySQL`` as a database provider, an additional database credential file is needed, containing the credentials for accessing the database:

.. code-block:: 

    [CREDENTIALS]
    host = <host>
    user = <user>
    password = <password>

By default, this file is located at ``config/database_credentials.cfg``. If this is not the case, the corresponding path has to be explicitly given when :ref:`executing <execution>` ``PyExperimenter``.
