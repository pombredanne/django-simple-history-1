# -*- coding: utf-8 -*-
"""setup.py: Django django-simple-history"""

from distutils.core import setup
import os


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
_dir = 'simple_history'

for dirpath, dirnames, filenames in os.walk(_dir):
    # Ignore PEP 3147 cache dirs and those whose names start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.') or dirname == '__pycache__':
            del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])


setup(name='simple_history',
      version='1.0',
      description='Store Django model history with the ability to revert back to a '
                  'specific change at any time. This includes capturing request.user',
      author='Steven Klass',
      author_email='sklass@pivotalenergysolutions.com',
      url='https://github.com/pivotal-energy-solutions/django-simple-history',
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
      packages=packages,
      data_files=data_files,
      requires=['django (>=1.2)',],
)