from setuptools import find_packages, setup

setup(
    name="getbetter",
    version="0.1.0",
    packages=[*find_packages(exclude=["tests", "tests.*"])],
    entry_points={
        "console_scripts": [
            "gallerize = getbetter.gallerize:main",
        ]
    },
    include_package_data=True,
)
