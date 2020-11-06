#!/usr/bin/env python3

# 2020 Eugene Vert; eugene.a.vert@gmail.com

import os, argparse, shutil, re, subprocess
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageStat
from termcolor import colored


NONIMAGES_DIR = Path('./mv')

if shutil.which('zopflipng'):
    from multiprocessing import cpu_count
    from multiprocessing import Pool
    pool_dict = {}
    ZOPFLI = True
else:
    ZOPFLI = False
def call_zopflipng(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


def argument_parser(*args):
    parser = argparse.ArgumentParser(description='Reduce images size',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', nargs='?',
                        help="dir with images")
    parser.add_argument('-o', dest="out_dir", type=str, default=str('./test'),
                        help="output dir \n    (default: %(default)s)")
    parser.add_argument('-c:f', dest='convert_format', type=str,
                        help="set output format for All files")
    parser.add_argument('-c:q', dest='convert_quality', type=int, default=int(92),
                        help='compression level \n    (default: %(default)s)')
    parser.add_argument('-lossless', action='store_true',
                        help="lossless webp")
    parser.add_argument('-ask', action='store_true',
                        help='ask resize for each resizeble')
    parser.add_argument('-resize', dest='size', type=int, default=int(3508),
                        help='resize to size. \n    (default: %(default)s)' +
                        '\n    (tip: A3&A4 paper 4961/3508/2480/1754/1240)\n' +
                        '_____________________________________________\n\n')
    parser.add_argument('-bnwjpg', action='store_true',
                        help="don't convert Black&White jpg's to png")
    parser.add_argument('-msize', dest='fsize_min', default="150K",
                        help="min filesize to process. (B | K | M) (K=2^10)")
    parser.add_argument('-mv', action='store_true',
                        help="""move non-images to "mv" folder""")
    parser.add_argument('-kpng', action='store_true',
                        help="keep (Don't convet) png")
    parser.add_argument('-usejpg', action='store_true',
                        help="use jpg instead webp in most cases")
    parser.add_argument('-orignocopy', action='store_true',
                        help="don't copy original images after size compare")
    global ZOPFLI
    if ZOPFLI:
        parser.add_argument('-nozopfli', action='store_true', help="don't use zopflipng")
    args = parser.parse_args(*args)

    if ZOPFLI:
        ZOPFLI = not args.nozopfli
        pool = Pool(processes=cpu_count()) if ZOPFLI else None
    else:
        pool = None

    return args, pool


def main(*args):
    args, pool = argument_parser(*args)

    if args.path:
        print('by argument')
        input_dir = Path(args.path)
    else:
        print('by cwd')
        input_dir = Path.cwd()
    print(colored('Path: ' + input_dir.as_posix(), 'yellow'))

    input_dir_files = \
        [f for f in input_dir.iterdir() if f.is_file()]
    input_dir_images = \
        [f for f in input_dir_files if f.name.endswith(('.png', '.jpg', '.webp'))]
    input_dir_nonimages = list(set(input_dir_files) - set(input_dir_images))

    if not input_dir_images:
        print(colored('No images', 'red'))
        return

    Path.mkdir(input_dir / NONIMAGES_DIR, exist_ok=True)
    if args.mv:
        nonimages_mv(input_dir_nonimages, input_dir / NONIMAGES_DIR)

    images_process(input_dir_images, input_dir, args, pool)

    if not os.listdir(input_dir / NONIMAGES_DIR):
        Path.rmdir(input_dir / NONIMAGES_DIR)


class Img:
    def __init__(self, f):
        self.name = f
        self.img: Image.Image = Image.open(f)
        self.size = self.img.size
        self.atime = os.path.getatime(f)
        self.mtime = os.path.getmtime(f)


def images_process(input_images, input_dir, args, pool):
    output_dir = input_dir / Path(args.out_dir)
    Path.mkdir(output_dir, exist_ok=True)

    if ZOPFLI:
        global pool_dict
        for f in input_images:
            # process image and get info about file in zopfli pool
            res = image_process(f, input_dir, output_dir, args, pool=pool)
            print()
            if res:
                pool_dict.update(res)
        pool.close()
        if pool_dict:  # if any files in zopfli pool
            print('Waiting zopflipng to complete:')
            print(*sorted(pool_dict.keys()), sep='\n')
            print('Waiting:')
        pool.join()
        print('Done')
        for item in pool_dict.values():
            out, _ = item.get()
            print("out:\n" + out.decode())  # get zopfli output

    else:
        for f in input_images:
            image_process(f, input_dir, output_dir, args)
            print()


def image_process(f, input_dir, output_dir, args, *, pool=None):
    resized = False
    try:
        img = Img(f)
    except IOError:
        print(colored("IOError;", 'red'))
        if args.mv:
            print("Moving to mv dir")
            nonimages_mv(f, input_dir / NONIMAGES_DIR)
        return

    print(f.name)
    print(img.size)

    # What if png file actually an apng?
    if f.name.endswith('.png') and img.img.get_format_mimetype() == 'image/apng':
        print(colored('APNG;', 'red'))
        if args.mv:
            print("Moving to mv dir")
            nonimages_mv(f, NONIMAGES_DIR)
        return

    # copy non-png files to output dir if they have small filesize
    filesize_min_to_process = size2bytes(args.fsize_min)
    if os.path.getsize(f) < filesize_min_to_process and not f.name.endswith('png'):
        if args.orignocopy:
            return
        print(colored("Size too low\nCopying to out dir", 'blue'))
        shutil.copy2(f, output_dir)
        return

    if args.convert_format:
        if ZOPFLI and args.convert_format.lower() == 'png' and f.name.endswith('.png'):
            args.kpng = True
        else:
            img_save(img, output_dir, args.convert_format,
                     quality=args.convert_quality,
                     lossless=args.lossless,
                     compare=False)
            return

    # resize images (ask for each or every image) if they are smaller than size_target
    size_target = args.size
    if size_target:
        if ((int(img.size[0]) > size_target) or
                (int(img.size[1]) > size_target)):
            if (not args.ask) or input(colored('resize? y/n ', 'yellow')).lower() == 'y':
                size_target = size_target, size_target
                print(colored('making image smaller', 'yellow'))
                # Lanczos filter is slow, but keeps details and edges. BICUBIC as alternative?
                img.img.thumbnail(size_target, Image.LANCZOS)
                resized = True

    if f.name.endswith('.png'):
        if (
                args.kpng
                and not resized
                and ZOPFLI
        ):
            cmd = ['zopflipng', '-y', f.resolve(), output_dir / f.name]
            pool_dict[f.name] = pool.apply_async(call_zopflipng, (cmd,))
            print('To zopflipng queue')
        elif args.kpng:
            img_save(img, output_dir, 'png',
                     quality=args.convert_quality,
                     origcopy=not args.orignocopy)
        elif image_has_transparency(img.img):
            print(colored('Image has transparency', 'yellow'))
            img_save(img, output_dir, 'webp',
                     lossless=args.lossless,
                     quality=args.convert_quality,
                     origcopy=not args.orignocopy)
        else:
            img_save_webp_or_jpg(img, output_dir, args)

    elif f.name.endswith('.jpg'):
        if (
                not args.bnwjpg
                and image_iscolorfull(img.img) in ('grayscale', 'blackandwhite')
        ):
            if args.lossless:
                print('Black and white image, convert jpg to png')
                img_save(img, output_dir, 'png',
                        quality=100,
                        origcopy=not args.orignocopy)
            else:
                print('Black and white image, convert jpg to webp')
                img_save(img, output_dir, 'webp',
                        quality=args.convert_quality,
                        origcopy=not args.orignocopy)
        else:
            img_save_webp_or_jpg(img, output_dir, args)

    else:
        print(colored(str(img.img.format).lower(), 'blue'))
        print(colored("Copying to out dir", 'blue'))
        shutil.copy2(f, output_dir)
    if ZOPFLI:
        return pool_dict


def img_save_webp_or_jpg(img, output_dir, args):
    if args.usejpg:
        img_save(img, output_dir, 'jpg',
                    quality=args.convert_quality,
                    origcopy=not args.orignocopy)
    else:
        img_save(img, output_dir, 'webp',
                    quality=args.convert_quality,
                    origcopy=not args.orignocopy)

       
def img_save(
        img: Img, output_path, ext: str, *,
        quality=90, lossless=False, compare=True, origcopy=True
):
    out_file_path = output_path / (img.name.stem + '.' + ext)
    out_file = BytesIO()
    i_ext = img.name.suffix[1:]
    # png  -> png, jpg, webp
    # jpg  -> png, jpg, webp
    # webp -> jpg, webp
    if ext == 'jpg':
        ext = 'jpeg'

    # JPEG
    if i_ext == 'jpg':
        if ext == 'jpeg':
            img.img.save(out_file, ext,
                         quality=quality,
                         subsampling='keep',
                         optimize=True,
                         progressive=True)
        elif ext == 'png':
            # img.img = img.img.convert(mode='P', palette=Image.ADAPTIVE)
            img.img.save(out_file, ext,
                         optimize=True)
        elif ext == 'webp':
            if lossless:
                img.img.save(out_file, ext,
                             quality=100,
                             lossless=True,
                             method=6)
            else:
                img.img.save(out_file, ext,
                             quality=quality,
                             lossless=False,
                             method=6)

    # PNG
    elif i_ext == 'png':
        if ext == 'png':
            img.img.save(out_file, ext,
                         optimize=True)
        elif ext == 'jpeg':
            img.img = img.img.convert('RGB')
            img.img.save(out_file, ext,
                         quality=quality,
                         subsampling=2,
                         optimize=True,
                         progressive=True)
        elif ext == 'webp':
            if lossless:
                img.img.save(out_file, ext,
                             quality=100,
                             lossless=True,
                             method=6)
            else:
                img.img.save(out_file, ext,
                             quality=quality,
                             method=6)

    # WEBP
    elif i_ext == 'webp':
        if ext == 'webp':
            if lossless:
                img.img.save(out_file,ext,
                             quality=100,
                             lossless=True,
                             method=6)
            else:
                img.img.save(out_file, ext,
                             quality=quality,
                             method=6)
        elif ext == 'jpeg':
            img.img.save(out_file, ext,
                         quality=quality,
                         subsampling=2,
                         optimize=True,
                         progressive=True)
        elif ext == 'png':
            img.img.save(out_file, ext,
                         optimize=True)

    out_file_size = out_file.tell()
    orig_file_size = os.path.getsize(img.name)
    print(f"Input size: {orig_file_size}")
    print(f"Result size: {out_file_size}. " +
          "Percentage of original:" +
          "{:.2f}".format(100 * out_file_size / orig_file_size) + "%")
    if (
            compare and (out_file_size < orig_file_size - 100*1024)  # Allow 100k difference
            or not compare
    ):
        with open(out_file_path, 'wb') as opened_file:
            print("Saving result")
            opened_file.write(out_file.getbuffer())
            os.utime(out_file_path, (img.atime, img.mtime))
    elif origcopy:
        print("Out size is bigger. Copying original")
        shutil.copy2(img.name, output_path)


# https://stackoverflow.com/questions/20068945/detect-if-image-is-color-grayscale-or-black-and-white-with-python-pil
def image_iscolorfull(image, thumb_size=40, MSE_cutoff=22, adjust_color_bias=True):
    pil_img = image
    bands = pil_img.getbands()
    if bands == ('R', 'G', 'B') or bands == ('R', 'G', 'B', 'A'):
        thumb = pil_img.resize((thumb_size, thumb_size))
        SSE, bias = 0, [0,0,0]
        if adjust_color_bias:
            bias = ImageStat.Stat(thumb).mean[:3]
            bias = [b - sum(bias)/3 for b in bias]
        for pixel in thumb.getdata():
            mu = sum(pixel)/3
            SSE += sum((pixel[i] - mu - bias[i])*(pixel[i] - mu - bias[i]) for i in [0, 1, 2])
        MSE = float(SSE)/(thumb_size*thumb_size)
        if MSE <= MSE_cutoff:
            print("Grayscale")
            return "grayscale"
        else:
            return "color"
        print("( MSE=", MSE, ")")
    elif len(bands) == 1:
        print("Black and white", bands)
        return "blackandwhite"
    else:
        print("Don't know...", bands)
        return "unknown"


def image_has_transparency(image: Image.Image):
    if len(image.getbands()) < 4:  # if 'A' not in image.getbands()
        return False
    return image.getextrema()[3][0] < 255-20


def size2bytes(size):
    size_name = ("B", "K", "M", "G")
    size.upper()
    size = re.split(r'(\d+)', size)
    num, unit = int(size[1]), size[2]
    idx = size_name.index(unit)
    factor = 1024 ** idx
    return num * factor

# def bite2size(num, suffix='B'):
#     for unit in ['','K','M','G']:
#         if abs(num) < 1024.0:
#             return "%3.1f%s%s" % (num, unit, suffix)
#         num /= 1024.0
#     return "%.1f%s%s" % (num, 'Yi', suffix)


def nonimages_mv(i, output_dir):
    for f in i:
        Path.rename(f, output_dir / f.name)


if __name__ == '__main__':
    main()
