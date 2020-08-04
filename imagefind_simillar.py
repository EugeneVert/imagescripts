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
    min_images_in_folder = int(input('Min images in folder: '))
    files_in_dir = [f.name for f in os.scandir(dir_target) if f.is_file()]
    img_hash_list = []
    for f in files_in_dir:
        try:
            filepath = dir_target + '/' + f
            image = Image.open(filepath)
            image_hash = imagehash.average_hash(image)
            image.close()
            img_hash_list.append([filepath, image_hash])
        except:
            print("Error, can't open  " + f)
            continue

    print(colored('Path: ' + dir_target, 'yellow'))
    if(not [f for f in files_in_dir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')

    print([i[0] for i in img_hash_list])
    images_process(dir_target, img_hash_list, min_images_in_folder)

def images_process(dir_target, img_hash_list, min_images_in_folder):
    img_hash_to_process = img_hash_list
    dir_count = 0
    while True:
        # print([i[0] for i in img_hash_to_process])
        if len(img_hash_to_process) < 1:
            break
        dir_count += 1
        img = img_hash_to_process[0][0]
        print('IMAGE: ' + img)
        img_hash = img_hash_list[0][1]
        # simillars, hash_diff_list = image_find_simillar(img_hash, img_hash_to_process)
        simillars = image_find_simillar(img_hash, img_hash_to_process)
        for num, i in enumerate(simillars):
            img_hash_to_process.remove(i)
            if len(simillars) >= min_images_in_folder:
                filename = os.path.basename(i[0])
                file_move(dir_target, filename, str(dir_count),
                          'File ' + filename + ' move to ./' + str(dir_count))
                          # '\nHash diff: '+ colored(str(hash_diff_list[num]),'yellow'))
        if len(simillars) < min_images_in_folder:
            dir_count -= 1

def image_find_simillar(orig_hash, img_hash_list):
    img_simillar = []
    # hash_diff_list = []
    for ihlist in img_hash_list:
        img_hash = ihlist[1]
        hash_diff = img_hash - orig_hash
        if hash_diff < 9:
            img_simillar.append(ihlist)
            # hash_diff_list.append(hash_diff)
    return img_simillar #, hash_diff_list


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


if __name__ == '__main__':
    main()
    print('done')
