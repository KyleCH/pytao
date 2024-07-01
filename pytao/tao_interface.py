"""
This module defines the tao_interface class, a general purpose interface
between tao and python that supports both the ctypes and pexpect
backend implementations.  Also defined here are a couple of helper functions
for the tao_interface class.
"""

import io
import os
import re
import sys

from .tao_ctypes import TaoCore
from .tao_pexpect import tao_io


class new_stdout(object):
    """
    Re-routes the print statements generated by tao_io
    so that they can be shown by tao_console.
    """

    def __init__(self):
        self.file_obj = io.StringIO()

    def __enter__(self):
        self.current_out = sys.stdout
        sys.stdout = self.file_obj
        return self.file_obj

    def __exit__(self, type, value, traceback):
        sys.stdout = self.current_out


def filter_output(x):
    """
    Filters out certain ANSI escape sequences from the string x
    """
    if not isinstance(x, str):
        return x
    # Filter out \[[6 q first
    x = x.replace("\x1b[6 q", "")
    # replace line feed ('\x0a') with return ('\x0d')
    # while x.find('\x0a') != -1:
    #  x = x.replace('\x0a', '\x0d')
    # Remove xterm-specific escape code
    if x.find("\x1b[?1034h") != -1:
        x = x.replace("\x1b[?1034h", "")
    # Filter out color codes
    color_regex = re.compile("\x1b\\[[0-9;]*m")
    matches = color_regex.findall(x)
    for color in matches:
        x = x.replace(color, "")
    return x


class tao_interface:
    """
    Serves as a general purpose interface between tao and python
    Supports both the ctypes and pexpect interface implementations, allowing
    the user to select between them and falling back on the other if the
    selected interface cannot be used

    Init arguments:
    mode: either "ctypes" (default) or "pexpect"
    init_args: a string with the command line initialization arguments that
            tao should use, e.g. "-init tao.init -rf_on
    tao_exe: the tao executable to use (applies to pexpect only)
    so_lib: the tao shared library to use (applies to ctypes only)
    expect_str: the prompt string that tao will use (default is "Tao>")

    If you need direct access to the methods defined by the ctypes or pexpect
    backends, you can call them on self.pexpect_pipe and self.ctypes_pipe
    respectively, e.g. in ctypes mode, the cmd_real method can be accessed by
    self.ctypes_pipe.cmd_real()
    """

    def __init__(self, mode="ctypes", init_args="", tao_exe="", expect_str="Tao>", so_lib=""):
        self.mode = mode
        self.exe_lib_warnings = ""
        self.exe_lib_warning_type = "normal"
        # Where to look for the shared library/executable
        if "ACC_LOCAL_ROOT" in os.environ:
            EXE_DIR = os.environ["ACC_LOCAL_ROOT"] + "/production/bin/"
            LIB_DIR = os.environ["ACC_LOCAL_ROOT"] + "/production/lib/"
        elif "ACC_EXE" in os.environ:
            EXE_DIR = os.environ["ACC_EXE"] + "/"
            LIB_DIR = None
        else:
            EXE_DIR = None
            LIB_DIR = None

        # Check for executable
        if os.path.isfile(tao_exe) and os.access(tao_exe, os.X_OK):
            exe_found = True
        elif (
            EXE_DIR is not None
            and os.path.isfile(EXE_DIR + "tao")
            and os.access(EXE_DIR + "tao", os.X_OK)
        ):
            tao_exe = EXE_DIR + "tao"
            exe_found = True
            if (mode == "pexpect") & (tao_exe != ""):
                self.exe_lib_warnings += "Note: could not find " + tao_exe
                self.exe_lib_warnings += ".\nDefaulting to " + EXE_DIR + "tao"
        else:
            exe_found = False
            if mode == "pexpect":
                self.exe_lib_warnings += "Warning: no executable found, defaulting to ctypes"
                self.exe_lib_warning_type = "error"

        # Check for shared library (and set up self.ctypes_pipe)
        lib_found = False
        try:
            self.ctypes_pipe = TaoCore(so_lib=so_lib)
            lib_found = True
        except OSError:  # so_lib not found
            if LIB_DIR is not None:
                try:
                    self.ctypes_pipe = TaoCore(so_lib=LIB_DIR + "libtao.so")
                    lib_found = True
                    if mode == "ctypes":
                        self.exe_lib_warnings += "Note: could not find " + so_lib
                        self.exe_lib_warnings += ".\nUsing library in " + LIB_DIR
                except OSError:  # so_lib not found
                    pass  # will continue below
            if not lib_found:
                try:
                    self.ctypes_pipe = TaoCore(so_lib="")
                    lib_found = True
                    if mode == "ctypes":
                        self.exe_lib_warnings += "Note: could not find " + so_lib
                        self.exe_lib_warnings += (
                            ".\nUsing library in "
                            + os.environ["ACC_ROOT_DIR"]
                            + "/production/lib/"
                        )
                except ValueError:
                    lib_found = False
                    if mode == "ctypes":
                        self.exe_lib_warnings += (
                            "Warning: no shared library found, defaulting to pexpect"
                        )
                        self.exe_lib_warning_type = "error"
        except ValueError:
            lib_found = False

        if self.exe_lib_warnings != "":
            self.exe_lib_warnings += "\n"

        # Switch mode if necessary
        if exe_found and not lib_found:
            mode = "pexpect"
            self.mode = "pexpect"
        elif not exe_found and lib_found:
            mode = "ctypes"
            self.mode = "ctypes"
        elif not exe_found and not lib_found:
            mode = "failed"
            self.mode = "failed"

        # new_stdout() needed to capture print statements from tao_io
        with new_stdout() as output:
            if mode == "pexpect":
                self.pexpect_pipe = tao_io(
                    init_args=init_args, tao_exe=tao_exe, expect_str=expect_str
                )
            if mode == "ctypes":
                for line in self.ctypes_pipe.init(init_args):
                    print(line)
            if mode == "failed":
                self.exe_lib_warnings += (
                    "FATAL: could not locate Tao shared library or executable.\n"
                )
                self.exe_lib_warnings += (
                    "Please reinitialize with a good executable or shared library."
                )
                self.exe_lib_warning_type = "fatal"
                print("")

        # Process startup message
        output = output.getvalue()
        output = filter_output(output)
        self.startup_message = output

    def cmd_in(self, cmd_str):
        """
        Runs cmd_str at the Tao command line and returns the output as a string
        """
        # Run the command:
        if self.mode == "pexpect":
            output = self.pexpect_pipe.cmd_in(cmd_str)
        elif self.mode == "ctypes":
            output_list = self.ctypes_pipe.cmd(cmd_str)
            output = ""
            for line in output_list:
                if line.strip != "":
                    output += line + "\n"
            if (len(output) > 0) and (output[-1] == "\n"):
                output = output[:-1]
        else:
            output = ""

        # Scrub output for extra new lines at the end,
        # as well as escape characters
        if cmd_str.find("python") == 0:
            output = output.replace("\r\n\r\n", "")
        output = filter_output(output)

        return output

    def cmd(self, cmd_str):
        """
        Runs cmd_str at the Tao command line and prints the output
        to standard out
        """
        self.cmd_in(cmd_str)
