from setuptools import setup

setup(
    name='chloop',
    version='0.1.0',
    description='A Redis-backed REPL that saves command history, output, & errors',
    author='Ken',
    author_email='kenjyco@gmail.com',
    url='https://github.com/kenjyco/chloop',
    packages=['chloop'],
    install_requires=[
        'click>=5.0,<6.0',
        'ipdb>=0.8,<1.0',
        'redis-helper',
    ],
)
