from setuptools import setup, find_packages
from codecs import open
from os import path

NAME = 'running'
REQUIRED = ["pyyaml"]

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

about = {}
with open(path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)

setup(
    name="running-ng",
    version=about["__VERSION__"],
    description='A library that helps you exercising good benchmarking methodology',
    long_description=long_description,
    url='https://github.com/caizixian/running-ng',
    author='Zixian Cai',
    author_email='u5937495@anu.edu.au',
    license='Apache',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: System :: Benchmark',
        'Programming Language :: Python :: 3',
    ],

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    entry_points={
        'console_scripts': [
            'running = running.__main__:main'
        ]
    },

    install_requires=REQUIRED,
    extras_require={},
)
