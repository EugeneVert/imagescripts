#!/usr/bin/env python3
#
# 2020 Eugene Vert; eugene.a.vert@gmail.com

import os
import sys
from PIL import Image
from termcolor import colored


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
    if(not [f for f in files_in_dir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')

    img_c_min = int(input('Min images count to mv '))
    input('Press any key')

    os.chdir(dir_target)
    images_find_eq_res(files_in_dir, dir_target, img_c_min)


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


def images_find_eq_res(files_in_dir, dir_target, img_c_min):
    known_images_dict = dict()
    for i in files_in_dir:
        img = None
        print('file: ', i)
        if i.endswith(('.png', '.jpg')):
            try:
                img = Image.open(i)
            except:
                print("can't open open image")
                continue
        else:
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
