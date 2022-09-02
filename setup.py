import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="w3pyconnect",
    version="0.3.0",
    author="Edoardo Fullin",
    author_email="edoardo.fullin@outlook.com",
    description="Wind3 API Wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edofullin/w3pyconnect",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)