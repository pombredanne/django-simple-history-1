# -*- coding: utf-8 -*-
"""setup.py: Django django-simple-history"""

from distutils.core import setup

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
      packages=['simple_history'],
      requires=['django (>=1.2)',],
)