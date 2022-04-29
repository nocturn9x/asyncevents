# Copyright (C) 2021 nocturn9x
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import setuptools

if __name__ == "__main__":
    with open("README.md") as readme:
        long_description = readme.read()
    setuptools.setup(
        name="asyncevents",
        version="0.1",
        author="Nocturn9x",
        author_email="nocturn9x@nocturn9x.space",
        description="Asynchronous event handling for modern Python",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/nocturn9x/asyncevents",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: Apache Software License",
        ],
        python_requires=">=3.6",
    )
