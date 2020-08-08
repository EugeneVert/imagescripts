#!/usr/bin/env python3

import os
import sys
import glob
import argparse
from argparse import RawTextHelpFormatter
from PIL import Image
import ffmpeg

def main():
    parser = argparse.ArgumentParser(description=\
"Generate video from set of images based on maximum images sizes of that set.\n" +\
"Then generates script for imagemagick for convert video back to images.",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of files.')
    parser.add_argument('-e', '--extension', default='', help='File extension to filter by.')
    parser.add_argument('-d', '--dimensions', help='Specify video dimensions')
    args = parser.parse_args()

    # Parse paths
    files = set()
    img_mode = 0
    dir_mode = 0
    for path in args.path:
        if os.path.isfile(path):
            files.add(path)
            img_mode = 1
        else:
            files |= set(glob.glob(path + '/'))
            dir_mode = 1
    if img_mode and dir_mode:
        print('Error, dirs and images passd as input')
        sys.exit()
    if img_mode:
        for f in files:
            print(f)
        files = [os.path.join(os.getcwd(), path) for path in files]
        for f in files:
            print(f)
        files = list(files)
        image2video(files, args.dimensions)
    else:
        for dir in files:
            _files = glob.glob(dir + '*' + args.extension)
            print(_files)
            _files = [os.path.join(os.getcwd(), path) for path in _files]
            print(_files)
            _files = list(_files)
            os.chdir(dir)
            image2video(_files, args.dimensions)
            os.chdir('..')

def image2video(in_files, dimensions=None):
    fps = 2
    crf = 12
    img_ext = os.path.splitext(in_files[0])[1]
    img_dir = os.path.dirname(in_files[0])
    if dimensions:
        dimensions = dimensions.split('x')
    else:
        dimensions = images_size_max(in_files)
    print("dimensions", dimensions)
    WH = dimensions
    (
        ffmpeg
        .input(img_dir + '/*' + img_ext, pattern_type='glob', framerate=fps)
        .filter('scale', WH[0], WH[1], force_original_aspect_ratio='decrease')
        .output(str(crf) + 'out.mp4', crf=crf, preset='veryslow', tune='animation')
        .run()
    )
    print('output')

def images_size_max(images):
    wlist = []
    hlist = []
    for i in images:
        # TODO Is image check
        img = Image.open(i)
        sizes = img.size
        wlist.append(sizes[0])
        hlist.append(sizes[1])
    w_max = list_most_frequent(wlist)
    h_max = list_most_frequent(hlist)
    wh_max = (w_max, h_max)
    return wh_max

def list_most_frequent(List):
    _max = 0
    _res = List[0]
    for i in List:
        freq = List.count(i)
        if freq > _max:
            _max = freq
            _res = i
    return _res

if __name__ == '__main__':
    main()
    print('done')
