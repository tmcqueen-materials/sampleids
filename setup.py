import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
  name="sampleids",
  version="0.0.2dev0",
  license="GNU GPLv2",
  author="Tyrel M. McQueen",
  author_email="tmcqueen-pypi@demoivre.com",
  description="Uniform Sample Identifiers Parser",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/tmcqueen-materials/sampleids",
  packages=setuptools.find_packages(),
  python_requires='>=3.4',
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "Operating System :: OS Independent",
  ],
)
