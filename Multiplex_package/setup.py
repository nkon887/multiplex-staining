from setuptools import find_packages, setup

setup(
    name='multiplex',
    packages=find_packages(),
    include_package_data=True,
    exclude_package_data={"multiplex": [".gitattributes", ".gitignore"]},
)
