import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-tagulous",
    version = "1.0.0",
    author = "Richard Terry",
    author_email = "python@radiac.net",
    description = ("A flexible tagging application for Django"),
    license = "BSD",
    keywords = "django tag tagging",
    url = "http://radiac.net/projects/django-tagulous/",
    long_description=read('README.txt'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    
    zip_safe=True,
    packages=find_packages()
)
