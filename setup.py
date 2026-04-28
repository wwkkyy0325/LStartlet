from setuptools import setup, find_packages

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="LStartlet",
    use_scm_version=True,
    author="wwkkyy0325",
    author_email="1074446976@qq.com",
    description=(
        "A lightweight Python framework with dependency injection, "
        "event system, lifecycle management, and configuration management"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wwkkyy0325/LStartlet",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Pytest",
    ],
    python_requires=">=3.9, <3.14",
    install_requires=requirements,
    zip_safe=False,
    include_package_data=True,
    keywords="framework dependency-injection event-system lifecycle management configuration",
    project_urls={
        "Bug Reports": "https://github.com/wwkkyy0325/LStartlet/issues",
        "Source": "https://github.com/wwkkyy0325/LStartlet",
        "Documentation": "https://github.com/wwkkyy0325/LStartlet#readme",
    },
)