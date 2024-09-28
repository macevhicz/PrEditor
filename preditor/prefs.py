"""
Module for handling user interface preferences

"""
from __future__ import absolute_import

import os
import re
import sys

from pathlib2 import Path
import datetime

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
format_str = '%(levelname)s %(module)s.%(funcName)s line:%(lineno)d - %(message)s'
formatter = logging.Formatter(format_str)
for handler in logging.root.handlers:
    handler.setFormatter(formatter)

# cache of all the preferences
_cache = {}

TIME_FORMAT = "-%Y-%m-%d-%H-%M-%S"


class VersionTypes:
    """Nice names for the workbox version types."""

    First = 0
    Previous = 1
    Next = 2
    Last = 3


def backup():
    """Saves a copy of the current preferences to a zip archive."""
    import glob
    import shutil

    archive_base = "preditor_backup_"
    # Save all prefs not just the current core_name.
    prefs = prefs_path()
    # Note: Using parent dir of prefs so we can use shutil.make_archive without
    # backing up the previous backups.
    parent_dir = os.path.join(os.path.dirname(prefs), "_backups")

    # Get the next backup version number to use.
    filenames = glob.glob(os.path.join(parent_dir, "{}*.zip".format(archive_base)))
    version = 1
    if filenames:
        # Add one to the largest version that exists on disk.
        version = int(os.path.splitext(max(filenames))[0].split(archive_base)[-1])
        version += 1

    # Build the file path to save the archive to.
    archive_base = os.path.join(parent_dir, archive_base + "{:04}".format(version))

    # Save the preferences to the given archive name.
    zip_path = shutil.make_archive(archive_base, "zip", prefs)

    return zip_path


def browse(core_name):
    from . import osystem

    path = prefs_path(core_name)
    osystem.explore(path)


def existing():
    """Returns a list of PrEditor preference path names that exist on disk."""
    root = prefs_path()
    return sorted(next(os.walk(root))[1], key=lambda i: i.lower())


def prefs_path(filename=None, core_name=None):
    """The path PrEditor's preferences are saved as a json file.

    The enviroment variable `PREDITOR_PREF_PATH` is used if set, otherwise
    it is saved in one of the user folders.
    """
    if "PREDITOR_PREF_PATH" in os.environ:
        ret = os.environ["PREDITOR_PREF_PATH"]
    else:
        if sys.platform == "win32":
            ret = "%appdata%/blur/preditor"
        else:
            ret = "$HOME/.blur/preditor"
    ret = os.path.normpath(os.path.expandvars(os.path.expanduser(ret)))
    if core_name:
        ret = os.path.join(ret, core_name)
    if filename:
        ret = os.path.join(ret, filename)
    return ret


def temp_dir(core_name=None, create=False):
    temp_dir = prefs_path('workboxes', core_name=core_name)
    if create and not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    return temp_dir


def temp_file(tempfile, create=False):
    if tempfile:
        return os.path.join(temp_dir(create=create), tempfile)


def create_stamped_path(core_name, group_name, name):
    directory = temp_dir(core_name=core_name, create=True)

    stem = Path(name).stem
    suffix = Path(name).suffix or ".py"

    now = datetime.datetime.now()
    time_str = now.strftime(TIME_FORMAT)
    stem += time_str

    path = (Path(directory) / group_name / stem).with_suffix(suffix)

    path.parent.mkdir(exist_ok=True)
    return path


def get_file_group(core_name, group_name, workbox_name):
    directory = Path(temp_dir(core_name=core_name)) / group_name

    workbox_name = Path(workbox_name).stem
    globStr = "{}*".format(workbox_name)
    datetime_pattern = r"-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}"
    pattern = workbox_name + datetime_pattern

    files = list(directory.glob(globStr))
    files = [file for file in files if re.match(pattern, file.stem)]
    return files


def get_backup_version_info(
    core_name, group_name, workbox_name, versionType, backup_file
):
    files = get_file_group(core_name, group_name, workbox_name)
    if not files:
        return ("", "", 0)
    count = len(files)

    idx = len(files) - 1
    if versionType == VersionTypes.First:
        idx = 0
    elif versionType == VersionTypes.Last:
        idx = len(files) - 1
    else:
        current_name = Path(backup_file) if backup_file else ""
        if current_name in files:
            idx = files.index(current_name)
            if versionType == VersionTypes.Previous:
                idx -= 1
                idx = max(idx, 0)
            else:
                idx += 1
                idx = min(idx, count - 1)

    filepath = files[idx]
    return filepath, idx + 1, count
