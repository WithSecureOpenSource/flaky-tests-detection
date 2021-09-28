from setuptools import setup, find_packages
import subprocess


def _read_long_description():
    with open("README.md") as readme:
        return readme.read()


GIT_VERSION = (
    subprocess.check_output("git describe --always".split())
    .strip()
    .decode("ascii")
    .replace("v", "", 1)
)
DEV_REQUIRE = [
    "pytest",
    "pytest-cov",
    "black",
    "mypy",
    "python-semantic-release",
]
NAME = "flaky_tests_detection"
NAME_DASHED = NAME.replace("_", "-")


setup(
    name=NAME_DASHED,
    description="Github actions plugin to check flakiness of tests by calculating fliprates.",
    long_description=_read_long_description(),
    long_description_content_type="text/markdown",
    author="Eero Kauhanen, Matvey Pashkovskiy, Alexey Vyskubov",
    author_email="", # warning: check: missing meta-data: if 'author' supplied, 'author_email' must be supplied too
    url=f"https://github.com/F-Secure/{NAME_DASHED}",
    license="Apache License 2.0",
    platforms="any",
    version=GIT_VERSION,
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
