import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

reqs = [
    "regex",
    "datasets~=2.18",
    "scipy~=1.12",
    "numpy~=1.26",
    "requests~=2.31",
    "opencv-python~=4.9",
    "tesseract~=0.1",
    "pytesseract~=0.3",
    "appium-python-client~=2.9",
]

extras_require = {
    "test": ["pytest~=8.0", "pytest-cov~=5.0", "coverage-badge~=1.0"],
    "hook": ["pre-commit~=3.0"],
    "lint": ["ruff~=0.2"],
    "docs": ["mkdocs-material~=9.0", "mkdocstrings[python]~=0.18", "mike~=2.0"],
}
extras_require["all"] = sum(extras_require.values(), [])
extras_require["dev"] = (
    extras_require["test"] + extras_require["hook"] + extras_require["lint"] + extras_require["docs"]
)

setuptools.setup(
    name="kebbie",
    version="0.1.3",
    author="Nicolas REMOND",
    author_email="nicolas.remond@thingthing.co",
    description="A small framework to test and compare mobile keyboards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FleksySDK/kebbie",
    packages=setuptools.find_packages(),
    package_data={"": ["layouts/*.json"]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=reqs,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "kebbie=kebbie.cmd:cli",
        ],
    },
)
