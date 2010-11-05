# chardet's setup.py
from distutils.core import setup

setup(
    name = "whatapi",
    packages = ['.'],
    version = "0.1",
    description = "Module to manage what.cd as a web service",
    author = "devilcius",
    author_email = "devilcius@gmail.com",
    licence = "WOL",
    url = "http://predatum.com",
    download_url = "http://predatum.com/whatapi-lastest.tgz",
    keywords = ["api", "webservice", "what.cd"],
    platform = "Windows,Linux",
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