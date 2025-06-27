from setuptools import setup, find_packages

setup(
    name='ultibot_inversiones',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
)