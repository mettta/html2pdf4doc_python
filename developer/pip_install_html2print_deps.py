import importlib.metadata as importlib_metadata
import os
import subprocess
import sys
import tempfile

import toml
from packaging.requirements import Requirement


class PackageNotFound(Exception):
    pass


class PackageVersionConflict(Exception):
    pass


# A simplified version inspired by:
# https://github.com/HansBug/hbutils/blob/37879186c489bced2791309c43d131f1703b7bd4/hbutils/system/python/package.py#L171
def check_if_package_installed(package_name: str):
    requirement: Requirement = Requirement(package_name)
    try:
        version = importlib_metadata.distribution(requirement.name).version
    except importlib_metadata.PackageNotFoundError:
        raise PackageNotFound(requirement) from None
    if not requirement.specifier.contains(version):
        raise PackageVersionConflict(version)


print(  # noqa: T201
    "pip_install_html2print_deps.py: "
    "checking if the current Python environment has all packages installed"
    ".",
    flush=True,
)

pyproject_content = toml.load("pyproject.toml")


# The development dependencies are ignored, because they are managed in tox.ini.
dependencies = pyproject_content["project"]["dependencies"]

needs_installation = False

for dependency in dependencies:
    try:
        check_if_package_installed(dependency)
    except PackageNotFound:
        print(  # noqa: T201
            f"pip_install_html2print_deps.py: "
            f"Package is not installed: '{dependency}'.",
            flush=True,
        )
        needs_installation = True
        break
    except PackageVersionConflict as exception_:
        print(  # noqa: T201
            (
                f"pip_install_html2print_deps.py: version conflict between "
                f"html2print's requirement '{dependency}' "
                f"and the already installed package: "
                f"{exception_.args[0]}."
            ),
            flush=True,
        )
        needs_installation = True
        break

if not needs_installation:
    print(  # noqa: T201
        "pip_install_html2print_deps.py: all packages seem to be installed.",
        flush=True,
    )
    sys.exit(0)

print(  # noqa: T201
    "pip_install_html2print_deps.py: will install packages.", flush=True
)

all_packages = "\n".join(dependencies) + "\n"

with tempfile.TemporaryDirectory() as tmp_dir:
    with open(
        os.path.join(tmp_dir, "requirements.txt"), "w", encoding="utf8"
    ) as tmp_requirements_txt_file:
        tmp_requirements_txt_file.write(all_packages)

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        tmp_requirements_txt_file.name,
    ]

    result = subprocess.run(command, check=True, encoding="utf8")
    print(  # noqa: T201
        f"'pip install' command exited with: {result.returncode}", flush=True
    )
