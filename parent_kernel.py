#!/usr/bin/python
#
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Does some intialization that must happen before "swift_kernel.py" runs, and
# then launches "swift_kernel.py" as a subprocess.

import os
import signal
import subprocess
import sys
import tempfile

# Determine the directory where user-installed packages will reside.
# Current locations include:
#   . <virtualenv_base>/swift-env, when using a virtualenv environment.
#     For example, if the virtualenv resides in ~/projects/myproject/env,
#     the location will be ~/projects/myproject/swift-env.
#     <virtualenv_base> is the directory that in turn contains the virtual environment.
#   . <conda_env>/swift-env, when using Anaconda.
#     For example, if the conda environment is called 'test', the location
#     will look like ~/anaconda3/envs/test/swift-env.
#   . ~/swift-env, if a system-wide Python is used or no virtual environment
#     container was detected. No attempt at separating Python versions
#     is performed.
def get_swift_packages_location():
    # Guess type of environment and derive an appropriate dir accordingly
    env_name = 'swift-env'

    # Anaconda
    if 'CONDA_PREFIX' in os.environ:
        return os.path.join(os.environ['CONDA_PREFIX'], env_name)

    # virtualenv, Python 3
    if hasattr(sys, 'base_prefix'):
        if sys.prefix != sys.base_prefix:
            return os.path.join(os.path.dirname(sys.prefix), env_name)

    # ToDo: verify whether Python 2 running in virtualenv exposes base_prefix

    # Unknown or system-wide
    return os.path.join(os.path.expanduser('~'), env_name)

# The args to launch "swift_kernel.py" are the same as the args we received,
# except with "parent_kernel.py" replaced with "swift_kernel.py".
args = [
    sys.executable,
    os.path.join(os.path.dirname(sys.argv[0]), 'swift_kernel.py')
]
args += sys.argv[1:]

# Determine a directory for package installation. This must happen in the
# parent process because we need to set the SWIFT_IMPORT_SEARCH_PATH
# environment in the child to tell LLDB where module files go.
package_install_base = get_swift_packages_location()
swift_import_search_path = os.path.join(package_install_base,
                                        'modules')
os.makedirs(swift_import_search_path, exist_ok=True)

print('Using Swift packages directory:', package_install_base )

# Launch "swift_kernel.py".
process = subprocess.Popen(
        args, env=dict(os.environ,
                       SWIFT_IMPORT_SEARCH_PATH=swift_import_search_path))

# Forward SIGINT to the subprocess so that it can handle interrupt requests
# from Jupyter. 
def handle_sigint(sig, frame):
    process.send_signal(signal.SIGINT)
signal.signal(signal.SIGINT, handle_sigint)

process.wait()
