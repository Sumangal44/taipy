# Copyright 2021-2024 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

"""The setup script for taipy-core package"""

import json
from pathlib import Path

from setuptools import find_packages, setup

root_folder = Path(__file__).parent

package_desc = Path(root_folder / "package_desc.md").read_text("UTF-8")

version_path = "taipy/core/version.json"

setup_requirements = Path("taipy/core/setup.requirements.txt")

with open(version_path) as version_file:
    version = json.load(version_file)
    version_string = f'{version.get("major", 0)}.{version.get("minor", 0)}.{version.get("patch", 0)}'
    if vext := version.get("ext"):
        version_string = f"{version_string}.{vext}"

requirements = [r for r in (setup_requirements).read_text("UTF-8").splitlines() if r]

test_requirements = ["pytest>=3.8"]

extras_require = {
    "fastparquet": ["fastparquet==2022.11.0"],
    "mssql": ["pyodbc>=4,<4.1"],
    "mysql": ["pymysql>1,<1.1"],
    "postgresql": ["psycopg2>2.9,<2.10"],
}

setup(
    author="Avaiga",
    author_email="dev@taipy.io",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
    ],
    description="A Python library to build powerful and customized data-driven back-end applications.",
    install_requires=requirements,
    long_description=package_desc,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
    keywords="taipy-core",
    name="taipy-core",
    packages=find_packages(where=root_folder, include=["taipy", "taipy.core", "taipy.core.*"]),
    include_package_data=True,
    test_suite="tests",
    tests_require=test_requirements,
    version=version_string,
    zip_safe=False,
    extras_require=extras_require,
    project_urls={
        "Homepage": "https://www.taipy.io",
        "Documentation": "https://docs.taipy.io",
        "Source": "https://github.com/Avaiga/taipy",
        "Download": "https://pypi.org/project/taipy/#files",
        "Tracker": "https://github.com/Avaiga/taipy/issues",
        "Security": "https://github.com/Avaiga/taipy?tab=security-ov-file#readme",
        f"Release notes": "https://docs.taipy.io/en/release-{version_string}/relnotes/",
    },
)
