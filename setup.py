from setuptools import setup, find_packages


with open('README.rst', 'r') as fp:
    long_description = fp.read()

setup(
    name='chloop',
    version='0.2.21',
    description='A Redis-backed REPL that saves command history, output, & errors',
    long_description=long_description,
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/chloop',
    download_url='https://github.com/kenjyco/chloop/tarball/v0.2.21',
    packages=find_packages(),
    install_requires=[
        'bg-helper',
        'click>=6.0',
        'fs-helper',
        'redis-helper',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
    ],
    keywords=['repl', 'redis', 'command', 'history']
)
