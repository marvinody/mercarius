import setuptools

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='mercarius',
    version='1.0.1',
    author='marvinody',
    author_email='manny@pypi.sadpanda.moe',
    description='mercari-us api-like wrapper',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/marvinody/mercari-us/',
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ]
)
