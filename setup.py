# chardet's setup.py
from distutils.core import setup
import setuptools

setup(
    name = "whatapi",
    packages = setuptools.find_packages(),
    version = "2.0",
    description = "Module to manage redacted.cd as a web service",
    author = "devilcius",
    author_email = "devilcius@gmail.com",
    license = "WOL",
    url = "https://github.com/devilcius/whatapi",
    download_url = "https://github.com/devilcius/whatapi/archive/refs/tags/v2.0.tar.gz",
    keywords = ["api", "webservice", "what.cd"],
    platforms = "Windows,Linux",
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: Repoze Public License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        ],
    long_description = ""
)