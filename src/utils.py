import os
import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from version import VERSION
from typing import List

import mypy.stubgen as stubgen
import sys


log = logging.getLogger(__name__)

STUB_FOLDER = "./all-stubs"


def clean_version(version: str, build: bool = False):
    "omit the commit hash from the git tag"
    # 'v1.13-103-gb137d064e' --> 'v1.13-103'
    nibbles = version.split("-")
    if len(nibbles) == 1:
        return version
    elif build and build != "dirty":
        return "-".join(version.split("-")[0:-1])
    else:
        return "-".join((version.split("-")[0], "N"))


def stubfolder(path: str) -> str:
    "return path in the stub folder"
    return "{}/{}".format(STUB_FOLDER, path)


def flat_version(version: str, keep_v: bool = False):
    "Turn version from 'v1.2.3' into '1_2_3' to be used in filename"
    version = version.strip().replace(".", "_")
    if not keep_v:
        version = version.lstrip("v")
    return version


def cleanup(modules_folder: Path):
    "Q&D cleanup"
    # for some reason (?) the umqtt simple.pyi and robust.pyi are created twice
    #  - modules_root folder ( simple.pyi and robust.pyi) - NOT OK
    #       - umqtt folder (simple.py & pyi and robust.py & pyi) OK
    #  similar for mpy 1.9x - 1.11
    #       - core.pyi          - uasyncio\core.py'
    #       - urequests.pyi     - urllib\urequest.py'
    # Mpy 1.13+
    #       - uasyncio.pyi      -uasyncio\__init__.py

    # todo - Add check for source folder
    for file_name in (
        "simple.pyi",
        "robust.pyi",
        "core.pyi",
        "urequest.pyi",
        "uasyncio.pyi",
    ):
        f = Path.joinpath(modules_folder, file_name)
        if f.exists():
            try:
                print(" - removing {}".format(f))
                f.unlink()
            except OSError:
                log.error(" * Unable to remove extranous stub {}".format(f))
                pass


def generate_pyi_from_file(file: Path) -> bool:
    """Generate a .pyi stubfile from a single .py module using mypy/stubgen"""
    # if 0:
    #     cmd = "stubgen {0} --output {1} --include-private --ignore-errors".format(file, file.parent)
    #     print(" >stubgen on {0}".format(file))
    #     result = os.system(cmd)
    #     return result == 0
    sg_opt = stubgen.Options(
        pyversion=(3, 5),
        no_import=False,
        include_private=True,
        doc_dir="",
        search_path=[],
        interpreter=sys.executable,
        parse_only=False,
        ignore_errors=True,
        modules=[],
        packages=[],
        files=[],
        output_dir="",
        verbose=True,
        quiet=False,
        export_less=False,
    )

    sg_opt.files = [str(file)]
    sg_opt.output_dir = str(file.parent)
    try:
        stubgen.generate_stubs(sg_opt)
        return True
    except BaseException:
        return False


def generate_pyi_files(modules_folder: Path) -> bool:
    """generate typeshed files for all scripts in a folder using mypy/stubgen"""
    # stubgen cannot process folders with duplicate modules ( ie v1.14 and v1.15 )
    py_files: List[Path]
    pyi_files: List[Path]
    modlist = list(modules_folder.glob("**/modules.json"))
    if len(modlist) <= 1:
        ## generate fyi files for folder
        # clean before to clean any old stuff
        cleanup(modules_folder)

        print("running stubgen on {0}".format(modules_folder))
        cmd = "stubgen {0} --output {0} --include-private --ignore-errors".format(modules_folder)
        result = os.system(cmd)
        # Check on error
        if result != 0:
            # in case of failure then Plan B
            # - run stubgen on each *.py
            print("Failure on folder, attempt to stub per file.py")
            py_files = List(modules_folder.glob("**/*.py"))
            for py in py_files:
                generate_pyi_from_file(py)
                # todo: report failures

def cleanup(modules_folder: Path):
    "Q&D cleanup"
    # for some reason (?) the umqtt simple.pyi and robust.pyi are created twice
    #  - modules_root folder ( simple.pyi and robust.pyi) - NOT OK
    #       - umqtt folder (simple.py & pyi and robust.py & pyi) OK
    #  similar for mpy 1.9x - 1.11
    #       - core.pyi          - uasyncio\core.py'
    #       - urequests.pyi     - urllib\urequest.py'
    # Mpy 1.13+
    #       - uasyncio.pyi      -uasyncio\__init__.py

    # todo - Add check for source folder
    for file_name in (
        "simple.pyi",
        "robust.pyi",
        "core.pyi",
        "urequest.pyi",
        "uasyncio.pyi",
    ):
        f = Path.joinpath(modules_folder, file_name)
        if f.exists():
            try:
                print(" - removing {}".format(f))
                f.unlink()
            except OSError:
                log.error(" * Unable to remove extranous stub {}".format(f))


