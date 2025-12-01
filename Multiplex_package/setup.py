from setuptools import find_packages, setup

setup(
    name='multiplex',
    version='0.1.0',
    author='Natalja Amiridze',
    author_email='natalja.amiridze@charite.de',
    packages=find_packages(),
    package_data={
        "multiplex": ["tests/*", "tests/**/*.py"],
        "multiplex.assets": ["*.png"],
    },

    url='https://github.com/nkon887/multiplex-staining',
    license='LICENSE',
    description='multiplex package that creates a gui to execute the steps of the multiplex pipeline',
    long_description=open('README.md').read(),
    python_requires='>=3.6',
    install_requires=["pytest",
                      "gdown",
                      "pandas",
                      ],
    include_package_data=True,
    exclude_package_data={"multiplex": [".gitattributes", ".gitignore"]},
)
