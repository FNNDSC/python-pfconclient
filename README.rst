##################
python-pfconclient
##################

A Python3 client for pfcon's web API.

.. image:: https://img.shields.io/github/license/fnndsc/python-pfconclient
    :alt: MIT License
    :target: https://github.com/FNNDSC/python-pfconclient/blob/master/LICENSE
.. image:: https://badge.fury.io/py/python-pfconclient.svg
    :target: https://badge.fury.io/py/python-pfconclient


Overview
--------
This repository provides a Python3 client for pfcon service's web API.
The client provides both a Python programmatic interface and a standalone CLI tool called ``pfconclient``.


Installation
------------

.. code-block:: bash

    $> pip install -U python-pfconclient


pfcon server preconditions
--------------------------

These preconditions are only necessary to be able to test the client against an actual instance of the pfcon server and run the automated tests.

Install latest Docker
=====================

Currently tested platforms:

- Ubuntu 18.04+ and MAC OS X 11.1+

Note: On a Linux machine make sure to add your computer user to the ``docker`` group.
Consult this page https://docs.docker.com/engine/install/linux-postinstall/

Fire up the full set of pfcon services
======================================

Open a terminal and run the following commands in any working directory:

.. code-block:: bash

    $> git clone https://github.com/FNNDSC/pfcon.git
    $> cd pfcon
    $> ./make.sh -N -F fslink

You can later remove all the backend containers with:

.. code-block:: bash

    $> cd pfcon
    $> ./unmake.sh -N -F fslink


Usage
-----

Python programmatic interface
=============================

Instantiate the client:

.. code-block:: python

    from pfconclient.client import Client, JobType

    token = Client.get_auth_token('http://localhost:30006/api/v1/auth-token/', 'pfcon', 'pfcon1234')
    cl = Client('http://localhost:30006/api/v1/', token)


Example: full fslink flow with ``pl-simpledsapp``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example assumes:

- The pfcon server was started with ``./make.sh -N -F fslink``
- pfcon is reachable at ``http://localhost:30006``
- STOREBASE defaults to ``/home/user/pfcon_fork/CHRIS_REMOTE_FS``
- Test data has been created under the storebase (see the concrete example in ``req_resp_flow.md`` for setup details)

.. code-block:: python

    job_id = 'chris-jid-2'

    # Step 1: Submit copy job
    copy_descriptors = {
        'input_dirs': ['home/user/cube'],
        'output_dir': 'home/user/cube_out',
    }
    cl.submit_job(JobType.COPY, job_id, copy_descriptors)

    # Step 2: Poll copy status until finished
    cl.poll_job_status(JobType.COPY, job_id)

    # Step 3: Submit plugin job
    plugin_descriptors = {
        'entrypoint': ['python3', '/usr/local/bin/simpledsapp'],
        'args': ['--prefix', 'le'],
        'auid': 'cube',
        'number_of_workers': 1,
        'cpu_limit': 1000,
        'memory_limit': 200,
        'gpu_limit': 0,
        'image': 'fnndsc/pl-simpledsapp',
        'type': 'ds',
        'input_dirs': ['home/user/cube'],
        'output_dir': 'home/user/cube_out',
    }
    cl.submit_job(JobType.PLUGIN, job_id, plugin_descriptors)

    # Step 4: Poll plugin status until finished
    cl.poll_job_status(JobType.PLUGIN, job_id)

    # Step 5: Get output file metadata
    resp = cl.get_plugin_job_json_data(job_id, 'home/user/cube_out')
    print(resp['rel_file_paths'])

    # Step 6: Submit upload job (no-op for fslink)
    upload_descriptors = {
        'job_output_path': 'home/user/cube_out',
    }
    cl.submit_job(JobType.UPLOAD, job_id, upload_descriptors)

    # Step 7: Submit delete job and poll until finished
    cl.submit_job(JobType.DELETE, job_id, {})
    cl.poll_job_status(JobType.DELETE, job_id)

    # Step 8: Remove all containers
    cl.delete_job(JobType.COPY, job_id)
    cl.delete_job(JobType.PLUGIN, job_id)
    cl.delete_job(JobType.DELETE, job_id)


Visit the `Python programmatic interface`_ wiki page to learn more about the client's programmatic API.

.. _`Python programmatic interface`: https://github.com/FNNDSC/python-pfconclient/wiki/Python-programmatic-interface


Standalone CLI client tool
==========================

Get and print auth token with the ``auth`` subcommand:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ auth --pfcon_user pfcon --pfcon_password pfcon1234


Submit a copy job:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> submit --job_type copy --jid chris-jid-2 --input_dirs home/user/cube --output_dir home/user/cube_out


Poll copy job status:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> poll --job_type copy --jid chris-jid-2


Submit a ``ds`` plugin job:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> submit --job_type plugin --jid chris-jid-2 --entrypoint python3 /usr/local/bin/simpledsapp --args '--prefix le' --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simpledsapp --type ds --input_dirs home/user/cube --output_dir home/user/cube_out


Poll plugin job status:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> poll --job_type plugin --jid chris-jid-2


Get plugin job status:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> status --job_type plugin --jid chris-jid-2


Delete a copy job's container:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> delete --job_type copy --jid chris-jid-2


Delete a plugin job's container:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> delete --job_type plugin --jid chris-jid-2


Submit a delete job:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> submit --job_type delete --jid chris-jid-2


Poll delete job status:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> poll --job_type delete --jid chris-jid-2


Delete a delete job's container:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> delete --job_type delete --jid chris-jid-2


Visit the `standalone CLI client`_ wiki page to learn more about the CLI client.

.. _`standalone CLI client`: https://github.com/FNNDSC/python-pfconclient/wiki/Standalone-CLI-client-tool


Development and testing
-----------------------

Optionally setup a virtual environment
======================================

Install ``virtualenv`` and ``virtualenvwrapper`` using your OS package manager.

Create a directory for your virtual environments e.g.:

.. code-block:: bash

    $> mkdir ~/Python_Envs

You might want to add the following lines to your ``.bashrc`` or ``.zshrc`` file:

.. code-block:: bash

    VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
    export WORKON_HOME=~/Python_Envs
    source /usr/local/bin/virtualenvwrapper.sh

Then source the file and create a new Python3 virtual environment:

.. code-block:: bash

    $> mkvirtualenv pfcon_client_env

To activate pfcon_client_env:

.. code-block:: bash

    $> workon pfcon_client_env

To deactivate pfcon_client_env:

.. code-block:: bash

    $> deactivate


Clone the repo
==============

.. code-block:: bash

    $> git clone https://github.com/FNNDSC/python-pfconclient.git


Run automated tests
===================

.. code-block:: bash

    $> cd python-pfconclient
    $> workon pfcon_client_env
    $> pip install -e ".[dev]"
    $> pytest
