=====
Usage
=====

littlefs-python offers three interfaces to the underlying littlefs library:

- A C-Style API which exposes all functions from the library using a minimal
  wrapper, written in Cython, to access the functions.
- A pythonic high-level API which offers convenient functions similar to
  the ones known from the :mod:`os` standard library module.
- A command line tool, available as ``littlefs-python``. See :ref:`doc-cli`
  for more information.

Both API's can be mixed and matched if required.

C-Style API
===========

The C-Style API tries to map functions from the C library to python with as little
intermediate logic as possible. The possibility to provide customized :func:`read`,
:func:`prog`, :func:`erase` and :func:`sync` functions to littlefs was a main goal
for the api.

All methods and relevant classes for this API are available in the :mod:`littlefs.lfs`
module. The methods where named the same as in the littlfs library, leaving out the `lfs_`
prefix. Because direct access to C structs is not possible from python, wrapper classes
are provided for the commonly used structs:

- :class:`~littlefs.lfs.LFSFilesystem` is a wrapper around the :c:type:`lfs_t` struct.
- :class:`~littlefs.lfs.LFSFile` is a wrapper around the :c:type:`lfs_file_t` struct.
- :class:`~littlefs.lfs.LFSDirectory` is a wrapper around the :c:type:`lfs_dir_t` struct.
- :class:`~littlefs.lfs.LFSConfig` is a wrapper around the :c:type:`lfs_config_t` struct.

All these wrappers have a :attr:`_impl` attribute which contains the actual data. Note that
this attribute is not accessible from python.
The :class:`~littlefs.lfs.LFSConfig` class exposes most of the internal fields from the
:attr:`_impl` as properties to provide read access to the configuration.


Pythonic API
============

While the pythonic API is working for basic operations like reading and writing files,
creating and listing directories and some other functionality, it's by no means finished.
Currently the usage is best explained in the :ref:`doc-examples` section.
