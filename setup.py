from setuptools import setup, find_packages

with open("requirements.txt", encoding="utf-8") as f:
    required = f.read().splitlines()

setup(
    name="ai-paper-reader",
    version="1.0.0",
    description="Based on AI paper reading assistant",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=required,
    entry_points={
        "console_scripts": [
            "paper-reader=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
