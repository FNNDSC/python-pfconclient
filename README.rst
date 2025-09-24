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
    $> ./make.sh  

You can later remove all the backend containers with:

.. code-block:: bash

    $> cd pfcon
    $> ./unmake.sh


Usage
-----

Python programmatic interface
=============================

Instantiate the client:

.. code-block:: python

    from pfconclient import client

    token = client.Client.get_auth_token('http://localhost:30006/api/v1/auth-token/', 'pfcon', 'pfcon1234')
    cl = client.Client('http://localhost:30006/api/v1/', token)


Run ``fs`` plugin until finished using any local input directory and get the resulting files in a local output directory:

.. code-block:: python

    job_descriptors = {
        'args': ['--saveinputmeta', '--saveoutputmeta', '--dir', 'cube/uploads'],
        'args_path_flags': ['--dir'],  # list of flags with arguments of type 'path' or 'unextpath'
        'auid': 'cube',
        'number_of_workers': 1,
        'cpu_limit': 1000,
        'memory_limit': 200,
        'gpu_limit': 0,
        'image': 'fnndsc/pl-simplefsapp',
        'entrypoint': ['python3', '/usr/local/bin/simplefsapp'],
        'type': 'fs'
    }
    job_id = 'chris-jid-1'
    inputdir = '/tmp/sbin/in'
    outputdir = '/tmp/sbin/out/chris-jid-1'
    cl.run_job(job_id, job_descriptors, inputdir, outputdir)

Run ``ds`` plugin until finished using the local output directory of a previous plugin as its input directory and get the resulting files in a local output directory:

.. code-block:: python

    job_descriptors = {
        'args': ['--saveinputmeta', '--saveoutputmeta', '--prefix', 'lolo'],
        'auid': 'cube',
        'number_of_workers': 1,
        'cpu_limit': 1000,
        'memory_limit': 200,
        'gpu_limit': 0,
        'image': 'fnndsc/pl-simpledsapp',
        'entrypoint': ['python3', '/usr/local/bin/simpledsapp'],
        'type': 'ds'
    }
    job_id = 'chris-jid-2'
    inputdir = '/tmp/sbin/out/chris-jid-1'
    outputdir = '/tmp/sbin/out/chris-jid-2'
    cl.run_job(job_id, job_descriptors, inputdir, outputdir)

Visit the `Python programmatic interface`_ wiki page to learn more about the client's programmatic API.

.. _`Python programmatic interface`: https://github.com/FNNDSC/python-pfconclient/wiki/Python-programmatic-interface


Standalone CLI client tool
==========================

Get and print auth token with the `auth` subcommand:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ auth --pfcon_user pfcon --pfcon_password pfcon1234


Run ``fs`` plugin until finished using any local input directory and get the resulting files in a local output directory:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> run --jid chris-jid-3 --args '--saveinputmeta --saveoutputmeta --dir cube/uploads' --args_path_flags='--dir' --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simplefsapp --selfexec simplefsapp --selfpath /usr/local/bin --execshell python3 --type fs /tmp/sbin/in /tmp/sbin/out/chris-jid-3


Run ``ds`` plugin until finished using the local output directory of a previous plugin as its input directory and get the resulting files in a local output directory:

.. code-block:: bash

    $> pfconclient http://localhost:30006/api/v1/ -a <token> run --jid chris-jid-4 --args '--saveinputmeta --saveoutputmeta --prefix lolo' --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simpledsapp --selfexec simpledsapp --selfpath /usr/local/bin --execshell python3 --type ds /tmp/sbin/out/chris-jid-3 /tmp/sbin/out/chris-jid-4


Visit the `standalone CLI client`_ wiki page to learn more about the CLI client.

.. _`standalone CLI client`: https://github.com/FNNDSC/python-pfconclient/wiki/Standalone-CLI-client-tool


Arguments of type ``path`` or ``unextpath``
===========================================

If a plugin's ``args`` list contains flags with arguments of type ``path`` or ``unextpath`` then those flags should be included
in the optional ``args_path_flags`` list. This string represents a list of flags. This way ``pfcon`` server will
know that it has to substitute the local path specified by the flag by an actual path in the cloud.


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
