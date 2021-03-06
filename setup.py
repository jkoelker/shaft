from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='shaft',
      version=version,
      description="Minecraft Shaft",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Jason K\xc3\xb6lker',
      author_email='jason@koelker.net',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']) + \
               ['twisted.plugins'],
      package_data = {'twisted': ['plugins/shaft_plugin.py'],},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'twisted <= 10.2',
          'pycrypto',
          'pyasn1',
          'simplejson',

      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      data_files=[('/etc/init.d', ['utils/shaft'])],
      )
