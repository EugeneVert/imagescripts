#!/usr/bin/env python3
#
# 2021 Eugene Vert; eugene.a.vert@gmail.com

"""Script to find images with size bigger then given

This script can sort 'resizeble' images to folders based on their property's.
Png's can be sorted separately, based on their resolution and file-size
"""

import os
import argparse
from pathlib import Path

from PIL import Image
from termcolor import colored


NONIMAGES_DIR_NAME = './mv'


def argument_parser(*args):
    parser = argparse.ArgumentParser(
        description="Find images larger than the specified imagesize",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', nargs='?',
                        help='Path of a dir.')
    parser.add_argument("-s", "--size",
                        help="move img size px" +
                             "   (default: %(default)s)\n(Note: A4 sizes(px) -- 1240,1754,2480,3508,4960,5953,7016)",
                        default=3508, type=int)
    parser.add_argument("-p", "--png-sort",
                        help="move png's to different folder",
                        action="store_true")
    parser.add_argument("-p:p", "--png_size_px",
                        help="move png size px   (default: %(default)s)",
                        default=1754, type=int)
    parser.add_argument("-p:m", "--png_size_mib",
                        help="move png size MiB  (default: %(default)s)",
                        default=1.3, type=float)
    parser.add_argument("-n", "--nonimages-mv",
                        help="move non-images to ./mv folder",
                        action="store_true")

    return parser.parse_args(*args)


def main(*args):
    args = argument_parser(*args)
    print(args)
    if args.path:
        print('by argument')
        input_dir = Path(args.path)
    else:
        print('by cwd')
        input_dir = Path.cwd()
        args.path = "."
    print(colored('Path: ' + str(input_dir.resolve()), 'yellow'))

    input_dir_files = \
        [f for f in input_dir.iterdir() if f.is_file()]
    input_dir_images = \
        [f for f in input_dir_files if f.name.endswith(('.png', '.jpg', '.webp'))]
    input_dir_nonimages = list(set(input_dir_files) - set(input_dir_images))

    if not input_dir_images:
        print(colored('No images', 'red'))
        return

    Path.mkdir(input_dir / NONIMAGES_DIR_NAME, exist_ok=True)
    nonimages_dir = input_dir / NONIMAGES_DIR_NAME
    if args.nonimages_mv:
        for f in input_dir_nonimages:
            Path.rename(f, nonimages_dir / f.name)

    process_files(input_dir_images, args)

    if not os.listdir(nonimages_dir):
        Path.rmdir(nonimages_dir)


def process_files(input_images, args):
    path_size = Path(args.path + '/Resizeble_' + str(args.size) + '/')
    path_png = Path(args.path + '/pngs/')
    path_png_size = Path(args.path + '/pngs/Resizeble_' + str(args.size) + '/')
    path_png_px = Path(args.path + '/pngs/Smaller_' + str(args.png_size_px) + '/')
    path_png_mib = Path(args.path + '/pngs/Size_' + str(args.png_size_mib) + '/')
    path_png_mib_size = Path(args.path + '/pngs/Size_' + str(args.png_size_mib) + '/' + str(args.size))

    # NOTE path_png on end to properly delete empty dir's
    paths = (path_size,
             path_png_mib_size,
             path_png_mib,
             path_png_px,
             path_png_size,
             path_png)

    for d in paths:
        d.mkdir(exist_ok=True, parents=True)

    for i in input_images:

        print('file :', i.name)

        img = None
        try:
            img = Image.open(i)
        except IOError:
            print(colored("Can't open image", "red"))
            continue
        print(img.size)

        if args.png_sort and i.name.endswith('.png'):
            png_filesize = i.stat().st_size / (1024*1024.0)
            # PNG FILESIZE > args.png_size_mib
            if png_filesize > args.png_size_mib:
                if int(img.size[0]) > args.size or int(img.size[1]) > args.size:
                    i.rename(path_png_mib_size / i.name)
                else:
                    i.rename(path_png_mib / i.name)
            # PNG PX SIZE > args.size
            elif int(img.size[0]) > args.size or int(img.size[1]) > args.size:
                i.rename(path_png_size / i.name)
            # PNG PX SIZE < args.png_size_px
            elif int(img.size[0]) < args.png_size_px and int(img.size[1]) < args.png_size_px:
                i.rename(path_png_px / i.name)
            else:
                i.rename(path_png / i.name)
            continue

        if int(img.size[0]) > args.size or int(img.size[1]) > args.size:
            i.rename(path_size / i.name)
            continue

    for d in paths:
        if len(list(d.iterdir())) == 0:
            d.rmdir()


if __name__ == "__main__":
    main()
    print('done')
