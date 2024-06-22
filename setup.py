import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="firstrade",
    version="0.0.19",
    author="MaxxRK",
    author_email="maxxrk@pm.me",
    description="An unofficial API for Firstrade",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/MaxxRK/firstrade-api",
    download_url="https://github.com/MaxxRK/firstrade-api/archive/refs/tags/0019.tar.gz",
    keywords=["FIRSTRADE", "API"],
    install_requires=["requests", "beautifulsoup4", "lxml"],
    packages=["firstrade"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
