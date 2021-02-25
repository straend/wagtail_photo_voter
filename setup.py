import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wagtail_photo_voter",
    version="0.9.10",
    author="Tomas Strand",
    author_email="wagtail@tomas.fik1.net",
    description="A Wagtail module for creating Photo competitions with voting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/straend/wagtail_photo_voter",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Wagtail",
    ],
    install_requires=[
        'Django>=3.1',
        'wagtail>=2.12',
        'django-bootstrap4',
        'django-exiffield'
    ],
    python_requires='>=3.8',
)
