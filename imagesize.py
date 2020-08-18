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
from typing import List
from PIL import Image
from termcolor import colored

def main():
    parser = argparse.ArgumentParser(description='Reduce images size',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', nargs='?', help="Dir with images \n")
    parser.add_argument('-ask', action='store_true', help='Ask resize for each resizeble \n')
    parser.add_argument('-nonimg', action='store_true', help="""don't move non images to "mv" folder \n""")
    parser.add_argument('-kpng', action='store_true', help="Keep (Don't convet) png \n")
    parser.add_argument('-c:q', dest='quality', default=int(90), help='Png convert quality \n (default: %(default)s)')
    parser.add_argument('-resize', dest='size', type=int, default=int(3508), help='Resize to size. \n (default: %(default)s)')
    parser.add_argument('-o', dest="out_dir", type=str, default=str('./test'), help="Output dir \n (default: %(default)s)")
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

        size_target = args.size
        if size_target:
            if ((int(img.size[0]) > size_target) or
                    (int(img.size[1]) > size_target)):
                if (not args.ask) or input(colored('resize? y/n ', 'yellow')).lower() == 'y':
                    size_target = size_target, size_target
                    print(colored('making image smaller', 'yellow'))
                    img.img.thumbnail(size_target, Image.LANCZOS)

        quality = args.quality
        if f.endswith('.png'):
            if args.kpng:
                img_save(img, out_dir, quality, 'png')
            else:
                img_save(img, out_dir, quality, 'jpg')
        if f.endswith('.jpg'):
            img_save(img, out_dir, quality, 'jpg')

def img_save(img: Img, out_dir, quality, ext: str):
    path_split = os.path.splitext(img.name)
    out_path = out_dir + path_split[0] + '.' + ext
    i_ext = path_split[1][1:]
    # png  -> png, jpg, webp
    # jpg  -> jpg, webp
    # webp -> jpg, webp

    # JPEG
    if i_ext == 'jpg':
        if ext == 'jpg':
            img.img.save(out_path, quality=95, subsampling='keep', optimize=True)
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

if __name__ == '__main__':
    main()
