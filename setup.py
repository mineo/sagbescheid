#!/usr/bin/env python2
from setuptools import setup


setup(name="sagbescheid",
      author="Wieland Hoffmann",
      author_email="themineo@gmail.com",
      packages=["sagbescheid", "sagbescheid.notifiers"],
      package_dir={"sagbescheid": "sagbescheid"},
      download_url=["https://github.com/mineo/sagbescheid/tarball/master"],
      url=["http://github.com/mineo/sagbescheid"],
      license="MIT",
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: MIT License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 2.7"],
      description="",
      long_description=open("README.rst").read(),
      install_requires=["Twisted[tls]>=15.2.0",
                        "txdbus==1.0.11",
                        "zope.interface==4.1.2",
                        "enum34==1.0.4"],
      setup_requires=["setuptools_scm"],
      use_scm_version={"write_to": "sagbescheid/version.py"},
      extras_require={
          'docs': ['sphinx', 'sphinxcontrib-autoprogram']
          }
      )
