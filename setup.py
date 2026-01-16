"""Build and installation script for report_creator."""

from setuptools import find_packages, setup

from report_creator.__version__ import __version__


# Function to read the requirements.txt file
def read_requirements():
    with open("requirements.txt") as req:
        content = req.readlines()
    return [line.strip() for line in content]


def read_readme():
    with open("README.md") as readme_file:
        return readme_file.read()


setup(
    name="report_creator",
    version=__version__,
    author="Daren Race",
    author_email="daren.race@gmail.com",
    description="Create self-contained HTML reports from Python.",
    long_description=read_readme(),
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
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    install_requires=read_requirements(),
    include_package_data=True,
)
