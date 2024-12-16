"""Build and installation script for report_creator."""

from setuptools import find_packages, setup
from report_creator.__version__ import __version__


# Function to read the requirements.txt file
def read_requirements():
    with open("requirements.txt") as req:
        content = req.readlines()
    return [line.strip() for line in content]


setup(
    name="report_creator",
    version="1.0.33",
    author="Daren Race",
    author_email="daren.race@gmail.com",
    description="Create self-contained HTML reports from Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="python, html, reports, report, creator, generator, markdown, yaml, plot, chart, table, blog",
    url="https://github.com/darenr/report_creator",
    packages=find_packages(),
    package_data={"report_creator": ["templates/*"]},
    python_requires=">=3.9",
    maintainer="Daren Race",
    maintainer_email="daren.race@gmail.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    install_requires=read_requirements(),
    include_package_data=True,
)
