.. _database_credential_file:

------------------------
Database Credential File
------------------------

When working with ``MySQL`` as a database provider, an additional database credential file is needed, containing the credentials for accessing the database.
By default, this file is located at ``config/database_credentials.yml``. If this is not the case, the corresponding path has to be explicitly given when :ref:`executing <execution>` ``PyExperimenter``.
Below is an example of a database credential file, that connects to a server with the address ``example.mysqlserver.com`` using the user ``example_user`` and the password ``example_password``. 

.. code-block:: yaml

    CREDENTIALS:
      Database:
        user: example_user
        password: example_password
      Connection:
        Standard: 
          server: example.mysqlserver.com

We additionally also support utilizing encrypted connections with (m)tls.  To that end, the following parameters can be added to the ``Standard`` section of the database credential file
- ``use_ssl``: a boolean value indicating whether to use ssl
- ``ssl_params``: a dictionary containing the following keys:
  - ``ca``: the path to the ca certificate (optional, needed if the database server uses a custom ca certificate not trusted by the client)
  - ``cert``: the path to the user certificate (optional, needed in case of client authentication with mtls)
  - ``key``: the path to the user private key (optional, needed in case of client authentication with mtls)

.. code-block:: yaml

    CREDENTIALS:
      Database:
        user: example_user
        password: example_password
      Connection:
        Standard: 
          server: example.mysqlserver.com
          use_ssl: some_boolean_value
          ssl_params:
            ca: config/certificates/ca.crt
            cert: config/certificates/user_cert.crt
            key: config/certificates/user_private_key.key
