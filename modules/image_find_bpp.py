#!/usr/bin/env python3
#
# 2021 Eugene Vert; eugene.a.vert@gmail.com

import os
import argparse

from pathlib import Path

from PIL import Image
from termcolor import colored

NONIMAGES_DIR_NAME = './mv'


def argument_parser(*args):
    parser = argparse.ArgumentParser(
        description='Reduce images size',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        'path', nargs='?',
        help="dir with images")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", type=float,
                       help="Move images with bpp < BPP")
    group.add_argument("-b", type=float,
                       help="Move images with bpp > BPP")
    parser.add_argument("-mv", action="store_true",
                        help="Move non-images (not png, jpg, webp)")
    args = parser.parse_args(*args)
    return args


def load_image(i):
    return Image.open(i)


def sort_by_bpp(image, path_bpp, args):
    filename = Path(image.filename)
    px_count = image.size[0] * image.size[1]
    filesize = Path(image.filename).stat().st_size
    bpp = filesize*8/px_count

    print(f"File: {filename.name}\n bpp: {bpp}")

    mode = "lesser" if args.l else "bigger"
    if mode == "lesser":
        if bpp < args.l:
            print(f"Move to {path_bpp.name}")
            filename.rename(path_bpp / filename.name)
    else:
        if bpp > args.b:
            print(f"Move to {path_bpp.name}")
            filename.rename(path_bpp / filename.name)


def main(*args):
    args = argument_parser(*args)
    args.bpp = args.l if args.l else args.b

    if args.path:
        print('by argument')
        input_dir = Path(args.path)
    else:
        print('by cwd')
        input_dir = Path.cwd()
    print(colored('Path: ' + input_dir.as_posix(), 'yellow'))

    input_dir_files = \
        [f for f in input_dir.iterdir() if f.is_file()]
    input_dir_images = \
        [f for f in input_dir_files if f.name.endswith(('.png', '.jpg', '.webp'))]
    input_dir_nonimages = list(set(input_dir_files) - set(input_dir_images))

    if not input_dir_images:
        print(colored('No images', 'red'))
        return

    Path.mkdir(input_dir / NONIMAGES_DIR_NAME, exist_ok=True)
    path_nonim = Path(input_dir / NONIMAGES_DIR_NAME)
    Path.mkdir(input_dir / str(args.bpp), exist_ok=True)
    path_bpp = Path(input_dir / str(args.bpp))
    # path_nonim = input_dir / NONIMAGES_DIR_NAME

    if args.mv:
        for i in input_dir_nonimages:
            Path.rename(i, path_nonim / i)
    for i in input_dir_images:
        img = load_image(i)
        sort_by_bpp(img, path_bpp, args)

    if not os.listdir(path_nonim):
        Path.rmdir(path_nonim)
    if not os.listdir(path_bpp):
        Path.rmdir(path_bpp)


if __name__ == "__main__":
    main()
    print('done')
