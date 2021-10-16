"""
Create stubs for (all) modules on a MicroPython board
Copyright (c) 2019-2021 Jos Verlinde
"""
# pylint: disable= invalid-name, missing-function-docstring, import-outside-toplevel, logging-not-lazy
import sys
import gc
import logging
import uos as os
from utime import sleep_us
from ujson import dumps

ENOENT = 2
stubber_version = "1.4.0.beta"
# deal with ESP32 firmware specific implementations.
try:
    from machine import resetWDT  # type: ignore  - LoBo specific function
except ImportError:
    # machine.WDT.feed()
    def resetWDT():
        pass


class Stubber:
    "Generate stubs for modules in firmware"
    MAX_CLASS_LEVEL = 2  # Max class nesting

    def __init__(self, path: str = None, firmware_id: str = None):
        try:
            if os.uname().release == "1.13.0" and os.uname().version < "v1.13-103":
                raise NotImplementedError("MicroPython 1.13.0 cannot be stubbed")
        except AttributeError:
            pass

        self._log = logging.getLogger("stubber")
        self._report = []
        self.info = self._info()
        if firmware_id:
            self._fwid = str(firmware_id).lower()
        else:
            self._fwid = "{family}-{port}-{ver}".format(**self.info).lower()
        self._start_free = gc.mem_free()  # type: ignore

        if path:
            if path.endswith("/"):
                path = path[:-1]
        else:
            path = self.get_root()

        self.path = "{}/stubs/{}".format(path, self.flat_fwid).replace("//", "/")
        self._log.debug(self.path)
        try:
            self.ensure_folder(path + "/")
        except OSError:
            self._log.error("error creating stub folder {}".format(path))
        self.problematic = [
            "upysh",
            "webrepl_setup",
            "http_client",
            "http_client_ssl",
            "http_server",
            "http_server_ssl",
        ]
        self.excluded = [
            "webrepl",
            "_webrepl",
            "port_diag",
            "example_sub_led.py",
            "example_pub_button.py",
        ]
        # there is no option to discover modules from micropython, need to hardcode
        # below contains combined modules from  Micropython ESP8622, ESP32, Loboris, Pycom and ulab , lvgl
        # spell-checker: disable
        # modules to stub : 131
        self.modules = [
            "_onewire",
            "_thread",
            "_uasyncio",
            "ak8963",
            "apa102",
            "apa106",
            "array",
            "binascii",
            "btree",
            "builtins",
            "cmath",
            "collections",
            "crypto",
            "curl",
            "dht",
            "display",
            "display_driver_utils",
            "ds18x20",
            "errno",
            "esp",
            "esp32",
            "espidf",
            "flashbdev",
            "framebuf",
            "freesans20",
            "fs_driver",
            "functools",
            "gc",
            "gsm",
            "hashlib",
            "heapq",
            #            "ili9341",
            "ili9XXX",
            "imagetools",
            "inisetup",
            "io",
            "json",
            "lcd160cr",
            "lodepng",
            "logging",
            "lv_colors",
            "lv_utils",
            "lvgl",
            "lwip",
            "machine",
            "math",
            "microWebSocket",
            "microWebSrv",
            "microWebTemplate",
            "micropython",
            "mpu6500",
            "mpu9250",
            "neopixel",
            "network",
            "ntptime",
            "onewire",
            "os",
            "pyb",
            "pycom",
            "pye",
            "queue",
            "random",
            "re",
            "requests",
            "rtch",
            "select",
            "socket",
            "ssd1306",
            "ssh",
            "ssl",
            "stm",
            "struct",
            "sys",
            "time",
            "tpcalib",
            "uarray",
            "uasyncio/__init__",
            "uasyncio/core",
            "uasyncio/event",
            "uasyncio/funcs",
            "uasyncio/lock",
            "uasyncio/stream",
            "ubinascii",
            "ubluetooth",
            "ucollections",
            "ucrypto",
            "ucryptolib",
            "uctypes",
            "uerrno",
            "uftpd",
            "uhashlib",
            "uheapq",
            "uio",
            "ujson",
            "ulab",
            "ulab/approx",
            "ulab/compare",
            "ulab/fft",
            "ulab/filter",
            "ulab/linalg",
            "ulab/numerical",
            "ulab/poly",
            "ulab/user",
            "ulab/vector",
            "umachine",
            "umqtt/robust",
            "umqtt/simple",
            "uos",
            "upip",
            "upip_utarfile",
            "uqueue",
            "urandom",
            "ure",
            "urequests",
            "urllib/urequest",
            "uselect",
            "usocket",
            "ussl",
            "ustruct",
            "usys",
            "utelnetserver",
            "utime",
            "utimeq",
            "uwebsocket",
            "uzlib",
            "websocket",
            "websocket_helper",
            "writer",
            "xpt2046",
            "ymodem",
            "zlib",
        ]  # spell-checker: enable
        # try to avoid running out of memory with nested mods
        self.include_nested = gc.mem_free() > 3200  # type: ignore

    @staticmethod
    def _info():
        "collect base information on this runtime"
        _n = sys.implementation.name  # type: ignore
        _p = sys.platform
        info = {
            "name": _n,  # - micropython
            "release": "0.0.0",  # mpy semver from sys.implementation or os.uname()release
            "version": "0.0.0",  # major.minor.0
            "build": "",  # parsed from version
            "sysname": "unknown",  # esp32
            "nodename": "unknown",  # ! not on all builds
            "machine": "unknown",  # ! not on all builds
            "family": _n,  # fw families, micropython , pycopy , lobo , pycom
            "platform": _p,  # port: esp32 / win32 / linux
            "port": _p,  # port: esp32 / win32 / linux
            "ver": "",  # short version
        }
        try:
            info["release"] = ".".join([str(n) for n in sys.implementation.version])
            info["version"] = info["release"]
            info["name"] = sys.implementation.name
            info["mpy"] = sys.implementation.mpy  # type: ignore
        except AttributeError:
            pass

        if sys.platform not in ("unix", "win32"):
            try:
                u = os.uname()
                info["sysname"] = u.sysname
                info["nodename"] = u.nodename
                info["release"] = u.release
                info["machine"] = u.machine
                # parse micropython build info
                if " on " in u.version:
                    s = u.version.split("on ")[0]
                    try:
                        info["build"] = s.split("-")[1]
                    except IndexError:
                        pass
            except (IndexError, AttributeError, TypeError):
                pass

        try:  # families
            from pycopy import const  # type: ignore

            info["family"] = "pycopy"
            del const
        except (ImportError, KeyError):
            pass
        if info["platform"] == "esp32_LoBo":
            info["family"] = "loboris"
            info["port"] = "esp32"
        elif info["sysname"] == "ev3":
            # ev3 pybricks
            info["family"] = "ev3-pybricks"
            info["release"] = "1.0.0"
            try:
                # Version 2.0 introduces the EV3Brick() class.
                from pybricks.hubs import EV3Brick  # type: ignore

                info["release"] = "2.0.0"
            except ImportError:
                pass

        # version info
        if info["release"]:
            info["ver"] = "v" + info["release"]
        if info["family"] != "loboris":
            if info["release"] and info["release"] >= "1.10.0" and info["release"].endswith(".0"):
                # drop the .0 for newer releases
                info["ver"] = info["release"][:-2]
            else:
                info["ver"] = info["release"]
            # add the build nr
            if info["build"] != "":
                info["ver"] += "-" + info["build"]
        # spell-checker: disable
        if "mpy" in info:  # mpy on some v1.11+ builds
            sys_mpy = int(info["mpy"])
            arch = [
                None,
                "x86",
                "x64",
                "armv6",
                "armv6m",
                "armv7m",
                "armv7em",
                "armv7emsp",
                "armv7emdp",
                "xtensa",
                "xtensawin",
            ][sys_mpy >> 10]
            if arch:
                info["arch"] = arch
        return info
        # spell-checker: enable

    def get_obj_attributes(self, obj: object):
        "extract information of the objects members and attributes"
        result = []
        errors = []
        name = None
        self._log.debug("get attributes {} {}".format(repr(obj), obj))
        try:
            for name in dir(obj):
                try:
                    val = getattr(obj, name)
                    # name , value , type
                    result.append((name, repr(val), repr(type(val)), val))
                except AttributeError as e:
                    errors.append("Couldn't get attribute '{}' from object '{}', Err: {}".format(name, obj, e))
        except AttributeError as e:
            errors.append("Couldn't get attribute '{}' from object '{}', Err: {}".format(name, obj, e))
        # remove internal __
        result = [i for i in result if not (i[0].startswith("_") and i[0] != "__init__")]
        gc.collect()
        return result, errors

    def add_modules(self, modules: list):
        "Add additional modules to be exported"
        self.modules = sorted(set(self.modules) | set(modules))

    def create_all_stubs(self):
        "Create stubs for all configured modules"
        self._log.info("Start micropython-stubber v{} on {}".format(stubber_version, self._fwid))
        # start with the (more complex) modules with a / first to reduce memory problems
        self.modules = [m for m in self.modules if "/" in m] + [m for m in self.modules if "/" not in m]
        gc.collect()
        for module_name in self.modules:
            # re-evaluate
            if self.include_nested:
                self.include_nested = gc.mem_free() > 3200  # type: ignore
            # use training comma to overide black formatting to avoid minify chocking on this
            if module_name.startswith("_") and module_name != "_thread":
                self._log.warning(
                    "Skip module: {:<20}        : Internal ".format(module_name),
                )
                continue
            if module_name in self.problematic:
                self._log.warning("Skip module: {:<20}        : Known problematic".format(module_name))
                continue
            if module_name in self.excluded:
                self._log.warning("Skip module: {:<20}        : Excluded".format(module_name))
                continue

            file_name = "{}/{}.py".format(self.path, module_name.replace(".", "/"))
            gc.collect()
            m1 = gc.mem_free()  # type: ignore
            self._log.info("Stub module: {:<20} to file: {:<55} mem:{:>5}".format(module_name, file_name, m1))
            try:
                self.create_module_stub(module_name, file_name)
            except OSError:
                pass
            gc.collect()
            self._log.debug("Memory     : {:>20} {:>6X}".format(m1, m1 - gc.mem_free()))  # type: ignore
        self._log.info("Finally done")

    def create_module_stub(self, module_name: str, file_name: str = None):
        "Create a Stub of a single python module"
        if module_name.startswith("_") and module_name != "_thread":
            self._log.warning("SKIPPING internal module:{}".format(module_name))
            return

        if module_name in self.problematic:
            self._log.warning("SKIPPING problematic module:{}".format(module_name))
            return

        if file_name is None:
            file_name = self.path + "/" + module_name.replace(".", "_") + ".py"

        if "/" in module_name:
            # for nested modules
            module_name = module_name.replace("/", ".")
            if not self.include_nested:
                self._log.warning("SKIPPING nested module:{}".format(module_name))
                return

        # import the module (as new_module) to examine it
        failed = False
        new_module = None
        try:
            new_module = __import__(module_name, None, None, ("*"))
        except ImportError:
            failed = True
            self._log.warning("Skip module: {:<20}        : Failed to import".format(module_name))
            if not "." in module_name:
                return

        # re-try import after importing parents
        if failed and "." in module_name:
            self._log.debug("re-try import with parents")
            levels = module_name.split(".")
            for n in range(1, len(levels)):
                parent_name = ".".join(levels[0:n])
                try:
                    parent = __import__(parent_name)
                    del parent
                except (ImportError, KeyError):
                    pass
            try:
                new_module = __import__(module_name, None, None, ("*"))
                self._log.debug("OK , imported module: {} ".format(module_name))
            except ImportError:  # now bail out
                self._log.debug("Failed to import module: {}".format(module_name))
                return

        # Start a new file
        self.ensure_folder(file_name)
        with open(file_name, "w") as fp:
            # todo: improve header
            s = '"""\nModule: \'{0}\' on {1}\n"""\n# MCU: {2}\n# Stubber: {3}\n'.format(
                module_name, self._fwid, self.info, stubber_version
            )
            fp.write(s)
            fp.write("from typing import Any\n\n")
            self.write_object_stub(fp, new_module, module_name, "")
            self._report.append({"module": module_name, "file": file_name})

        if not module_name in ["os", "sys", "logging", "gc"]:
            # try to unload the module unless we use it
            try:
                del new_module
            except (OSError, KeyError):  # lgtm [py/unreachable-statement]
                self._log.warning("could not del new_module")
            try:
                del sys.modules[module_name]
            except KeyError:
                self._log.debug("could not del sys.modules[{}]".format(module_name))
            gc.collect()

    def write_object_stub(self, fp, object_expr: object, obj_name: str, indent: str, in_class: int = 0):
        "Write a module/object stub to an open file. Can be called recursive."
        if object_expr in self.problematic:
            self._log.warning("SKIPPING problematic module:{}".format(object_expr))
            return

        # self._log.debug("DUMP    : {}".format(object_expr))
        items, errors = self.get_obj_attributes(object_expr)

        if errors:
            self._log.error(errors)

        for name, rep, typ, obj in items:
            # allow the scheduler to run on LoBo based FW
            resetWDT()
            sleep_us(1)

            cls_mtd_tps = ["<class 'function'>", "<class 'bound_method'>"]

            # Class expansion only on first 3 levels (bit of a hack)
            if typ == "<class 'type'>" and len(indent) <= self.MAX_CLASS_LEVEL * 4:
                self._log.debug("{0}class {1}:".format(indent, name))
                # stub style : generic __init__ with Empty comment and pass
                s = "\n" + indent + "class " + name + ":\n"  #
                s += indent + "    ''\n"

                fp.write(s)
                # self._log.debug("\n" + s)

                self._log.debug("# recursion over class {0}".format(name))
                self.write_object_stub(
                    fp,
                    obj,
                    "{0}.{1}".format(obj_name, name),
                    indent + "    ",
                    in_class + 1,
                )
            # Class Methods
            elif typ in cls_mtd_tps:
                self._log.debug("# def {1} function or method, type = '{0}'".format(typ, name))
                # module Function or class method
                # will accept any number of params
                # return type Any
                ret = "Any"
                first = ""
                # Self parameter only on class functions
                if typ == cls_mtd_tps[0]:
                    first = "self, "
                    # __init__ returns None
                    if name == "__init__":
                        ret = "None"
                # class method - add function decoration
                if typ == cls_mtd_tps[1]:
                    s = "{}@classmethod\n".format(indent)
                    s += "{}def {}(cls) -> {}:\n".format(indent, name, ret)
                else:
                    s = "{}def {}({}*args) -> {}:\n".format(indent, name, first, ret)
                # s += indent + "    ''\n" # EMPTY DOCSTRING
                s += indent + "    ...\n\n"
                fp.write(s)
                self._log.debug("\n" + s)
            # constants of known types & values
            elif typ.startswith("<class '"):

                t = typ[8:-2]
                s = ""

                if t in ["str", "int", "float", "bool", "bytearray", "bytes"]:
                    # known type: use actual value
                    s = "{0}{1} = {2} # type: {3}\n".format(indent, name, rep, t)
                elif t in ["dict", "list", "tuple"]:
                    # dict, list , tuple: use empty value
                    ev = {"dict": "{}", "list": "[]", "tuple": "()"}
                    s = "{0}{1} = {2} # type: {3}\n".format(indent, name, ev[t], t)
                else:
                    # something else
                    if not t in ["object", "set", "frozenset"]:
                        # Possibly default others to instance object ?
                        # https://docs.python.org/3/tutorial/classes.html#instance-objects
                        t = "Any"
                    s = "{0}{1}: {2}\n".format(indent, name, t)
                fp.write(s)
                self._log.debug("\n" + s)
            else:
                # keep only the name
                self._log.debug("# all other, type = '{0}'".format(typ))
                fp.write("# all other, type = '{0}'\n".format(typ))

                fp.write(indent + name + " = Any\n")

        del items
        del errors
        try:
            del name, rep, typ, obj  # pylint: disable=undefined-loop-variable
        except (OSError, KeyError, NameError):  # lgtm [py/unreachable-statement]
            pass

    @property
    def flat_fwid(self):
        "Turn _fwid from 'v1.2.3' into '1_2_3' to be used in filename"
        s = self._fwid
        # path name restrictions
        chars = " .()/\\:$"
        for c in chars:
            s = s.replace(c, "_")
        return s

    def clean(self, path: str = None):
        "Remove all files from the stub folder"
        if path is None:
            path = self.path
        self._log.info("Clean/remove files in folder: {}".format(path))
        try:
            items = os.listdir(path)
        except (OSError, AttributeError):  # lgtm [py/unreachable-statement]
            # os.listdir fails on unix
            return
        for fn in items:
            item = "{}/{}".format(path, fn)
            try:
                os.remove(item)
            except OSError:
                try:  # folder
                    self.clean(item)
                    os.rmdir(item)
                except OSError:
                    pass

    def report(self, filename: str = "modules.json"):
        "create json with list of exported modules"
        self._log.info(
            "Created stubs for {} modules on board {}\nPath: {}".format(len(self._report), self._fwid, self.path)
        )
        f_name = "{}/{}".format(self.path, filename)
        gc.collect()
        try:
            # write json by node to reduce memory requirements
            with open(f_name, "w") as f:
                f.write("{")
                f.write(dumps({"firmware": self.info})[1:-1])
                f.write(",\n")
                f.write(dumps({"stubber": {"version": stubber_version}})[1:-1])
                f.write(",\n")
                f.write('"modules" :[\n')
                start = True
                for n in self._report:
                    if start:
                        start = False
                    else:
                        f.write(",\n")
                    f.write(dumps(n))
                f.write("\n]}")
            used = self._start_free - gc.mem_free()  # type: ignore
            self._log.info("Memory used: {0} Kb".format(used // 1024))
        except OSError:
            self._log.error("Failed to create the report.")

    def ensure_folder(self, path: str):
        "Create nested folders if needed"
        i = start = 0
        while i != -1:
            i = path.find("/", start)
            if i != -1:
                if i == 0:
                    p = path[0]
                else:
                    p = path[0:i]
                # p = partial folder
                try:
                    _ = os.stat(p)
                except OSError as e:
                    # folder does not exist
                    if e.args[0] == ENOENT:
                        try:
                            os.mkdir(p)
                        except OSError as e2:
                            self._log.error("failed to create folder {}".format(p))
                            raise e2
                    else:
                        self._log.error("failed to create folder {}".format(p))
                        raise e
            # next level deep
            start = i + 1

    @staticmethod
    def get_root() -> str:
        "Determine the root folder of the device"
        try:
            r = "/flash"
            _ = os.stat(r)
        except OSError as e:
            if e.args[0] == ENOENT:
                try:
                    r = os.getcwd()
                except (OSError, AttributeError):
                    # unix port
                    r = "."
            else:
                r = "/"
        return r


def show_help():
    print("-p, --path   path to store the stubs in, defaults to '.'")
    sys.exit(1)


def read_path() -> str:
    "get --path from cmdline. [unix/win]"
    path = ""
    if len(sys.argv) == 3:
        cmd = (sys.argv[1]).lower()
        if cmd in ("--path", "-p"):
            path = sys.argv[2]
        else:
            show_help()
    elif len(sys.argv) == 2:
        show_help()
    return path


def isMicroPython() -> bool:
    "runtime test to determine full or micropython"
    # pylint: disable=unused-variable,eval-used
    try:
        # either test should fail on micropython
        # a) https://docs.micropython.org/en/latest/genrst/syntax.html#spaces
        # b) https://docs.micropython.org/en/latest/genrst/builtin_types.html#bytes-with-keywords-not-implemented
        a = eval("1and 0")  # lgtm [py/unused-local-variable]
        b = bytes("abc", encoding="utf8")  # lgtm [py/unused-local-variable]
        return False
    except (NotImplementedError, SyntaxError):
        return True


def main():
    print("stubber version :", stubber_version)
    try:
        logging.basicConfig(level=logging.INFO)
        # logging.basicConfig(level=logging.DEBUG)
    except NameError:
        pass
    stubber = Stubber(path=read_path())
    # stubber = Stubber(path="/sd")
    # Option: Specify a firmware name & version
    # stubber = Stubber(firmware_id='HoverBot v1.2.1')
    stubber.clean()
    # # Option: Add your own modules
    # # stubber.add_modules(['bluetooth','GPS'])
    stubber.create_all_stubs()
    stubber.report()


if __name__ == "__main__" or isMicroPython():
    main()
