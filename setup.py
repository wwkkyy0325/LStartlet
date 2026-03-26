from setuptools import setup, find_packages

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="core-infrastructure-framework",
    version="1.0.0",
    author="Core Infrastructure Team",
    description="A modular, high-cohesion, low-coupling infrastructure framework for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/core-infrastructure-framework",
    packages=find_packages(exclude=["tests*", "test_reports*", "build*", "deployment*", "plugin.example_ocr_plugin", "plugin.example_ocr_plugin.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.7, <3.12",
    install_requires=requirements,
    zip_safe=False,
    include_package_data=True,
)