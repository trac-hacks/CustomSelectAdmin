from ez_setup import use_setuptools

use_setuptools()
from setuptools import setup, find_packages

setup(name='CustomSelectAdmin',
      version='0.5',
      packages=find_packages(exclude=''),
      package_data={'CustomSelectAdmin' : ['templates/*.html']},
      author='Jimmy Theis',
      author_email='jimmy@jetheis.com',
      description='Modify custom select fields for tickets in an admin panel within Trac.',
      long_description=open('README').read()+'\n'+open('CHANGES').read(),
      url='https://svn.jetheis.com/public/CustomSelectAdmin',
      license='GPLv3',
      entry_points={'trac.plugins': ['CustomSelectAdmin = CustomSelectAdmin']},
)
