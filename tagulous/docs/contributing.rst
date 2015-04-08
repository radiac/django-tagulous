.. _contributing:

Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues
and project `roadmap <CHANGES>`_ to see what needs work.

When submitting UI changes, please aim to support the latest versions of
Chrome, Firefox and Internet Explorer through progressive enhancement - old
browsers must still be able to access all functionality.


Testing
-------

It is greatly appreciated when contributions come with unit tests.

Run the python tests using django's test framework::
    ./manage.py test tagulous

Run the javascript tests using Jasmine::
    pip install jasmine
    cd tagulous/tests
    jasmine
    # open http://127.0.0.1:8888/ in your browser
