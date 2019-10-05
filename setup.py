from setuptools import setup, find_packages
from setuptools import Extension
from Cython.Build import cythonize

# Extension definition
EXTENSIONS = [
    Extension("littlefs.lfs", ["src/littlefs/lfs.pyx", 'littlefs/lfs.c', 'littlefs/lfs_util.c'],
              include_dirs=['littlefs'],
              define_macros=[
                  ('LFS_NO_DEBUG', '1'),
                  ('LFS_NO_WARN', '1'),
                  ('LFS_NO_ERROR', '1'),
                # ('LFS_YES_TRACE', '1')
              ],
              extra_compile_args=['-std=c99']
    )
]

setup_requires = [
    'setuptools_scm',
]

setup(
    name='littlefs-python',
    url='https://github.com/jrast/littlefs-python',
    author='Jürg Rast',
    author_email='juergr@gmail.com',
    use_scm_version=True,
    setup_requires=setup_requires,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    ext_modules=cythonize(EXTENSIONS, language_level=3, annotate=False, 
                          compiler_directives={'embedsignature': True}),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Filesystems'
    ]
)
