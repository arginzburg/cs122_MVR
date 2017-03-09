# Quick function to differtiate OS X from Linux. Obviously I don't expect this
# to be worth anything for grading, but it helps when going back and forth
# between my laptop (which tends to run everything faster) and the VMs.
#
# Based on
# http://stackoverflow.com/questions/8220108/how-do-i-check-the-operating-system-in-python

from sys import platform

def is_VM():
    if platform == "linux":
        return True
    elif platform == "darwin":
        return False