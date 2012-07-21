from setuptools import setup

setup(
    name='PyCalCurse',
    author='Max Brauer',
    author_email='max.brauer@inqbus.com',
    version=open('versions.txt').read(),
    packages=[],
    license='WTFPL',
    long_description=open('README.rst').read(),
    scripts=['pycalcurse.py'],
    url='https://github.com/DebVortex/pycalcurse',
    description='Useful towel-related stuff.',
    setup_requires=[
        "icalendar",
    ],
)