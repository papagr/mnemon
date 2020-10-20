import os

from pip._internal.req import parse_requirements
from pip._internal.network.session import PipSession

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.md')).read()

requirements = parse_requirements(os.path.join(HERE, 'requirements.txt'),
                                  session=PipSession())
requires = [str(req.requirement) for req in requirements]

setup(name='Mnemon',
      version='0.6.0',
      description='Mnemon',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Nikolaos Papagrigoriou',
      author_email='nikolaos@papagrigoriou.com',
      url='https://mnemon.eu',
      keywords='web pyramid pylons mnemon',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="mnemon",
      entry_points="""\
      [paste.app_factory]
      main = mnemon:main
      [console_scripts]
      init_mnemon_mongodb = mnemon.persistence.scripts:init_mongodb
      """,
      )
