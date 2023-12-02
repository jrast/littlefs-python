===================
littlefs for Python
===================

.. image:: https://readthedocs.org/projects/littlefs-python/badge/?version=latest
    :target: https://littlefs-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/littlefs-python.svg
    :target: https://badge.fury.io/py/littlefs-python

littlefs-python provides a thin wrapper around littlefs_, a filesystem targeted for
small embedded systems.
The wrapper provides a pythonic interface to the filesystem and allows the creation,
inspection and modification of the filesystem or individual files.
Even if this package uses Cython_, the goal is not to provide a high performance
implementation. Cython was chosen as an easy method is offered to generate the binding
and the littlefs library in one step.

Quick Examples
==============
Let's create a image ready to transfer to a flash memory using the pythonic interface:

.. code:: python

    from littlefs import LittleFS

    # Initialize the File System according to your specifications
    fs = LittleFS(block_size=512, block_count=256)

    # Open a file and write some content
    with fs.open('first-file.txt', 'w') as fh:
        fh.write('Some text to begin with\n')

    # Dump the filesystem content to a file
    with open('FlashMemory.bin', 'wb') as fh:
        fh.write(fs.context.buffer)

The same can be done by using the more verbose C-Style API, which closely resembles the
steps which must be performed in C:

.. code:: python

    from littlefs import lfs

    cfg = lfs.LFSConfig(block_size=512, block_count=256)
    fs = lfs.LFSFilesystem()

    # Format and mount the filesystem
    lfs.format(fs, cfg)
    lfs.mount(fs, cfg)

    # Open a file and write some content
    fh = lfs.file_open(fs, 'first-file.txt', 'w')
    lfs.file_write(fs, fh, b'Some text to begin with\n')
    lfs.file_close(fs, fh)

    # Dump the filesystem content to a file
    with open('FlashMemory.bin', 'wb') as fh:
        fh.write(cfg.user_context.buffer)


Installation
============

.. note::
    As littlefs_ is bundled with the package you will need to install the correct version of
    this package in successfully read or create images for your embedded system. If you start
    from scratch the latest version is recommended.

    .. csv-table::
        :header: "Package Version", "LittleFS Version", "LittleFS File System Version"

        0.8.X, 2.8.0, 2.0 / 2.1 [#f1]_
        0.7.X, 2.7.0, 2.0 / 2.1 [#f1]_
        0.6.X, 2.7.0, 2.0 / 2.1 [#f1]_
        0.5.0, 2.6.1, 2.1
        0.4.0, 2.2.1, 2.0
        0.3.0, 2.2.1, 2.0

    .. [#f1] See ``test/test_multiversion.py`` for examples.


This is as simple as it can be::

    pip install littlefs-python

At the moment wheels (which require no build) are provided for the following platforms,
on other platforms the source package is used and a compiler is required:

 - Linux: Python 3.8 - 3.12 / x86_64, arm64
 - MacOS: Python 3.8 - 3.12 / x86_64, arm64
 - Windows: Python 3.8 - 3.12 / 32- & 64-bit


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


Development Hints
-----------------

- Test should be run before committing: `pytest test`
- Mypy is used for typechecking. Run it also on the tests to catch more issues:
  `mypy src test test/lfs`
- Mypy stubs can be generated with `stubgen src`. This will create a `out` directory
  containing the generated stub files.


Creating a new release
======================

NEW (with github deploy action):

- Make sure the master branch is in the state you want it.
- Create a new tag with the correct version number and push the tag to github
- Start the "Build and Deploy Package" workflow for the created tag on github


OUTDATED (without github deploy action):

- Make sure the master branch is in the state you want it.
- Create a tag with the new version number
- Wait until all builds are completed. A new release should be created
  automatically on github.
- Build the source distribution with `python setup.py sdist`
- Download all assets (using `ci/download_release_files.py`)
- Upload to pypi using twine: `twine upload dist/*`



.. _littlefs: https://github.com/littlefs-project/littlefs
.. _Cython: http://docs.cython.org/en/latest/index.html
