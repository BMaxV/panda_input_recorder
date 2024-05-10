import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "panda_input_data_recorder",#module name
    version = "0.5",
    author = "Bruno Maximilian Voß",
    author_email = "bruno.m.voss@gmail.com",
    description = ("example for how to record data in panda3d and play it back"),
    
    license = "MIT",
    keywords = "panda3d",
   
    packages=['input_data_recorder'],#foldername
    
)
