"""
示例OCR插件的 setup.py 配置
"""

from setuptools import setup, find_packages

setup(
    name="example-ocr-plugin",
    version="1.0.0",
    description="Example OCR Plugin demonstrating all plugin system features",
    author="Example Author",
    author_email="author@example.com",
    packages=find_packages(),
    package_data={
        '': ['plugin.json'],  # 包含根目录的 plugin.json
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "pillow>=8.0.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)