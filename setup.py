import setuptools
from codecs import open
from os import path

NAME = 'running'
REQUIRED = ["pyyaml", "zulip"]

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

about = {}
with open(path.join(here, "src", NAME, '__version__.py')) as f:
    exec(f.read(), about)

setuptools.setup(
    name="running-ng",
    version=about["__VERSION__"],
    description='Running: Next Generation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anupli/running-ng",
    project_urls={
        "Bug Tracker": "https://github.com/anupli/running-ng/issues",
    },
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

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    package_data={
        "running": ["data/**/*.yml"],
    },
    include_package_data=True,
    python_requires=">=3.6",

    entry_points={
        'console_scripts': [
            'running = running.__main__:main'
        ]
    },

    install_requires=REQUIRED,
    extras_require={},
)
