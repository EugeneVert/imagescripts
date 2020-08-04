#!/usr/bin/env python3
#
import os
import sys
import imagehash
from PIL import Image
from termcolor import colored

def main():
    print(sys.argv)
    if len(sys.argv) >= 2:
        print('by argument')
        dir_target = os.path.abspath(sys.argv[1])
    else:
        print('by cwd')
        dir_target = os.getcwd()
    files_in_dir = [f.name for f in os.scandir(dir_target) if f.is_file()]
    images_in_dir = []
    for f in files_in_dir:
        try:
            image = Image.open(dir_target + '/' + f)
            images_in_dir.append(image)
        except:
            print("Error, can't open  " + f)
            continue
    print(colored('Path: ' + dir_target, 'yellow'))
    if(not [f for f in files_in_dir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')
    print([i.filename for i in images_in_dir])
    images_process(dir_target, images_in_dir)

def images_process(dir_target, images_in_dir):
    images_to_process = images_in_dir
    dir_count = 0
    while True:
        if len(images_to_process) < 1:
            break
        dir_count += 1
        img = images_to_process[0]
        print('IMAGE: ' + img.filename)
        img_hash = imagehash.average_hash(img)
        simillars = image_find_simillar(img_hash, images_to_process)
        for i in simillars:
            images_to_process.remove(i)
            if len(simillars) > 3:
                filename = os.path.basename(i.filename)
                file_move(dir_target, filename, str(dir_count),
                          'File ' + filename + ' move to ./' + str(dir_count))

def image_find_simillar(orig_hash, images_list):
    img_simillar = []
    for img in images_list:
        img_hash = imagehash.average_hash(img)
        if img_hash - orig_hash < 10:
            img_simillar.append(img)
    return img_simillar


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


if __name__ == '__main__':
    main()
    print('done')
