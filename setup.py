from setuptools import setup, find_packages

setup(
    name='PyCalCurse',
    author='Max Brauer',
    author_email='max.brauer@inqbus.com',
    version=open('versions.txt').read(),
    packages=find_packages(),
    license='WTFPL',
    long_description=open('README.rst').read(),
    scripts=['pycalcurse.py'],
    url='https://github.com/DebVortex/pycalcurse',
    description='Useful towel-related stuff.',
    install_requires=[
        "icalendar",
    ],
)