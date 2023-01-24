from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Python package for interacting & fetching somtoday\'s data.'

with open("./README.md", "r")as file:
        data = file.read()
# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="somtodaydotpy", 
        version=VERSION,
        long_description=data,
        
        author="luxkatana/TheTrojanHorse",
        author_email="taseen.bibi@gmail.com",
        description=DESCRIPTION,
        packages=find_packages(),
        install_requires=["requests", "httpx"], # add any additional packages that 
        
        
        
        
)