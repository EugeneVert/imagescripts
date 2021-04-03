#!/usr/bin/env python3
#
# 2021 Eugene Vert; eugene.a.vert@gmail.com

"""Script to find images with same image sizes

This script sort images in given directory (or in current work dir) by their
image sizes. Images with same image sizes grouped in directory's
with names of images dimension's.

Minimum count of images of same size is asked on run
1'st optional argument -- path
"""

import os
import sys

from PIL import Image
from termcolor import colored

from imagescripts_utils import file_move


def main(argv):
    print(argv)
    if len(argv) >= 2:
        print('by argument')
        dir_target = os.path.abspath(argv[1])
    else:
        print('by cwd')
        dir_target = os.getcwd()
    files_in_dir = [f.name for f in os.scandir(dir_target) if f.is_file()]
    print(colored('Path: ' + dir_target, 'yellow'))
    img_c_min = int(input('Min images count to mv '))
    input('Press any key')

    os.chdir(dir_target)
    images_find_eq_res(files_in_dir, dir_target, img_c_min)


def images_find_eq_res(files_in_dir, dir_target, img_c_min):
    known_images_dict = dict()
    for i in files_in_dir:
        img = None
        print('file: ', i)
        try:
            img = Image.open(i)
        except:
            print("can't open open image")
            continue

        img_res = img.size
        print(img_res)

        known_images_dict[i] = img_res

    resname_images_dict = images_dict_flipsort(known_images_dict, dir_target)
    for res, j in resname_images_dict.items():
        print('res: ', res)
        print(j)

        if len(j) > img_c_min:
            for f in j:
                file_move(dir_target, f, str(res[0])+' x'+str(res[1]), 'file ' + f + ' moved')


def images_dict_flipsort(images_dict, dir_target):
    flipped = {}
    for key, value in images_dict.items():
        if value not in flipped:
            flipped[value] = [key]
        else:
            flipped[value].append(key)
    return flipped


if __name__ == '__main__':
    main(sys.argv)
    print('done')
