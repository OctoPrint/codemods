import io

from setuptools import find_packages, setup

with io.open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="octoprint_codemods",
    version="0.2.1",
    description="libcst based tooling for running various conversions on OctoPrint's source",
    url="https://github.com/OctoPrint/codemods",
    packages=find_packages(exclude=["tests"]),
    install_requires=["libcst"],
    author="Gina Häußge",
    author_email="gina@octoprint.org",
    license="MIT License",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={
        "console_scripts": [
            "codemod_dict_to_literal=octoprint_codemods.dict_to_literal:main",
            "codemod_set_to_literal=octoprint_codemods.set_to_literal:main",
            "codemod_not_in=octoprint_codemods.not_in:main",
            "codemod_remove_future_imports=octoprint_codemods.remove_future_imports:main",
            "codemod_remove_builtins_imports=octoprint_codemods.remove_builtins_imports:main",
            "codemod_detect_past_builtins_imports=octoprint_codemods.detect_past_builtins_imports:main",
            "codemod_py3_class_inheritance=octoprint_codemods.py3_class_inheritance:main",
            "codemod_oserror_merge=octoprint_codemods.oserror_merge:main",
        ]
    },
)
