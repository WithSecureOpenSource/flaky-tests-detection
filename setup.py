from setuptools import setup, find_packages
from distutils.util import convert_path
from typing import Dict


def _read_long_description():
    with open("README.md") as readme:
        return readme.read()


DEV_REQUIRE = [
    "pytest",
    "pytest-cov",
    "black",
    "mypy",
    "python-semantic-release",
]
NAME = "flaky_tests_detection"
NAME_DASHED = NAME.replace("_", "-")

init_content: Dict[str, str] = {}
init_path = convert_path('flaky_tests_detection/__init__.py')
with open(init_path) as init_file:
    exec(init_file.read(), init_content)


setup(
    name=NAME_DASHED,
    description="Github actions plugin to check flakiness of tests by calculating fliprates.",
    long_description=_read_long_description(),
    long_description_content_type="text/markdown",
    author="Eero Kauhanen, Matvey Pashkovskiy, Alexey Vyskubov, Tatu Aalto, Joona Oikarinen",
    author_email="", # warning: check: missing meta-data: if 'author' supplied, 'author_email' must be supplied too
    url=f"https://github.com/F-Secure/{NAME_DASHED}",
    license="Apache License 2.0",
    platforms="any",
    version=init_content["__version__"],
    packages=find_packages(exclude=[f"{NAME}.tests", f"{NAME}.tests.*"]),
    entry_points={
        "console_scripts": [
            "flaky=flaky_tests_detection.check_flakes:main",
        ]
    },
    install_requires=["pandas", "junitparser", "seaborn", "matplotlib"],
    extras_require={"dev": DEV_REQUIRE},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
