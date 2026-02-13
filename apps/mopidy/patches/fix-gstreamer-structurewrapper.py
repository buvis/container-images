"""Patch mopidy scan.py for GStreamer 1.25-1.26.2 StructureWrapper compat.

See: https://github.com/mopidy/mopidy/pull/2094
"""

import re
import sys

scan_py = "/usr/lib/python3/dist-packages/mopidy/audio/scan.py"

with open(scan_py) as f:
    content = f.read()

helper = '''

def _get_structure_name(struct):
    try:
        return struct.get_name()
    except AttributeError:
        with struct as _struct:
            return _struct.get_name()

'''

# Add helper after imports
content = content.replace(
    "from mopidy.internal.gi import Gst, GstPbutils\n",
    "from mopidy.internal.gi import Gst, GstPbutils\n" + helper,
)

# Patch the callsite in _process()
content = content.replace(
    'mime = msg.get_structure().get_value("caps").get_name()',
    'mime = _get_structure_name(msg.get_structure().get_value("caps"))',
)

with open(scan_py, "w") as f:
    f.write(content)

print("Patched scan.py")
