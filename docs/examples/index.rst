.. _doc-examples:

========
Examples
========


Preparing a filesystem on the PC
================================

In the following example shows how to prepare an image of a Flash / EEPROM
memory. The generated image can then be written to the memory by other
tools.


Start by creating a new filesystem:

.. doctest::

    >>> from littlefs import LittleFS
    >>> fs = LittleFS(block_size=256, block_count=64)

It's important to set the correct :attr:`block_size` and :attr:`block_count` during the
instantiation of the filesystem. The values you set here must match the settings which are
later used on the embedded system. The filesystem is automatically formatted and mounted [1]_
during instantiation. For example, if we look at the first few bytes of the underlying buffer,
we can see that the filesystem header was written:

.. doctest::

    >>> fs.context.buffer[:20]
    bytearray(b'\x00\x00\x00\x00\xf0\x0f\xff\xf7littlefs/\xe0\x00\x10')

We can start right away by creating some files. Lets create a simple file containing some
Information about the hardware [2]_:

.. doctest::
    :options:

    >>> with fs.open('hardware.txt', 'w') as fh:
    ...     fh.write('BoardVersion:1234\n')
    ...     fh.write('BoardSerial:001122\n')
    18
    19


File- and foldernames are encoded as ASCII. File handles of littlefs can be
used as normal file handles, using a context manager ensures that the file is
closed as soon as the :code:`with` block is left.

Let's create some more files in a configuration folder:

.. doctest::
    :options:

    >>> fs.mkdir('/config')
    0
    >>> with fs.open('config/sensor', 'wb') as fh:
    ...     fh.write(bytearray([0x01, 0x02, 0x05]))
    3
    >>> with fs.open('config/actor', 'wb') as fh:
    ...     fh.write(bytearray([0xAA, 0xBB] * 100))
    200

As we want to place the files in a folder, the folder first needs to be created.
The filesystem does not know the concept of a working directory. The working directory
is always assumed to be the root directory, therefore :code:`./config`, :code:`/config` and
:code:`config` have all the same meaning, use whatever you like the best.

A final check to see if all required files are on the filesystem before we dump the data
to a file:

.. doctest::

    >>> fs.listdir('/')
    ['config', 'hardware.txt']
    >>> fs.listdir('/config')
    ['actor', 'sensor']

Everything ok? Ok, lets go and dump the filesystem to a binary file.
This file can be written/downloaded to the actual storage.

.. doctest::

    >>> with open('fs.bin', 'wb') as fh:
    ...     fh.write(fs.context.buffer)
    16384


Inspecting a filesystem image
=============================

Sometimes it's necessary to inspect a filesystem which was previously in use
on a embedded system. Once the filesystem is available as an binary image, it's easy
to inspect the content using littlefs-python.

In this example we will inspect the image created in the last example. We check if
the actor file is still the same as when the image was written.
We start again by creating a :class:`~littlefs.LittleFS` instance. However, this
time we do not want to mount the filesystem immediateley because we need to load
the actual data into the buffer first.
After the buffer is initialized with the correct data, we can mount the filesystem.

.. doctest::

    >>> fs = LittleFS(block_size=256, block_count=64, mount=False)
    >>> with open('fs.bin', 'rb') as fh:
    ...     fs.context.buffer = bytearray(fh.read())
    >>> fs.mount()
    0

Let's see what's on the filesystem:

.. doctest::

    >>> fs.listdir('/config')
    ['actor', 'sensor']

Ok, this seems to be fine. Let's check if the `actor` file was modified:

.. doctest::

    >>> with fs.open('/config/actor', 'rb') as fh:
    ...     data = fh.read()
    >>> assert data == bytearray([0xAA, 0xBB] * 100)

Great, our memory contains the correct data!

Now it's up to you! Play around with the data, try writing and reading other files,
create directories or play around with different :code:`block_size` and :code:`block_count`
arguments.


---------------------------------------------------------

.. [1] See :func:`littlefs.lfs.format` and :func:`littlefs.lfs.mount` for further details.
.. [2] Ignore the output of the examples. These are the return values in which we are not
    interested in almost all cases.
