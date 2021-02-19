#!/usr/bin/env python3
#
# 2020 Eugene Vert; eugene.a.vert@gmail.com

import os
import sys
import glob
import shutil
import argparse
from argparse import RawTextHelpFormatter

# getting image size
from PIL import Image
# video creation
import ffmpeg
# orig of resized images arhiving
import zipfile


def main(*args):
    parser = argparse.ArgumentParser(description="\
Generate a video from a set of images. The Size of the video based on the average images size. \n\n\
\
Creates a script for imagemagick to convert the video back to the images.\n\
The resized images to a smaller size, the original image names, a rename script will be stored in .zip file.",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of files.')
    parser.add_argument('-e', '--extension', default='', help='File extension to filter by.')
    parser.add_argument('-d', '--dimensions', help='Specify video dimensions')
    parser.add_argument('-b', '--background', default='Black', help='Specify video background')
    parser.add_argument('--noarchive', action='store_true', help="Don't create archive with non-resized original images")
    parser.add_argument('-crf', dest='crf', type=int, default=12, help='Specify video CRF')
    parser.add_argument('-r', '--fps', dest='fps', type=int, default=2, help='Specify video framerate')  # NOTE fps default value check on gen_extract_file in image2video
    args = parser.parse_args(*args)

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
        files = list(files)
        image2video(files, args, args.dimensions)
    else:
        for dir in files:
            _files = glob.glob(dir + '*' + args.extension)
            _files = [os.path.join(os.getcwd(), path) for path in _files]

            owd = os.getcwd()
            os.chdir(dir)
            image2video(_files, args, args.dimensions)
            os.chdir(owd)


def image2video(in_files, args, dimensions=None):  # TODO Specify name of out.mp4
    background = args.background
    crf = args.crf
    fps = args.fps
    img_dir = os.path.dirname(in_files[0])
    fullname = os.path.basename(sorted(in_files)[0])
    # set output filename same as first image
    name, img_ext = os.path.splitext(fullname)
    # find most frequent size
    WH, img_size_dict = images_size_targ(in_files)
    if dimensions:
        WH = tuple(map(int, dimensions.split('x')))
    print("CRF", crf)
    print('\n\n\n')
    (
        ffmpeg
        .input((img_dir + '/*' + img_ext).replace('[','\[').replace(']','\]'), pattern_type='glob', framerate=fps)
        .filter('scale', WH[0], WH[1], force_original_aspect_ratio='decrease')
        .filter('pad', WH[0], WH[1], '(ow-iw)/2', '(oh-ih)/2', background)  # TODO background color calculation
        .output(name+'.mp4', crf=crf, preset='veryslow', tune='animation', deblock='-3:-3')
        .run()
    )
    gen_extract_file(WH, img_size_dict, name, args)


def images_size_targ(images):
    img_size_dict = {}
    for i in images:
        # TODO Is image check
        with Image.open(i) as img:
            img_size_dict[i] = img.size
    w_max = list_most_frequent([i[0] for i in img_size_dict.values()])
    h_max = list_most_frequent([i[1] for i in img_size_dict.values()])
    wh_max = (w_max, h_max)
    return wh_max, img_size_dict


def list_most_frequent(List):
    _max = 0
    _res = List[0]
    for i in List:
        freq = List.count(i)
        if freq > _max:
            _max = freq
            _res = i
    return _res


def gen_extract_file(WH, img_size_dict, out_dname, args):  # TODO Specify name of out.mp4 (image2video)
    fps = args.fps
    img_list = [os.path.basename(i) for i in sorted(img_size_dict.keys())]
    fullname = img_list[0]
    name, ext = os.path.splitext(fullname)

    os.makedirs(out_dname, exist_ok=True)

    f = open(out_dname + '/_names.txt', 'w')
    for i in sorted(img_size_dict.keys()):
        f.write(os.path.basename(i) + '\n')
    f.close()

    f = open('_frames.sh', 'w')
    f.write('#!/usr/bin/env bash\n')
    f.write("""
for i in *.mp4
do
    if [ -L "$i" ]
    then continue; fi
    dirname="${{i%.*}}"
    mkdir "$dirname"
    ffmpeg -i "$i" -vsync 2 ./"$dirname"/img%03d.png
done
""".format(fps))
    f.close()

    print('rename.sh')
    f = open(out_dname + '/_rename.sh', 'w')
    f.write("""ls ./img* | paste -d' ' - "./_names.txt" | while read a b; do mv "$a" "${b%.*}.${a##*.}"; done""")
    f.close()

    if not args.noarchive:
        resize_dict = gen_resize_dict(WH, img_size_dict, img_list, out_dname)
    else: resize_dict = ''
    inv_resize_dict = {}

    if resize_dict:
        f = open(out_dname + '/_transform.sh', 'w')
        f.write('\n')
        f.write('if [ -d "./' + name + '" ]; then ')
        f.write('cd "./' + name + '" || exit ; ')
        for key, value in sorted(resize_dict.items()):
            if value not in inv_resize_dict:
                inv_resize_dict[value] = [key]
            else:
                inv_resize_dict[value].append(key)
        for i in inv_resize_dict.items():
            f.write('mogrify ' +
                    ' -gravity Center' +
                    ' -quality 95' +
                    # TODO Lossles images -> resize -> lossy
                    ' -extent ' + str(i[0][0])+'x'+str(i[0][1])+'! ' +
                    " ".join(map(lambda x: '"' + ("img{:03d}.jpg").format(img_list.index(x) + 1) + '"', i[1])) + ' ; '
                    )
        f.write('cd .. ; ')
        f.write('fi')
        f.close()
    path = os.path.dirname(os.path.abspath(args.path[0]))
    make_archive(path, out_dname)


def list_to_str(src: list):
    s = str()
    for i in src:
        formated = '"'+ str(i) +'" '
        s += formated
    return s


def gen_resize_dict(WH: tuple, img_size_dict: dict, img_list: list, out_dname):
    resize_dict = {}
    img_size_list = list(img_size_dict.items())
    path = os.path.dirname(img_size_list[0][0])
    for i in img_size_list:
        name = os.path.basename(i[0])
        outname = ("img{:03d}.jpg").format(img_list.index(name) + 1)
        ratio_w = WH[0]/i[1][0]
        ratio_h = WH[1]/i[1][1]
        if ratio_h == 1 and ratio_w == 1:
            continue
        print("filename " + name + '\n' + outname)
        ratio_best = min(ratio_w, ratio_h)
        print(ratio_best)
        i_new_WH = (int(i[1][0] * ratio_best),
                    int(i[1][1] * ratio_best))
        if ratio_best > 1.15 or ratio_best < 0.95:
            shutil.copy2(i[0], path + '/' + out_dname + '/' + outname)
        resize_dict[name] = i_new_WH
    print('Converting _d to jpg')
    after_gen(path, out_dname)
    return resize_dict


def after_gen(path, out_dname):
    files = glob.glob(out_dname + '/*.jpg')
    print(files)
    for f in files:
        img = Image.open(f)
        img_name, ext = os.path.splitext(f)
        img.save(img_name + ".jpg", format="jpeg", quality=94)
        print('done for image', f)


def make_archive(path, path_d):
    if os.listdir(path_d):
        shutil.make_archive(path_d, 'zip', path, os.path.basename(path_d) + '/')
    shutil.rmtree(path_d)


if __name__ == '__main__':
    main()
