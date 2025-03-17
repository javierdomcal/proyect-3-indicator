from setuptools import setup, find_packages

setup(
    name="project_3_indicator",  # Fixed typo here
    version="0.1.0",
    package_dir={"": "src"},    # Added this line
    packages=find_packages(where="src"),  # Modified this line
    install_requires=[
        'numpy',
        'pandas',
        'paramiko',
        'scp',
        'pathlib'
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A quantum chemistry calculation package",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quantum-flux",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)