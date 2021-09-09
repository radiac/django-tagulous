import re
from pathlib import Path

from setuptools import setup


def find_version(*paths):
    path = Path(*paths)
    content = path.read_text()
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(version=find_version("tagulous", "__init__.py"))
