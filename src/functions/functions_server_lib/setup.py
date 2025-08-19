from setuptools import setup, find_packages

setup(
    name="agent_functions",
    version="0.1.0",
    author="Prasanna HN",
    author_email="prasanna@opencyberspace.org",
    description="agent_functions SDK for building functions",
    long_description="",
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.20.0",
        "websockets",
        "flask"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "flake8>=3.9.0",
            "websockets"
        ],
    },
    entry_points={
    },
)
