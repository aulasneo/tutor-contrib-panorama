"""
Setuptools file for tutor-contrib-panorama.
"""
import io
import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def load_readme():
    """
    Load readme file.
    :return:
    """
    with io.open(os.path.join(HERE, "README.rst"), "rt", encoding="utf8") as f:
        return f.read()


def load_about():
    """
    Load about file.
    :return:
    """
    about = {}
    with io.open(
        os.path.join(HERE, "tutorpanorama", "__about__.py"),
        "rt",
        encoding="utf-8",
    ) as f:
        exec(f.read(), about)  # pylint: disable=exec-used
    return about


ABOUT = load_about()


setup(
    name="tutor-contrib-panorama",
    version=ABOUT["__version__"],
    url="https://github.com/aulasneo/tutor-contrib-panorama",
    project_urls={
        "Code": "https://github.com/aulasneo/tutor-contrib-panorama",
        "Issue tracker": "https://github.com/aulasneo/tutor-contrib-panorama/issues",
    },
    license="AGPLv3",
    author="Aulsneo",
    maintainer="Aulasneo",
    author_email="andres@aulasneo.com",
    description="Tutor plugin for Panorama Analytics",
    long_description=load_readme(),
    long_description_content_type='text/x-rst',
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=["tutor>=17.0.0,<18.0.0"],
    entry_points={
        "tutor.plugin.v1": [
            "panorama = tutorpanorama.plugin"
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
