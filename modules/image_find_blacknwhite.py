#!/usr/bin/env python3
#
# 2021 Eugene Vert; eugene.a.vert@gmail.com

"""Script to find images with size bigger then given

This script can sort 'resizeble' images to folders based on their property's.
Png's can be sorted separately, based on their resolution and file-size
"""

import argparse
from pathlib import Path

from PIL import Image
from termcolor import colored
from PIL import ImageStat


NONIMAGES_DIR_NAME = './mv'


def argument_parser(*args):
    parser = argparse.ArgumentParser(description="\
        Find black and white images",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', nargs='?',
                        help='Path of a dir.')

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

    if not input_dir_images:
        print(colored('No images', 'red'))
        return

    process_files(input_dir_images, args)


def process_files(input_images, args):
    path_bnw = Path(args.path + '/blacknwhite')

    paths = (path_bnw,)
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

        if image_iscolorfull(img) in ('bnw', 'grayscale'):
            i.rename(path_bnw / i.name)
            continue

    for d in paths:
        if len(list(d.iterdir())) == 0:
            d.rmdir()


# https://stackoverflow.com/questions/20068945/detect-if-image-is-color-grayscale-or-black-and-white-with-python-pil
def image_iscolorfull(image, thumb_size=40, MSE_cutoff=22, adjust_color_bias=True):
    pil_img = image
    bands = pil_img.getbands()
    if bands == ('R', 'G', 'B') or bands == ('R', 'G', 'B', 'A'):
        thumb = pil_img.resize((thumb_size, thumb_size))
        SSE, bias = 0, [0, 0, 0]
        if adjust_color_bias:
            bias = ImageStat.Stat(thumb).mean[:3]
            bias = [b - sum(bias)/3 for b in bias]
        for pixel in thumb.getdata():
            mu = sum(pixel)/3
            SSE += sum((pixel[i] - mu - bias[i])*(pixel[i] - mu - bias[i]) for i in [0, 1, 2])
        MSE = float(SSE)/(thumb_size*thumb_size)
        if MSE <= MSE_cutoff:
            print("Grayscale")
            return "grayscale"
        else:
            return "color"
        print("( MSE=", MSE, ")")
    elif len(bands) == 1:
        print("Black and white", bands)
        return "bnw"
    else:
        print("Don't know...", bands)
        return "unknown"


if __name__ == "__main__":
    main()
    print('done')
