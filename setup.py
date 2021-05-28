import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements_raw = fh.read()
    requirements_list = requirements_raw.split('\n')
    requirements = []
    for req in requirements_list:
        if not req.strip().startswith('#') and len(req.strip()) > 0:
            requirements.append(req)

with open("src/tfr/data/VERSION", "r") as fh:
    version = fh.read()

setuptools.setup(
    name="tesla-ce-provider-fr-tfr",
    version=version,
    author="Xavier Baro",
    author_email="xbaro@uoc.edu",
    description="TeSLA CE Face Recognition Provider",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://tesla-ce.github.io",
    project_urls={
        'Documentation': 'https://tesla-ce.github.io/provider-fr-tfr/',
        'Source': 'https://github.com/tesla-ce/provider-fr-tfr',
    },
    packages=setuptools.find_packages('src', exclude='__pycache__'),
    package_dir={'': 'src'},  # tell distutils packages are under src
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
    package_data={
        '': ['*.cfg', 'VERSION'],
        'tfr': [
            'data/*',
                    ],
    },
    include_package_data=True,
    install_requires=requirements,
)
