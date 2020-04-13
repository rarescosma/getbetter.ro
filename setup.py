from setuptools import find_packages, setup

setup(
    name="gb",
    version="0.0.1",
    packages=[*find_packages(exclude=["tests", "tests.*"])],
    include_package_data=True,
)
