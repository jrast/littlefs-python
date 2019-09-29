.. image:: https://travis-ci.org/jrast/littlefs-python.svg?branch=master
    :target: https://travis-ci.org/jrast/littlefs-python
    :alt: Build Status: Linux

.. image:: https://ci.appveyor.com/api/projects/status/v7i08nhfbs2e0vro?svg=true
    :target: https://ci.appveyor.com/project/jrast/littlefs-python
    :alt: Build Status: Windows

.. image:: https://readthedocs.org/projects/littlefs-python/badge/?version=latest
    :target: https://littlefs-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

===================
littlefs for Python
===================

littlefs-python provides a thin wrapper around littlefs_, a filesystem targeted for
small embedded systems.
The wrapper provides a pythonic interface to the filesystem and allows the creation,
inspection and modification of the filesystem or individual files.
Even if this package uses Cython_, the goal is not to provide a high performance
implementation. Cython was chosen as an easy method is offered to generate the binding
and the littlefs library in one step.

Quick Examples
==============
Let's create a image ready to transfer to a flash memory:

.. code:: python

    from littlefs import LittleFS

    # Initialize the File System according to your specifications
    fs = LittleFS(block_size=512, block_count=256)

    # Open a file and write some content
    with fs.open('first-file.txt', 'w') as fh:
        fh.write(b'Some text to begin with\n')

    # Dump the filesystem content to a file
    with open('FlashMemory.bin', 'wb') as fh:
        fh.write(fs.buffer)


Installation
============

This is as simple as it can be::

    pip install littlefs-python

At the moment wheels (which require no build) are provided for the following platforms,
on other platforms the source package is provided:

 - Linux


Development Setup
=================

Start by checking out the source repository of littlefs-python::

    git clone https://github.com/jrast/littlefs-python.git

The source code for littlefs is included as a submodule which must be
checked out after the clone::

    cd <littlefs-python>
    git submodule update --init

this ensures that the correct version of littlefs_ is cloned into
the littlefs folder. As a next step install the dependencies and install
the package::

    pip install -r requirements.txt
    pip install -e .

.. note::
    It's highly recommended to install the package in a virtual environment!



.. _littlefs: https://github.com/ARMmbed/littlefs
.. _Cython: http://docs.cython.org/en/latest/index.html
