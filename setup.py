"""Build and installation script for report_creator."""

# standard libs
import re
from pathlib import Path

from setuptools import find_packages, setup

# get long description from README.rst
with open("README.md") as f:
    long_description = f.read()


# include necessary deopendencies
def get_install_requires() -> list[str]:
    """Returns requirements.txt parsed to a list"""
    fname = Path(__file__).parent / "requirements.txt"
    targets = []
    if fname.exists():
        with open(fname) as f:
            targets = f.read().splitlines()

    return targets


# get package metadata by parsing __meta__ module
with open("report_creator/__meta__.py") as source:
    content = source.read().strip()
    metadata = {
        key: re.search(key + r'\s*=\s*[\'"]([^\'"]*)[\'"]', content).group(1)
        for key in [
            "__version__",
            "__authors__",
            "__contact__",
            "__description__",
            "__license__",
        ]
    }


setup(
    name="report_creator",
    version=metadata["__version__"],
    author=metadata["__authors__"],
    author_email=metadata["__contact__"],
    description=metadata["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=metadata["__license__"],
    keywords="python, html, reports, report, creator, generator, markdown, yaml, plot, chart, table, blog",
    url="https://github.com/darenr/report_creator",
    packages=find_packages(),
    include_package_data=True,
    package_data={"report_creator": ["templates/*"]},
    install_requires=get_install_requires(),
    maintainer="Daren Race",
    maintainer_email="daren.race@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    license_files=("LICENSE",),
)
