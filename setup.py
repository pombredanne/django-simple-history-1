# -*- coding: utf-8 -*-
"""setup.py: Django django-simple-history"""

from setuptools import find_packages, setup

setup(name='simple_history',
      version='1.0',
      description='Store Django model history with the ability to revert back to a '
                  'specific change at any time. This includes capturing request.user',
      author='Steven Klass',
      author_email='sklass@pivotalenergysolutions.com',
      url='https://github.com/pivotal-energy-solutions/django-simple-history',
      license='Apache License (2.0)',
      classifiers=[
             'Development Status :: 2 - Pre-Alpha',
             'Environment :: Web Environment',
             'Framework :: Django',
             'Intended Audience :: Developers',
             'License :: OSI Approved :: Apache Software License',
             'Operating System :: OS Independent',
             'Programming Language :: Python',
             'Topic :: Software Development',
      ],
      packages=find_packages(exclude=['tests', 'tests.*']),
      package_data={'simple_history': ['static/js/*.js', 'templates/simple_history/*.html']},
      include_package_data=True,
      requires=['django (>=1.2)',],
)