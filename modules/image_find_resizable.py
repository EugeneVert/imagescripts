#!/usr/bin/env python3
#
# 2020 Eugene Vert; eugene.a.vert@gmail.com

import os
import sys
from PIL import Image
from termcolor import colored
from ncurses.cursesmultisel import DisplayMenu


OPTIONS = [
    ['sort png', 'sw'],
    # ['mv png less that', 'txt', '1024'],
    ['mv png size MiB', 'txt', '1.2'],
    ['mv png size px', 'txt', '1754'],
    ['mv img size px', 'txt', '3508'],
    ['move non-images to ./mv', 'sw'],
]

def confirmprompt(promptin):
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(promptin +" [Y/N]? ").lower()
    return answer == "y"


def file_move(srcdir: str, filename: str, dirname: str, msg: str = ''):
    print(msg)
    if not os.path.exists(srcdir + '/' + dirname):
        os.mkdir(srcdir + '/' + dirname)
    os.rename(srcdir + '/' + filename, srcdir + '/' + dirname + '/' + filename)


def process_files(filesindir, targetdir, sizetarg, png_sort,
                  png_sizetarg_MiB, png_sizetarg_px, nonimagetomv):
    for i in filesindir:
        img = None

        print('file :', i)
        try:
            if i.endswith(('.png', '.jpg')):
                img = Image.open(i)
        except:
            print(colored("Can't open image", "red"))
            continue

        # Move non-images/animations to 'mv' dir
        if not i.endswith('.jpg'):
            if(
                    not i.endswith('.png') or
                    i.endswith('.png') and img.get_format_mimetype() == 'image/apng'
            ):
                if nonimagetomv:
                    file_move(targetdir, i, 'mv',
                              colored('Not an png/jpg, moving to mv directory', 'red'))
                continue

        path_resizebles = targetdir + '/Resizeble_' + str(sizetarg) + '/'
        if not os.path.exists(path_resizebles):
            os.mkdir(path_resizebles)
            print(colored('Creating dir ./Resizeble_' + str(sizetarg), 'green'))
        path_png_mv = targetdir + '/pngs/'
        if png_sort and not os.path.exists(path_png_mv):
            os.mkdir(path_png_mv)
            print(colored('Creating dir ./pngs/', 'green'))
        # path_png_mv_resizebles = targetdir + '/pngs/' + str(png_sizetarg) + '/'
        # if png_sort and not os.path.exists(path_png_mv_resizebles):
        #     os.mkdir(path_png_mv_resizebles)
        #     print(colored('Creating dir ./pngs/Resizeble_' + str(png_sizetarg), 'green'))
        path_png_mv_size = targetdir + '/pngs/Size_' + str(png_sizetarg_MiB) + '/'
        if png_sort and not os.path.exists(path_png_mv_size):
            os.mkdir(path_png_mv_size)
            print(colored('Creating dir ./pngs/Resizeble_' + str(png_sizetarg_MiB), 'green'))

        imgsizer = img.size
        print(imgsizer)

        if png_sort:
            if i.endswith('.png'):
                png_filesize = os.path.getsize(targetdir + '/' + i) / (1024*1024.0)
                # if int(imgsizer[0]) > png_sizetarg or int(imgsizer[1]) > png_sizetarg:
                #     file_move(targetdir, i, 'pngs/Resizeble_' + str(png_sizetarg),
                #               'To pngs/Resizeble_.../')
                #     continue
                if png_filesize > png_sizetarg_MiB:
                    if int(imgsizer[0]) > sizetarg or int(imgsizer[1]) > sizetarg:
                        file_move(targetdir, i, 'pngs/Size_' + str(png_sizetarg_MiB) +
                                  '/Resizeble_' + str(sizetarg),
                                  colored('To pngs/Size_...', 'blue') +
                                  colored('/Resizeble_...', 'yellow'))
                        continue
                    if int(imgsizer[0]) < png_sizetarg_px and int(imgsizer[1]) < png_sizetarg_px:
                        file_move(targetdir, i, 'pngs/Size_' + str(png_sizetarg_MiB)
                                  + '/Smaller_' + str(png_sizetarg_px),
                                  colored('To pngs/Size...', 'blue') +
                                  colored('/Smaller...', 'cyan'))
                        continue
                    file_move(targetdir, i, 'pngs/Size_' + str(png_sizetarg_MiB),
                              colored('To pngs/Size_.../', 'blue'))
                    continue
                file_move(targetdir, i, 'pngs', 'To pngs/')
                continue
            if i.endswith('.jpg'):
                if int(imgsizer[0]) > sizetarg or int(imgsizer[1]) > sizetarg:
                    file_move(targetdir, i, 'Resizeble_' + str(sizetarg),
                              colored('To Resizeble_.../', 'yellow'))
                    continue
        else:
            if int(imgsizer[0]) > sizetarg or int(imgsizer[1]) > sizetarg:
                file_move(targetdir, i, 'Resizeble_' + str(sizetarg),
                          'To Resizeble_.../')


def main(options, argv):
    activeopt = list()
    print(argv)
    if len(argv) >= 2:
        print('by argument')
        targetdir = os.path.abspath(argv[1])
    else:
        print('by cwd')
        targetdir = os.getcwd()

    filesindir = [f.name for f in os.scandir(targetdir) if f.is_file()]
    print(colored('Path: ' + targetdir, 'yellow'))
    if(not [f for f in filesindir if f.endswith(('.png', '.jpg'))]):
        print('\033[4m' + colored('No images', 'red') + '\033[0m')
        sys.exit('')

    input('Press any key')

    DisplayMenu(options, activeopt)
    if not activeopt:
        return
    print(activeopt)

    sizetarg = ''
    png_sort = 0
    # png_sizetarg = ''
    png_sizetarg_MiB = ''
    png_sizetarg_px = ''
    nonimagetomv = 0

    for element in activeopt:
        if 'mv img size px' in element:
            sizetarg = int(element[1])
            print('sizetarg', sizetarg)
        # if 'mv png less that' in element:
        #     png_sizetarg = int(element[1])
        #     print('png_sizetarg', png_sizetarg)
        if 'mv png size MiB' in element:
            png_sizetarg_MiB = float(element[1])
            print('png_sizetarg_MiB', png_sizetarg_MiB)
        if 'mv png size px' in element:
            png_sizetarg_px = int(element[1])
            print('png_sizetarg_px', png_sizetarg_px)
    if not sizetarg:
        print(colored('Error, no resize target! default - 3508 set', 'red'))
        sizetarg = 3508
    # if not png_sizetarg:
    #     print(colored('Error, no png resize target! default - 1024 set', 'red'))
    #     png_sizetarg = 1024
    if not png_sizetarg_MiB:
        print(colored('Error, no png size MiB target! default - 1 MiB set', 'red'))
        png_sizetarg_MiB = 1
    if not png_sizetarg_px:
        print(colored('Error, no png size px target! default - 1024 px set', 'red'))
        png_sizetarg_px = 1024
    if 'sort png' in activeopt:
        png_sort = 1
    if 'move non-images to ./mv' in activeopt:
        nonimagetomv = 1
    os.chdir(targetdir)
    process_files(filesindir,
                  targetdir,
                  sizetarg,
                  png_sort,
                  # png_sizetarg,
                  png_sizetarg_MiB,
                  png_sizetarg_px,
                  nonimagetomv)


if __name__ == "__main__":
    args = sys.argv
    main(OPTIONS, args)
    print('done')
