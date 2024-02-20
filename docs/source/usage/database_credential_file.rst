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

However, for security reasons, databases might only be accessible from a specific IP address. In these cases, one can ssh into the network and use port forwarding to access the database. 
The following example shows how to connect to a database server using an SSH server with the address ``ssh_hostname`` and the port ``optional_ssh_port``.

.. code-block:: yaml

    CREDENTIALS:
      Database:
        user: example_user
        password: example_password
      Connection:
        Standard: 
          server: example.sshmysqlserver.com
        Ssh:
          server: example.mysqlserver.com (address from ssh server)
          address: ssh_hostname (either name/ip address of the ssh server or a name from you local ssh config file)
          port: optional_ssh_port (default: 22)
          passphrase: passphrase
          remote_address: optional_mysql_server_address (default: 127.0.0.1)
          remote_port: optional_mysql_server_port (default: 3306)
          local_address: optional_local_address (default: 127.0.0.1)
          local_port: optional_local_port (default: 3306)

Note that we do not support further parameters for the SSH connection, such as explicitly setting the private key file. To use these adapt you local ssh config file.