# -*- coding: utf-8 -*-
"""setup.py: Django django-simple-history"""

from setuptools import find_packages, setup
from simple_history import __name__, __version__, __author__

base_url = 'https://github.com/pivotal-energy-solutions/django-simple-history'

setup(name=__name__,
      version=__version__,
      description=open('{0}/README.rst'.format(__name__)).read(),
      author=__author__,
      author_email='sklass@pivotalenergysolutions.com',
      url=base_url,
      download_url='{0}/archive/{1}-{1}.tar.gz'.format(base_url, __name__, __version__),
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
      requires=['django (>=1.2)', ],
)
