##################
python-pfconclient
##################

A python client for the (flask-based) pfcon API.

.. image:: https://travis-ci.org/FNNDSC/python-pfconclient.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/python-pfconclient


Installation
------------

.. code-block:: bash

   pip install -U python-pfconclient


Usage
-----

For the ``run`` subcommand
==========================

Run ``fs`` plugin until finished and get the resulting files in a local directory:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-1 run --cmd_args '--saveinputmeta --saveoutputmeta path:--dir cube/uploads'
    --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simplefsapp
    --selfexec simplefsapp.py --selfpath /usr/src/simplefsapp --execshell python3 --type fs /tmp/sbin/in /tmp/sbin/out/chris-jid-1


Run ``ds`` plugin until finished and get the resulting files in a local directory:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-2 run --cmd_args '--saveinputmeta --saveoutputmeta --prefix lolo'
    --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simpledsapp
    --selfexec simpledsapp.py --selfpath /usr/src/simpledsapp --execshell python3 --type ds /tmp/sbin/in /tmp/sbin/out/chris-jid-2


For the ``submit`` subcommand
=============================

Submit ``fs`` plugin for execution:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-3 submit --cmd_args '--saveinputmeta --saveoutputmeta path:--dir cube/uploads'
    --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simplefsapp
    --selfexec simplefsapp.py --selfpath /usr/src/simplefsapp --execshell python3 --type fs /tmp/sbin/in


Submit ``ds`` plugin for execution:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-4 submit --cmd_args '--saveinputmeta --saveoutputmeta --prefix lolo'
    --auid cube --number_of_workers 1 --cpu_limit 1000 --memory_limit 200 --gpu_limit 0 --image fnndsc/pl-simpledsapp
    --selfexec simpledsapp.py --selfpath /usr/src/simpledsapp --execshell python3 --type ds /tmp/sbin/in


For the ``poll`` subcommand
=============================

Keep polling for the execution status of a previously submitted plugin until it finishes:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-3 poll


For the ``status`` subcommand
=============================

Perform a single check of the execution status of a previously submitted plugin:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-4 status


For the ``download`` subcommand
===============================

Download the output files of a previously submitted plugin that has already finished:

.. code-block:: bash

    pfconclient http://localhost:5006/api/v1/ chris-jid-4 download /tmp/sbin/out/chris-jid-4