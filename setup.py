import os
from os import path
from setuptools import setup, find_packages
from setuptools import Extension
import Cython
from Cython.Build import cythonize

# Opt-in stable-ABI (abi3) build: LITTLEFS_PY_LIMITED_API=3.9 builds one extension that runs on CPython 3.9
# and every later version. Unset, the extension is built for the running Python only.
LIMITED_API = os.environ.get("LITTLEFS_PY_LIMITED_API")
LIMITED_API_MACROS = []
LIMITED_API_OPTIONS = {}
if LIMITED_API:
    major, minor = (int(part) for part in LIMITED_API.split("."))
    if (major, minor) < (3, 9):
        raise SystemExit("LITTLEFS_PY_LIMITED_API must be 3.9 or later, got %s" % LIMITED_API)
    cython_version = tuple(int(part) for part in Cython.__version__.split(".")[:2])
    if cython_version < (3, 1):
        raise SystemExit("An abi3 build needs Cython 3.1 or later, found %s" % Cython.__version__)
    LIMITED_API_MACROS = [("Py_LIMITED_API", "0x%02X%02X0000" % (major, minor))]
    LIMITED_API_OPTIONS = {"bdist_wheel": {"py_limited_api": "cp%d%d" % (major, minor)}}

# Extension definition
EXTENSIONS = [
    Extension(
        "littlefs.lfs",
        ["src/littlefs/lfs.pyx", "littlefs/lfs.c", "littlefs/lfs_util.c"],
        include_dirs=["littlefs"],
        define_macros=[
            ("LFS_NO_DEBUG", "1"),
            ("LFS_NO_WARN", "1"),
            ("LFS_NO_ERROR", "1"),
            ("LFS_MULTIVERSION", "1"),
            ("LFS_NAME_MAX", "1022"),  # LittleFS limitation: must be <= 1022
            # ('LFS_YES_TRACE', '1')
        ]
        + LIMITED_API_MACROS,
        extra_compile_args=["-std=c99", "-UNDEBUG"],
        py_limited_api=bool(LIMITED_API),
    )
]


HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="littlefs-python",
    url="https://github.com/jrast/littlefs-python",
    author="Jürg Rast",
    author_email="juergr@gmail.com",
    description="A python wrapper for littlefs",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    use_scm_version=True,
    packages=find_packages("src"),
    package_data={"*": ["py.typed", "*.pyi"]},
    package_dir={"": "src"},
    zip_safe=False,
    options=LIMITED_API_OPTIONS,
    ext_modules=cythonize(EXTENSIONS, language_level=3, annotate=False, compiler_directives={"embedsignature": True}),
    entry_points={
        "console_scripts": [
            "littlefs-python = littlefs.__main__:main",
        ]
    },
    install_requires=[
        "importlib-metadata>=4.4; python_version < '3.10'",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Filesystems",
    ],
)
