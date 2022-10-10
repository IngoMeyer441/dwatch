import os
import runpy
from typing import Optional, cast

from setuptools import find_packages, setup


def get_version_from_pyfile(version_file: str = "dwatch/_version.py") -> str:
    file_globals = runpy.run_path(version_file)
    return cast(str, file_globals["__version__"])


def get_long_description_from_readme(readme_filename: str = "README.md") -> Optional[str]:
    long_description = None
    if os.path.isfile(readme_filename):
        with open(readme_filename, "r", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
    return long_description


version = get_version_from_pyfile()
long_description = get_long_description_from_readme()

setup(
    name="dwatch",
    version=version,
    packages=find_packages(),
    python_requires="~=3.6",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "dwatch = dwatch.cli:main",
        ]
    },
    author="Ingo Meyer",
    author_email="i.meyer@fz-juelich.de",
    description="A tool to watch command output for differences and send notifications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/IngoMeyer441/dwatch",
    keywords=["administration", "monitoring"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)
