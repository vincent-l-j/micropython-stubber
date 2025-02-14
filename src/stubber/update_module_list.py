"""
generate the list of modules that should be attempted to stub
for this : 
- combine the modules from the different texts files
- split the lines into individual module names
- combine them in one set
- remove the ones than cannot be stubbed
- remove test modules, ending in `_test`
- write updates to:
    - board/modulelist.txt
    - board/createsubs.py 

- TODO: remove the frozen modules from this list
- TODO: bump patch number if there are actual changes

"""

from pathlib import Path
from typing import Set, List, Union


def read_modules(path: Path = None) -> Set:
    """
    read text files with modules per firmware.
    each contains the output of help("modules")
    - lines starting with # are comments.
    - split the other lines at whitespace seperator,
    - and add each module to a set
    """
    path = Path(path or "./data")
    assert path
    all_modules = set()
    for file in path.glob("*.txt"):
        print("processing:", file)
        with file.open("r") as f:
            line = f.readline()
            while line:
                if len(line) > 1 and line[0] != "#":

                    file_mods = line.split()
                    # print(line[0:-1])
                    # print( set(file_mods))
                    # remove modules ending in _test
                    file_mods = [m for m in file_mods if not m.endswith("_test")]
                    all_modules = set(all_modules | set(file_mods))
                # next
                line = f.readline()

    #     print("-" * 40)
    # print(">" * 40)

    return all_modules


def wrapped(modules: Union[Set, List]) -> str:
    "wrap code line at spaces"
    long_line = str(modules)
    _wrapped = "        self.modules = "
    IDENT = len(_wrapped)
    MAX_WIDTH = 135

    # find seperator
    while len(long_line) > MAX_WIDTH:
        p1 = long_line.find("', ", MAX_WIDTH)
        # drop space
        p1 += 3
        short = long_line[0 : p1 - 1]
        _wrapped += short + "\n" + " " * IDENT
        long_line = long_line[p1 - 1 :]
    _wrapped += long_line
    return _wrapped


def main():
    """
    helper script
    generate a few lines of code with all modules to be stubbed by createstubs
    """
    #######################################################################
    # the exceptions
    #######################################################################
    mods_problematic = set(
        [
            "upysh",
            "webrepl_setup",
            "http_client",
            "http_client_ssl",
            "http_server",
            "http_server_ssl",
        ]
    )
    mods_excluded = set(
        [
            "__main__",
            "_main",
            "_boot",
            "webrepl",
            "_webrepl",
            "port_diag",
            "example_sub_led",
            "example_pub_button",
            "upip",
            "upip_utarfile",
            "upysh",
            # DOCSTUB_SKIP = [
            "uasyncio",  # can create better stubs from frozen python modules.
            "builtins",  # conflicts with static type checking , has very little information anyway
            "re",  # regex is too complex
            "collections",
            "io",
            "uio",
        ]
    )

    all_modules = read_modules()
    modules_to_stub = sorted(all_modules - set(mods_excluded | mods_problematic))

    # remove pycom MQTT* from defaults
    modules_to_stub = sorted({m for m in modules_to_stub if not m.startswith("MQTT")})

    # print("modules to stub :", len(modules_to_stub))
    # print(wrapped(modules_to_stub))

    # update modules.txt
    modules_txt = Path("board/modulelist.txt")
    if modules_txt.exists():
        with open(modules_txt) as f:
            lines = f.readlines()
            # only keep comment lines
            lines = [l for l in lines if l[0] == "#"]
    else:
        lines = ["# list of modules to stub."]
    lines = lines + [m + "\n" for m in modules_to_stub]

    with open(modules_txt, "w") as f:
        f.writelines(lines)

    # update createstubs.py
    createstubs = Path("board/createstubs.py")
    if createstubs.exists():
        with open(createstubs) as f:
            lines = f.readlines()

    l_start = lines.index("    stubber.modules = [\n")
    assert l_start
    l_end = lines.index("    ]  # spell-checker: enable\n", l_start)
    assert l_end

    # Plug in the new list of modules
    lines = lines[: l_start + 1] + [f'        "{m}",\n' for m in modules_to_stub] + lines[l_end:]

    with open(createstubs, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main()
