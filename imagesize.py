#!/usr/bin/env python3
#    _                                       _
#   (_)_ __ ___   __ _  __ _  ___  ___   ___(_)_______
#   | | '_ ` _ \ / _` |/ _` |/ _ \/ __| / __| |_  / _ \
#   | | | | | | | (_| | (_| |  __/\__ \ \__ \ |/ /  __/
#   |_|_| |_| |_|\__,_|\__, |\___||___/ |___/_/___\___|
#                      |___/
#                 _
#    _ __ ___  __| |_   _  ___ ___ _ __
#   | '__/ _ \/ _` | | | |/ __/ _ \ '__|
#   | | |  __/ (_| | |_| | (_|  __/ |
#   |_|  \___|\__,_|\__,_|\___\___|_|
#
# 2020 Eugene Vert; eugene.a.vert@gmail.com

import os
import sys
import argparse
import shutil
import re
from typing import List
from PIL import Image, ImageStat
from termcolor import colored

def main():
    parser = argparse.ArgumentParser(description='Reduce images size',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', nargs='?', help="Dir with images")
    parser.add_argument('-ask', action='store_true', help='ask resize for each resizeble')
    parser.add_argument('-nonimg', action='store_true', help="""don't move non-images to "mv" folder""")
    parser.add_argument('-kpng', action='store_true', help="keep (Don't convet) png")
    parser.add_argument('-bnwjpg', action='store_true', help="don't convert Black&White jpg's to png")
    parser.add_argument('-msize', dest='fsize_min', default="150K", help="min filesize to process. (B | K | M) (K=2^10)")
    parser.add_argument('-c:f', dest='convert_format', type=str, help="set 'convert to' Format for all files")
    parser.add_argument('-c:q', dest='convert_quality', type=int, default=int(90), help='non-jpg Convert Quality \n (default: %(default)s) (tip: A3&A4 paper 4961/3508/2480/1754/1240)')
    parser.add_argument('-resize', dest='size', type=int, default=int(3508), help='resize to size. \n (default: %(default)s)')
    parser.add_argument('-o', dest="out_dir", type=str, default=str('./test'), help="output dir \n (default: %(default)s)")
    args = parser.parse_args()

    if args.path:
        print('by argument')
        src_dir = os.path.abspath(args.path)
    else:
        print('by cwd')
        src_dir = os.getcwd()

    filesindir = [f.name for f in os.scandir(src_dir) if f.is_file()]
    print(colored('Path: ' + src_dir, 'yellow'))
    if(not [f for f in filesindir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')

    files_process(src_dir, filesindir, args)


class Img:
    def __init__(self, f):
        self.name: str = f
        self.img: Image.Image = Image.open(f)
        self.size = self.img.size
        self.atime = os.path.getatime(f)
        self.mtime = os.path.getmtime(f)


def files_process(src_dir: str, filesindir: List[str], args):
    out_dir = os.path.abspath(args.out_dir) + '/'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        print(colored('Creating dir ' + args.out_dir, 'green'))

    for f in filesindir:
        try:
            img = Img(f)
        except Exception:
            if not args.nonimg:
                print(colored("Moving to mv dir", 'red'))
                file_move(src_dir, f, 'mv')
            continue

        print(f)
        print(img.size)
        if f.endswith('.png') and img.img.get_format_mimetype() == 'image/apng':
            if not args.nonimg:
                file_move(src_dir, f, 'mv')
            continue

        filesize_min_to_process = parse_size(args.fsize_min)
        if os.path.getsize(f) < filesize_min_to_process and not f.endswith('png'):
            print(colored("Size too low\nCopying to out dir", 'blue'))
            shutil.copy2(f, args.out_dir)
            continue

        quality = args.convert_quality
        if args.convert_format:
            img_save(img, out_dir, quality, args.convert_format)
            continue

        size_target = args.size
        if size_target:
            if ((int(img.size[0]) > size_target) or
                    (int(img.size[1]) > size_target)):
                if (not args.ask) or input(colored('resize? y/n ', 'yellow')).lower() == 'y':
                    size_target = size_target, size_target
                    print(colored('making image smaller', 'yellow'))
                    img.img.thumbnail(size_target, Image.LANCZOS)

        if f.endswith('.png'):
            if args.kpng:
                img_save(img, out_dir, quality, 'png')
            elif image_has_transparency(img.img):
                img_save(img, out_dir, quality, 'webp')
            else:
                img_save(img, out_dir, quality, 'jpg')
        elif f.endswith('.jpg'):
            if not args.bnwjpg and image_iscolorfull(img.img) in ('grayscale', 'blackandwhite'):
                print('Black and white image, convert jpg to png')
                img_save(img, out_dir, quality, 'png')
            else:
                img_save(img, out_dir, quality, 'jpg')
        else:
            print(colored(str(img.img.format).lower(), 'blue'))
            print(colored("Copying to out dir", 'blue'))
            shutil.copy2(f, args.out_dir)


def img_save(img: Img, out_dir, quality, ext: str):
    path_split = os.path.splitext(img.name)
    out_path = out_dir + path_split[0] + '.' + ext
    i_ext = path_split[1][1:]
    # png  -> png, jpg, webp
    # jpg  -> png, jpg, webp
    # webp -> jpg, webp

    # JPEG
    if i_ext == 'jpg':
        if ext == 'jpg':
            img.img.save(out_path, quality=90, subsampling='keep', optimize=True)
        elif ext == 'png':
            img.img = img.img.convert(mode='P', palette=Image.ADAPTIVE)
            img.img.save(out_path, optimize=True)
        elif ext == 'webp':
            img.img.save(out_path, quality=quality + 2, method=6)
    # PNG
    elif i_ext == 'png':
        if ext == 'png':
            img.img.save(out_path, optimize=True)
        elif ext == 'jpg':
            img.img = img.img.convert('RGB')
            img.img.save(out_path, quality=quality, subsampling=1, optimize=True)
        elif ext == 'webp':
            img.img.save(out_path, quality=quality + 2, method=6)
    # WEBP
    elif i_ext == 'webp':
        if ext == 'webp':
            img.img.save(out_path, quality=quality + 2, method=6)
        elif ext == 'jpg':
            img.img.save(out_path, quality=quality, subsampling=0, optimize=True)

    os.utime(out_path, (img.atime, img.mtime))

   
def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


def parse_size(size: str):
    units = {"B": 1, "K": 2**10, "M": 2**20}
    size = size.upper()
    if not re.match(r' ', size):
        size = re.sub(r'([BKM]?)$', r' \1', size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * units[unit])

# https://stackoverflow.com/questions/20068945/detect-if-image-is-color-grayscale-or-black-and-white-with-python-pil
# By Noah Whitman
def image_iscolorfull(image, thumb_size=40, MSE_cutoff=22, adjust_color_bias=True):
    pil_img = image
    bands = pil_img.getbands()
    if bands == ('R','G','B') or bands== ('R','G','B','A'):
        thumb = pil_img.resize((thumb_size,thumb_size))
        SSE, bias = 0, [0,0,0]
        if adjust_color_bias:
            bias = ImageStat.Stat(thumb).mean[:3]
            bias = [b - sum(bias)/3 for b in bias ]
        for pixel in thumb.getdata():
            mu = sum(pixel)/3
            SSE += sum((pixel[i] - mu - bias[i])*(pixel[i] - mu - bias[i]) for i in [0,1,2])
        MSE = float(SSE)/(thumb_size*thumb_size)
        if MSE <= MSE_cutoff:
            print("Grayscale")
            return "grayscale"
        else:
            print("Color")
            return "color"
        print("( MSE=",MSE,")")
    elif len(bands)==1:
        print("Black and white", bands)
        return "blackandwhite"
    else:
        print("Don't know...", bands)
        return "unknown"


def image_has_transparency(image: Image.Image):
    if len(image.getbands()) < 4: # if 'A' not in image.getbands()
        return False
    return True if image.getextrema()[3][0] != 255 else False


if __name__ == '__main__':
    main()