def generate_pyi_from_file(file: Path) -> bool:
    """Generate a .pyi stubfile from a single .py module using mypy/stubgen"""

    sg_opt = stubgen.Options(
        pyversion=(3, 5),
        no_import=False,
        include_private=True,
        doc_dir="",
        search_path=[],
        interpreter=sys.executable,
        parse_only=False,
        ignore_errors=True,
        modules=[],
        packages=[],
        files=[],
        output_dir="",
        verbose=True,
        quiet=False,
        export_less=False,
    )

    sg_opt.files = [str(file)]
    sg_opt.output_dir = str(file.parent)
    try:
        stubgen.generate_stubs(sg_opt)
        return True
    except Exception as e:
        print(e)
        return False


def generate_pyi_files(modules_folder: Path) -> bool:
    """generate typeshed files for all scripts in a folder using mypy/stubgen"""
    # stubgen cannot process folders with duplicate modules ( ie v1.14 and v1.15 )

    modlist = list(modules_folder.glob("**/modules.json"))
    if len(modlist) > 1:
        # try to process each module seperatlely
        r = True
        for mod_manifest in modlist:
            ## generate fyi files for folder
            r = r and generate_pyi_files(mod_manifest.parent)
        return r
    else:  # one or less module manifests
        ## generate fyi files for folder
        # clean before to clean any old stuff
        cleanup(modules_folder)

        print("running stubgen on {0}".format(modules_folder))
        cmd = "stubgen {0} --output {0} --include-private --ignore-errors".format(modules_folder)
        result = os.system(cmd)
        # Check on error
        if result != 0:
            # in case of failure ( duplicate module in subfolder) then Plan B
            # - run stubgen on each *.py
            print("Failure on folder, attempt to stub per file.py")
            py_files = modules_folder.glob("**/*.py")
            for py in py_files:
                generate_pyi_from_file(py)
                # todo: report failures by adding to module manifest

        # for py missing pyi:
        py_files = list(modules_folder.rglob("*.py"))
        pyi_files = list(modules_folder.rglob("*.pyi"))

        for pyi in pyi_files:
            # remove all py files that have been stubbed successfully from the list
            try:
                py_files.remove(pyi.with_suffix(".py"))
            except ValueError:
                pass
        # now stub the rest
        # note in some cases this will try a file twice
        for py in py_files:
            generate_pyi_from_file(py)
            # todo: report failures by adding to module manifest

        # and clean after to only check-in good stuff
        cleanup(modules_folder)
        return True
    #     ##
    # for mod_manifest in modlist:
    #     ## generate fyi files for folder
    #     generate_pyi_files(mod_manifest.parent)

    #     # todo: collect and report results
    # return True


def manifest(
    family=None,
    machine=None,
    port=None,
    platform=None,
    sysname=None,
    nodename=None,
    version=None,
    release=None,
    firmware=None,
) -> dict:

    "create a new empty manifest dict"
    if family is None:
        family = "micropython"  # family
    if machine is None:
        machine = family  # family

    if port is None:
        port = "common"  # family
    if platform is None:
        platform = port  # family

    if version is None:
        version = "0.0.0"

    if nodename is None:
        nodename = sysname
    if release is None:
        release = version
    if firmware is None:
        firmware = "{}-{}-{}".format(family, port, flat_version(version))

    mod_manifest = {
        "firmware": {
            "family": family,
            "port": port,
            "platform": platform,
            "machine": machine,
            "firmware": firmware,
            "nodename": nodename,
            "version": version,
            "release": release,
            "sysname": sysname,
        },
        "stubber": {"version": VERSION},
        "modules": [],
    }
    return mod_manifest


def make_manifest(folder: Path, family: str, port: str, version: str) -> bool:
    """Create a `module.json` manifest listing all files/stubs in this folder and subfolders."""
    mod_manifest = manifest(family=family, port=port, sysname=family, version=version)

    try:
        # list all *.py files, not strictly modules but decent enough for documentation
        for file in folder.glob("**/*.py"):
            mod_manifest["modules"].append({"file": str(file.relative_to(folder)), "module": file.stem})
        # write the the module manifest
        with open(os.path.join(folder, "modules.json"), "w") as outfile:
            json.dump(mod_manifest, outfile, indent=4, sort_keys=True)
        return True
    except OSError:
        return False


def generate_all_stubs():
    "just create typeshed stubs"
    # now generate typeshed files for all scripts
    print("Generate type hint files (pyi) in folder: {}".format(STUB_FOLDER))
    generate_pyi_files(Path(STUB_FOLDER))


def read_exclusion_file(path: Path = None) -> List[str]:
    """Read a .exclusion file to determine which files should not be automatically re-generated
    in .GitIgnore format

    """
    if path is None:
        path = Path(".")
    try:
        with open(path.joinpath(".exclusions")) as f:
            content = f.readlines()
            return [line.rstrip() for line in content if line[0] != "#" and len(line.strip()) != 0]
    except OSError:
        return []
    # exclusions = read_exclusion_file()


def should_ignore(file: str, exclusions: List[str]) -> bool:
    """Check if  a file matches a line in the exclusion list."""
    for excl in exclusions:
        if fnmatch(file, excl):
            return True
    return False
    # for file in Path(".").glob("**/*.py*"):
    #     if should_ignore(str(file), exclusions):
    #         print(file)
