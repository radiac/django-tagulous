import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-tagulous",
    version = "0.7.0",
    author = "Richard Terry",
    author_email = "code@radiac.net",
    description = ("A flexible tagging application for Django"),
    license = "BSD",
    keywords = "django tag tagging",
    url = "http://radiac.net/projects/django-tagulous/",
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    extras_require = {
        'dev':  ['jasmine'],
        'i18n': ['unidecode'],
    },
    zip_safe=True,
    packages=find_packages()
)
