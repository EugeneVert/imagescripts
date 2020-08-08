#!/usr/bin/env python3

import os
import sys
import glob
import stat
import argparse
from argparse import RawTextHelpFormatter

# getting image size
from PIL import Image
# video creation
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

def image2video(in_files, dimensions=None): # TODO Specify name of out.mp4

    fps = 2
    crf = 12
    img_dir = os.path.dirname(in_files[0])
    fullname = os.path.basename(sorted(in_files)[0])
    name, img_ext = os.path.splitext(fullname)
    WH, img_size_dict = images_size_max(in_files)
    if dimensions:
        WH = dimensions.split('x')
    print("dimensions", dimensions)
    (
        ffmpeg
        .input(img_dir + '/*' + img_ext, pattern_type='glob', framerate=fps)
        .filter('scale', WH[0], WH[1], force_original_aspect_ratio='decrease')
        .filter('pad', WH[0], WH[1], '(ow-iw)/2', '(oh-ih)/2', 'Black') # TODO background color calculation
        .output(name+'.mp4', crf=crf, preset='veryslow', tune='animation')
        .run()
    )
    gen_extract_file(WH, img_size_dict)

    print('output')

def images_size_max(images):
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

def gen_extract_file(WH, img_size_dict): # TODO Specify name of out.mp4 (image2video)
    img_list = [os.path.basename(i) for i in sorted(img_size_dict.keys())]
    fullname = img_list[0]
    name, ext = os.path.splitext(fullname)
    f = open('extract.sh', 'w')
    f.write('#!/usr/bin/env bash')
    f.write("""
for i in *.mp4
do
    dirname="${i%.*}"
    mkdir "$dirname"
    ffmpeg -i "$i" -r 2 -q:v 1 -qmin 1 -qmax 1 ./"$dirname"/img%03d.png
done
""")
    f.write('\n\n\n')
    f.write('cd ./' + name + ' || exit\n')
    print(WH)
    print(img_size_dict)
    resize_dict = gen_resize_dict(WH, img_size_dict)
    inv_resize_dict = {}
    for key, value in sorted(resize_dict.items()):
        if value not in inv_resize_dict:
            inv_resize_dict[value] = [key]
        else:
            inv_resize_dict[value].append(key)
    print(inv_resize_dict)
    for i in inv_resize_dict.items():
        f.write('mogrify ' +\
                ' -gravity Center ' +\
                '-extent ' + str(i[0][0])+'x'+str(i[0][1])+'! ' +\
                " ".join(map(lambda x: '"'+("img{:03d}"+ext).format(img_list.index(x)+1)+'"', i[1])) + '\n'
                )
    f.write('cd ..')

    st = os.stat('extract.sh')
    os.chmod('extract.sh', st.st_mode | stat.S_IEXEC)
   
def list_to_str(list:list):
    s = str()
    for i in list:
        formated = '"'+ str(i) +'" '
        s += formated
    return s
def gen_resize_dict(WH, img_size_dict:dict):
    resize_dict = {}
    for i in img_size_dict.items():
        ratio_w = WH[0]/i[1][0]
        ratio_h = WH[1]/i[1][1]
        if ratio_h == 1 and ratio_w == 1:
            continue
        print([ratio_w, ratio_h])
        ratio_best = min(ratio_w, ratio_h)
        print(ratio_best)
        i_new_WH = (int(i[1][0] * ratio_best),
                    int(i[1][1] * ratio_best))
        if i_new_WH < (i[1][0], i[1][1]):
            print('EEEEEEEEEEEEEE')
        name = os.path.basename(i[0])
        resize_dict[name] = i_new_WH
    return resize_dict



if __name__ == '__main__':
    main()
    print('done')
