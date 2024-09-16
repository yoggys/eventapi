from pathlib import Path

from setuptools import find_packages, setup

cwd = Path(__file__).parent
long_description = (cwd / "README.md").read_text()

setup(
    name="eventapi",
    version="1.1.2",
    author="yoggys",
    author_email="yoggies@yoggies.dev",
    description="Wrapper for 7TV EventAPI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yoggys/eventapi",
    packages=find_packages(),
    install_requires=[
        "websockets ~= 12.0",
        "typing_extensions ~= 4.12.2",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=[
        "python",
        "7tv",
        "eventapi",
        "7tvapi",
        "7tveventapi",
        "async",
        "asyncio",
        "wrapper",
    ],
)
