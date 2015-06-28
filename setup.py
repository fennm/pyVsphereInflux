from setuptools import setup, find_packages
from glob import glob

setup(name='pyVsphereInflux',
      version='0.1',
      description='A library and supporting script for pulling data from vSphere and inserting it into InfluxDB',
      scripts=glob('bin/*'),
      packages=find_packages(),
      install_requires=[
        'pyvmomi==5.5.0.2014.1.1',
        'influxdb==2.6.0',
      ])
      
# vim: et:ai:sw=4:ts=4
