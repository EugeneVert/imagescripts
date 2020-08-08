#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import imagehash
from PIL import Image
from termcolor import colored

def main():
    print(sys.argv)
    if len(sys.argv) >= 2:
        print('by argument')
        src_dir = os.path.abspath(sys.argv[1])
    else:
        print('by cwd')
        src_dir = os.getcwd()
    min_images_in_folder = int(input('Min images in folder: '))
    files_in_dir = [f.name for f in os.scandir(src_dir) if f.is_file()]
    img_hash_dict = {}
    for f in files_in_dir:
        try:
            filepath = src_dir + '/' + f
            image = Image.open(filepath)
            image_hash = imagehash.average_hash(image)
            image.close()
            img_hash_dict[filepath] = image_hash
        except:
            print("Error, can't open  " + f)
            continue
    print(colored('Path: ' + src_dir, 'yellow'))
    if(not [f for f in files_in_dir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')

    print(img_hash_dict.keys())
    _img_hash_dict_2, counter = images_process(src_dir, img_hash_dict, min_images_in_folder)
    print('________\n\n\n\n\n IMG PROCESS OTHER')
    images_process(src_dir, _img_hash_dict_2, min_images_in_folder, counter)

def images_process(src_dir, img_hash_dict, min_images_in_folder, counter_for_folders=0):
    imgs_hash_to_process = img_hash_dict
    _img_hash_dict_2 = {}
    while True:
        # print([i[0] for i in img_hash_to_process])
        if len(imgs_hash_to_process) < 1:
            break
        counter_for_folders += 1
        img = list(sorted(imgs_hash_to_process.items()))[0]
        img_name = img[0]
        img_hash = img[1]
        print('IMAGE: ' + img_name)
        # simillars, hash_diff_list = image_find_simillar(img_hash, img_hash_to_process)
        print(imgs_hash_to_process.keys())
        simillars = image_find_simillar(img, imgs_hash_to_process, _img_hash_dict_2)
        print(imgs_hash_to_process.keys())
        print(simillars.keys())
        # mv_flag = None
        for i in list(simillars.items()):
            imgs_hash_to_process.pop(i[0])
            if len(simillars) >= min_images_in_folder:
                # mv_flag = True
                filename = os.path.basename(i[0])
                file_move(src_dir, filename, str(counter_for_folders),
                          'File ' + filename + ' move to ./' + str(counter_for_folders))
                          # '\nHash diff: '+ colored(str(hash_diff_list[num]),'yellow'))
        if len(simillars) < min_images_in_folder:
            counter_for_folders -= 1
        # if mv_flag:
        #     dir_target = src_dir + '/' + str(counter_for_folders)
        #     images_sort_by_hash(simillars, dir_target)
    return _img_hash_dict_2, counter_for_folders

def image_find_simillar(orig, img_hash_dict, _img_hash_dict_2={}, mode=0):
    print('find similar for: ', orig[0])
    img_simillar = {}
    _img_hash_dict_ex = {}
    img_hash_dict_copy = img_hash_dict.copy()
    imageviewer = str(subprocess.check_output('xdg-mime query default image/png', shell=True))\
        [2:-3].split('.')[0]
    # hash_diff_list = []
    for ihlist in sorted(img_hash_dict_copy.items()):
        if ihlist[0] in _img_hash_dict_2.keys():
            continue
        if ihlist[0] in _img_hash_dict_ex.keys():
            continue
        img_hash = ihlist[1]
        orig_hash = orig[1]
        hash_diff = img_hash - orig_hash
        if mode == 1:
            if hash_diff < 5:
                img_simillar[ihlist[0]] = ihlist[1]

        elif hash_diff < 12:
            if hash_diff < 9:
                img_simillar[ihlist[0]] = ihlist[1]
            else:
                print("Hash diff " + str(hash_diff) + ">" + "8" +\
                      '.\nPlease confirm simillarity. Opening images via ' +\
                      imageviewer + ':\nOrig: ' + orig[0] + '\n    ' + ihlist[0])

                sp_orig = subprocess.Popen(imageviewer +\
                                           ' "' + orig[0] + '"',
                                           stdout=subprocess.PIPE, shell=True)
                sp_simi = subprocess.Popen(imageviewer +\
                                           ' "' + ihlist[0] + '"',
                                           stdout=subprocess.PIPE, shell=True)
                inp_are_simillar = input('Are these images simillar? Y(es)/N(o)/E(xclude)')
                inp_are_simillar.lower()
                if inp_are_simillar in ('y', ''):
                    img_simillar[ihlist[0]] = ihlist[1]
                    in_simillars = image_find_simillar(ihlist, img_hash_dict, {}, 1)
                    for i in list(in_simillars.items()):
                        print(i[0])
                        if i[0] not in img_simillar:
                            img_simillar[i[0]] = i[1]
                            _img_hash_dict_ex[i[0]] = i[1]
                elif inp_are_simillar == 'e':
                    sp_orig.kill()
                    sp_simi.kill()
                    break
                else:
                    print('Finding another simillars')
                    ex_simillars = image_find_simillar(ihlist, img_hash_dict, {}, 1)
                    for i in list(ex_simillars.items()):
                        print(i[0])
                        if i[0] in img_simillar:
                            img_simillar.pop(i[0])
                        img_hash_dict.pop(i[0])
                        _img_hash_dict_2[i[0]] = i[1]
                sp_orig.kill()
                sp_simi.kill()
            # hash_diff_list.append(hash_diff)
    return img_simillar #, hash_diff_list

def images_sort_by_hash(simillars, src_dir):
    files_sorted = sorted(simillars.items(), key= lambda i: str(i[1]))
    if not os.path.exists(src_dir + '/out'):
        os.mkdir(src_dir + '/out')
    print([str(x[1]) for x in files_sorted])
    for num, i in enumerate(files_sorted):
        filename = os.path.basename(i[0])
        print(num)
        print('filename: ' + filename)
        print('hash : ' + str(i[1]))
        fileformat = filename.split(".")[-1]
        shutil.copy2(str(src_dir + '/' + filename), str(src_dir + '/out/' + str(num) + '.' + fileformat))


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


if __name__ == '__main__':
    main()
    print('done')
