'''
setup.py for installing this package do python3 setup.py install.
'''
from setuptools import setup, find_packages

VERSION = '0.0.3'
DESCRIPTION = 'Python package for interacting & fetching somtoday\'s data.'

with open("./README.md", "r", encoding="utf-8")as file:
    data = file.read()
setup(
        name="somtodaypython",
        version=VERSION,
        long_description_content_type="text/markdown",
        long_description=data,
        author="luxkatana/TheTrojanHorse",
        author_email="taseen.bibi@gmail.com",
        description=DESCRIPTION,
        packages=find_packages(),
        install_requires=["requests", "httpx"], # add any additional packages that
        url="https://github.com/luxkatana/somtodayapi_python",
)
