"""
Helper module to create stubs for the lvgl modules.
Note that the stubs can be very large, and it may be best to directly store them on an SD card if your device supports this.
"""

try:
    import lvgl
except:
    # raise ImportError("The `lvgl` module could not be found on this firmware")
    pass

import sys
from createstubs import *


def main():
    "Create stubs for the lvgl modules using the lvlg version number."
    print("stubber version :", stubber_version)
    try:
        logging.basicConfig(level=logging.INFO)
        # logging.basicConfig(level=logging.DEBUG)
    except NameError:
        pass
    # Specify firmware name & version
    try:
        fw_id = "lvgl-{0}_{1}_{2}-{3}-{4}".format(
            lvgl.version_major(),
            lvgl.version_minor(),
            lvgl.version_patch(),
            lvgl.version_info(),
            sys.platform,
        )
    except:
        fw_id = "lvgl-{0}_{1}_{2}_{3}-{4}".format(8, 1, 0, "dev", sys.platform)
    stubber = Stubber(firmware_id=fw_id, path="/sd")
    stubber.clean()

    # Just get the lvlg modules written in C
    stubber.modules = ["io", "lodepng", "rtch", "lvgl"]
    stubber.create_all_stubs()
    stubber.report()


if __name__ == "__main__" or isMicroPython():
    main()
