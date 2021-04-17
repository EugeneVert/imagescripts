#!/usr/bin/env python3

"""Formating/cli functions"""


import os
import re


def image_has_transparency(image):
    if len(image.getbands()) < 4:  # if 'A' not in image.getbands()
        return False
    return image.getextrema()[3][0] < 255


def size2bytes(size):
    size_name = ("B", "K", "M", "G")
    size.upper()
    size = re.split(r'(\d+)', size)
    num, unit = int(size[1]), size[2]
    idx = size_name.index(unit)
    factor = 1024 ** idx
    return num * factor


def bite2size(num, suffix='iB'):
    for unit in ['', 'K', 'M', 'G']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def confirmprompt(promptin):
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(promptin + " [Y/N]? ").lower()
    return answer == "y"


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)
