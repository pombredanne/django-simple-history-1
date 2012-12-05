# -*- coding: utf-8 -*-
"""setup.py: Django django-simple-history"""

from distutils.core import setup
import os

# compile the list of packages available, because distutils doesn't have an easy way to do this
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('simple_history'):
    # ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        # strip 'simple_history/' or 'simple_history\'
        prefix = dirpath[15:]
        for f in filenames:
            data_files.append(os.path.join(prefix, f))

setup(name='simple_history',
      version='1.0',
      description='Store Django model history with the ability to revert back to a '
                  'specific change at any time. This includes capturing request.user',
      author='Steven Klass',
      author_email='sklass@pivotalenergysolutions.com',
      url='https://github.com/pivotal-energy-solutions/django-simple-history',
      packages=['stdimage'],

      package_dir={'simple_history': 'simple_history'},
      packages=packages,
      package_data={'simple_history': data_files},
      classifiers=[
             'Development Status :: 2 - Pre-Alpha',
             'Environment :: Web Environment',
             'Framework :: Django',
             'Intended Audience :: Developers',
             'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
             'Operating System :: OS Independent',
             'Programming Language :: Python',
             'Topic :: Software Development',
      ],
)

setup(
    name='django-stdimage',
    version='0.2.1',
    description='Django Standarized Image Field',
    author='garcia.marc',
    author_email='garcia.marc@gmail.com',
    url='http://code.google.com/p/django-stdimage/',
    license='lgpl',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    packages=['stdimage'],
    requires=['django (>=1.0)',],
)
