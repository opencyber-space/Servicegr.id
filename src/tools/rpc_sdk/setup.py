from setuptools import setup, find_packages

setup(
    name="tools_rpc_sdk",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="SDK for registering and executing distributed tools over gRPC in Kubernetes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "grpcio>=1.50.0",
        "grpcio-tools>=1.50.0",
        "flask>=2.0.0",
        "pymongo>=4.0.0",
        "requests>=2.25.0",
        "kubernetes>=26.1.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
    include_package_data=True,
    zip_safe=False,
)
