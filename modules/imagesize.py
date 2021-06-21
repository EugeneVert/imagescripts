#!/usr/bin/env python3
#
# 2021 Eugene Vert; eugene.a.vert@gmail.com

import os
import argparse
import subprocess
import tempfile
import shutil

from multiprocessing import Pool, cpu_count
from pathlib import Path
from io import BytesIO

from termcolor import colored
from PIL import Image
# from PIL import ImageStat
from PIL.ImageFilter import GaussianBlur, UnsharpMask

from imagescripts_utils import size2bytes, bite2size, image_has_transparency

NONIMAGES_DIR_NAME = './mv'
OLDIMAGES_DIR_NAME = 'old'
PERCENTAGE = ''

HAVE_JXL = shutil.which('cjxl')

ENC_SETTINGS = {
    "png": {
        "any": {
            "optimize": True
        }
    },
    "jpg": {
        "any": {
            "quality": "$quality",
            "subsampling": 2,
            "optimize": True,
            "progressive": True
        },
        "jpg": {
            "quality": "$quality",
            "subsampling": "keep",
            "optimize": True,
            "progressive": True
        }
    },
    "jxl": {
        "any": {
            "quality": "$quality",
            "lossless": "$lossless"
        }
    },
    "avif": {
        "any": {
            "quality": "$quality",
        }
    },
    "webp_lossless": {
        "any": {
            "quality": 100,
            "lossless": True,
            "method": 4
        }
    },
    "webp_lossy": {
        "any": {
            "quality": "$quality",
            "method": 6
        }
    }
}


def argument_parser(*args):
    global PERCENTAGE
    parser = argparse.ArgumentParser(
        description='Reduce images size',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        'path', nargs='?',
        help="dir with images")
    parser.add_argument(
        '-o', '--output', dest="out_dir", type=str,
        default=str('./test'),
        help="output dir \n    (default: %(default)s)")
    parser.add_argument(
        '-c:f', dest='convert_format', type=str,
        help="set output format for all files")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-c:q', dest='convert_quality', type=float, action="store",
        default=int(92.777),  # (jxl 'distance' 0.75 converted to 'quality')
        help='quality setting \n    (default: %(default)s)')
    group.add_argument(
        '-c:d', dest='convert_distance_jxl', type=float, action="store",
        help='distance setting of Jpeg XL (will be converted to c:q)')
    parser.add_argument(
        '-l', '--lossless', action='store_true',
        help="keep png lossless")
    parser.add_argument(
        '-slow', action="store_true",
        help="Slow lossless jxl encode")
    parser.add_argument(
        '-ask', action='store_true',
        help='ask resize for each resizable')
    parser.add_argument(
        '-r', '--resize', dest='size', type=str,
        default=str(3508),
        help='set resize size.\n  Add "x" to end to resize by smallest side' +
        '\n    (default: %(default)s)' +
        '\n    (tip: A3&A4 paper 4961/3508/2480/1754/1240)')
    parser.add_argument(
        '-blur', nargs='?', dest='blur_radius', type=float,
        const=0.5,
        help='add blur to image\n    (const: %(const)s)\n')
    parser.add_argument(
        '-sharpen', nargs='?', dest='sharpen', type=float,
        const=1,
        help='add sharpen filter to image\n' +
        '_____________________________________________\n\n')
    parser.add_argument(
        '-msize', dest='fsize_min',
        default="0K",
        help="min filesize to process. (B | K | M) (K=2^10)")
    parser.add_argument(
        '-percent', dest='percentage',
        default=90,
        help="Max percentage of original file to save")
    parser.add_argument(
        '-mv', action='store_true',
        help="""move non-images to "mv" folder""")
    parser.add_argument(
        '-kpng', action='store_true',
        help="keep (Don't convet) png")
    parser.add_argument(
        '-nowebp', action='store_true',
        help="don't use webp")
    parser.add_argument(
        '-orignocopy', action='store_true',
        help="don't copy original images after size compare")
    parser.add_argument(
        '-mvo', dest='out_orig_dir',
        help="mv original images to folder")
    parser.add_argument(
        '-nproc', dest='nproc', type=int,
        default=cpu_count(),
        help="count of procs")

    args = parser.parse_args(*args)

    # jxl distance to quality NOTE (actually works only for d < ~~6.310)
    if args.convert_distance_jxl:
        args.convert_quality = 100 + (0.1 - args.convert_distance_jxl) / 0.09

    PERCENTAGE = int(args.percentage)

    return args


def main(*args):
    args = argument_parser(*args)

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

    Path.mkdir(input_dir / NONIMAGES_DIR_NAME, exist_ok=True)
    nonimages_dir = input_dir / NONIMAGES_DIR_NAME
    if args.mv:
        nonimages_mv(input_dir_nonimages, nonimages_dir)

    images_process(input_dir_images, input_dir, args)

    # remove dir if empty
    if not any(nonimages_dir.iterdir()):
        Path.rmdir(nonimages_dir)


def collect_result(result):
    if result:
        print(result[0])
        if result[1]:
            print(result[1])


def std_wrapper(args):
    from io import StringIO
    import sys
    sys.stdout, sys.stderr = StringIO(), StringIO()  # replace stdout/err with our buffers
    # args is a list packed as: [0] process function name; [1] args; [2] kwargs; lets unpack:
    process_name = args[0]
    process_args = args[1] if len(args) > 1 else []
    process_kwargs = args[2] if len(args) > 2 else {}
    # get our method from its name, assuming global namespace of the current module/script
    process = globals()[process_name]
    try:
        # TODO
        response = process(*process_args, **process_kwargs)  # call our process function
    except Exception as e:
        print(e)
    # rewind our buffers:
    sys.stdout.seek(0)
    sys.stderr.seek(0)
    return sys.stdout.read(), sys.stderr.read()


def images_process(input_images, input_dir, args):
    if args.out_orig_dir:
        Path.mkdir(input_dir / args.out_orig_dir, exist_ok=True)
        output_orig_dir = input_dir / args.out_orig_dir
        print(output_orig_dir)

    output_dir = input_dir / Path(args.out_dir)
    Path.mkdir(output_dir, exist_ok=True)

    pool = Pool(args.nproc)

    for f in sorted(input_images):
        if args.out_orig_dir:
            f = f.rename(output_orig_dir / f.name)
        # image_process(f, input_dir, output_dir, args)
        pool.apply_async(
            std_wrapper, [('image_process', (f, input_dir, output_dir, args))],
            callback=collect_result)
    pool.close()
    pool.join()


class Img:
    def __init__(self, f):
        self.name = f
        self.img: Image.Image = Image.open(f)
        self.size = self.img.size
        self.atime = os.path.getatime(f)
        self.mtime = os.path.getmtime(f)


def image_process(f, input_dir, output_dir, args):
    processed = False
    try:
        img = Img(f)
    except IOError:
        print(colored("IOError;", 'red'))
        if args.mv:
            print("Moving to mv dir")
            nonimages_mv(f, input_dir / NONIMAGES_DIR_NAME)
        return

    print(f.name)
    print(img.size)

    # What if png file actually an apng?
    if f.name.endswith('.png') and img.img.get_format_mimetype() == 'image/apng':
        print(colored('APNG;', 'red'))
        if args.mv:
            print("Moving to mv dir")
            nonimages_mv(f, input_dir / NONIMAGES_DIR_NAME)
        return

    # copy non-png files to output dir if they have small filesize
    filesize_min_to_process = size2bytes(args.fsize_min)
    if os.path.getsize(f) < filesize_min_to_process:
        if args.orignocopy:
            return
        print(colored("Size too low\nCopying to out dir", 'blue'))
        try:
            shutil.copy2(f, output_dir)
        except shutil.SameFileError:
            pass
        return

    # optional images bluring for smoothing jpg artifacts
    if args.blur_radius:
        img.img = img.img.convert('RGB')
        img.img = img.img.filter(GaussianBlur(radius=args.blur_radius))
        processed = True

    if args.sharpen:
        img.img = img.img.filter(UnsharpMask(radius=args.sharpen, percent=150, threshold=0))
        # img.img = img.img.filter(Kernel((3, 3), [0    , -1.14, 0    ,
        #                                          -1.14, 5.56 , -1.14,
        #                                          0    , -1.14, 0    ], scale=args.sharpen ))
        processed = True

    # resize images (has option to ask for each) if they are bigger than args.size
    # args.size == 0 disables resizing
    if args.size != '0':
        if args.size[-1] == 'x':  # set resize size by smallest side
            size_target_min = int(args.size[:-1])
            if int(min(img.size)) > size_target_min:

                if (not args.ask) or input(colored('resize? y/n ', 'yellow')).lower() == 'y':
                    size_target = calc_minsize_target(img.img.size, size_target_min)
                    print(colored('making image smaller', 'yellow'))
                    img.img.thumbnail(size_target, Image.LANCZOS)
                    processed = True

        else:
            if int(max(img.size)) > int(args.size):  # else set resize size by biggest side
                size_target = int(args.size)

                if (not args.ask) or input(colored('resize? y/n ', 'yellow')).lower() == 'y':
                    size_target = size_target, size_target
                    print(colored('making image smaller', 'yellow'))
                    # Lanczos filter is slow, but keeps details and edges. BICUBIC as alternative?
                    img.img.thumbnail(size_target, Image.LANCZOS)
                    processed = True

    additional_args = {"quality": args.convert_quality,
                       "lossless": args.lossless,
                       "origcopy": not args.orignocopy,
                       "processed": processed,
                       "slow_enc": args.slow}

    # optional convert to format
    if args.convert_format:
        img_save(img, output_dir, args.convert_format,
                 **additional_args,
                 compare=False)
        return

    if f.name.endswith('.png'):
        if args.kpng:
            ext = 'png'
            img_save(img, output_dir, ext, **additional_args)
        elif image_has_transparency(img.img):
            print(colored('Image has transparency', 'yellow'))
            ext = 'jxl' if HAVE_JXL else 'webp'
            img_save(img, output_dir, ext, **additional_args)
        else:
            img_save_lossy(img, output_dir, args.nowebp, additional_args)

    elif f.name.endswith('.jpg'):
        img_save_lossy(img, output_dir, args.nowebp, additional_args)

    else:
        print(colored(str(img.img.format).lower(), 'blue'))
        print(colored("Copying to out dir", 'blue'))
        try:
            shutil.copy2(f, output_dir)
        except shutil.SameFileError:
            pass


def calc_minsize_target(img_size, target_minsize):
    new_maxsize = target_minsize * max(img_size) / min(img_size)
    new_maxsize = round(new_maxsize)
    return (target_minsize, new_maxsize) \
        if img_size[0] == min(img_size) \
        else (new_maxsize, target_minsize)


def img_save_lossy(img, output_dir, nowebp, additional_args):
    if nowebp:
        ext = 'jpg'
    elif HAVE_JXL:
        ext = 'jxl'
    else:
        ext = 'webp'
    img_save(img, output_dir, ext, **additional_args)


def img_save(
        img: Img, output_path, ext: str, *,
        quality=90, lossless=False, compare=True, origcopy=True,
        processed=False, slow_enc=False
):
    global PERCENTAGE
    out_file_path = output_path / (img.name.stem + '.' + ext)
    out_file = BytesIO()         # output image buffer
    i_ext = img.name.suffix[1:]  # input image extension

    # get arguments from dict
    kwargs_raw = 0
    if ext == "webp":
        kwargs_raw = (ENC_SETTINGS["webp_lossless"]["any"] if lossless
                      else ENC_SETTINGS["webp_lossy"]["any"])
    if not kwargs_raw:
        kwargs_raw = (ENC_SETTINGS[ext][i_ext]
                      if i_ext in ENC_SETTINGS[ext]
                      else ENC_SETTINGS[ext]["any"])
    # replace placeholders with values
    kwargs = {key:
              (val if
               (val != "$quality" and val != "$lossless")
               else quality if val != "$lossless"
               else lossless)
              for key, val in kwargs_raw.items()}

    # Pillow wants jpeg as extension
    if ext == 'jpg':
        ext = 'jpeg'

    # OUTPUT -- JXL
    if ext == 'jxl':
        out_file = save_jxl(img, i_ext, **kwargs,
                            input2png=processed, slow=slow_enc)

    elif ext == 'avif':
        if lossless:
            print("Lossless avif TODO")
        else:
            out_file = save_avif(img, i_ext, **kwargs,
                                 input2png=processed, slow=slow_enc)

    # INPUT -- JPEG
    elif i_ext == 'jpg':
        if ext == 'jpeg':
            try:
                img.img.save(out_file, ext, **kwargs)
            except ValueError:
                print("Can't keep JPG subsampling the same")
                kwargs.pop("subsampling", None)
                img.img.save(out_file, ext, **kwargs)
        elif ext == 'png':
            # reduce color palette
            # img.img = img.img.convert(mode='P', palette=Image.ADAPTIVE)
            ###
            img.img.save(out_file, ext, **kwargs)
        elif ext == 'webp':
            img.img.save(out_file, ext, **kwargs)

    # INPUT -- PNG
    elif i_ext == 'png':
        if ext == 'jpeg':
            if "A" in img.img.getbands():
                img.img = img.img.convert('RGB')
            img.img.save(out_file, ext, **kwargs)
        else:
            img.img.save(out_file, ext, **kwargs)

    # INPUT -- WEBP
    elif i_ext == 'webp':
        img.img.save(out_file, ext, **kwargs)

    # compare i/o sizes
    out_file_size = out_file.tell()
    orig_file_size = os.path.getsize(img.name)
    percentage_of_original = "{:.2f}".format(
        100 * out_file_size / orig_file_size)

    # print i/o size in human-readable format
    print(colored(
          f"{bite2size(orig_file_size)} --> {bite2size(out_file_size)}    " +
          f"{percentage_of_original}%", attrs=['underline']))

    if (
            compare and (float(percentage_of_original) < PERCENTAGE)
            or not compare
    ):
        with open(out_file_path, 'wb') as opened_file:
            print("Saving result")
            opened_file.write(out_file.getbuffer())
            os.utime(out_file_path, (img.atime, img.mtime))
    elif origcopy:
        print("Copying original")
        try:
            shutil.copy2(img.name, output_path)
        except shutil.SameFileError:
            pass

    else:
        print("Image not saved")


def save_jxl(img: Img, input_extension, quality=93, lossless=False,
             input2png=False, slow=False):
    temp = 0
    bufer = tempfile.NamedTemporaryFile(prefix="jxl_")
    # cjxl does't support webp and tiff as input
    # -- the input can be PNG, APNG, GIF, JPEG, EXR, PPM, PFM, or PGX
    if input2png or input_extension == ("webp", "tiff"):
        # save as temp png
        temp = tempfile.NamedTemporaryFile(prefix="png_")
        img.img.save(temp, "png")
        cmd = "cjxl " + temp.name

    else:
        cmd = 'cjxl "' + img.name.as_posix() + '"'

    if lossless:
        # Jpg can be transcoded losslessly, no need of modular mode
        if input_extension == "jpg":
            # TODO a bit missleading var name, change back to "processed" ?
            if not input2png:
                cmd += " -s 8"
                print("jpg transcode to jxl")
            else:
                print(colored("PROCESSED JPG, NOT LOSSLESS", "red"))
                cmd += f" -q {quality}"
        else:
            # modular mode settings
            # speed 9 (-s 9), look to outher chanels (-E 3)
            cmd += " -m -s 9 -E 3" if slow else " -m -s 8"
    else:
        # VarDCT quality
        cmd += f" -q {quality}"
    cmd += " " + bufer.name
    print(cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # print((proc.communicate()[1]).decode("utf-8"))
    proc.communicate()
    if temp:
        temp.close()

    out = BytesIO(bufer.read())
    out.read()
    bufer.close()
    return out


def save_avif(img: Img, input_extension, quality=93, lossless=False,
              input2png=False, slow=False):
    temp = 0
    bufer = tempfile.NamedTemporaryFile(prefix="avif_")
    # avifenc does't support webp and tiff as input
    # -- avifenc [options] input.[jpg|jpeg|png|y4m] output.avif
    if input2png or input_extension in ("webp", "tiff"):
        # save as temp png
        temp = tempfile.NamedTemporaryFile(prefix="png_")
        img.img.save(temp, "png")
        cmd = "avifenc " + temp.name

    else:
        cmd = 'avifenc "' + img.name.as_posix() + '"'

    # using 10-bit and yuv420 for optimized main av1 profile,
    # setting min and max quantizer for color  (0-63, where 0 is lossless)
    cmd += f" -d 10 -y 444 --min {quality} --max {quality + 2}"
    if "A" not in img.img.getbands():
        cmd += " -a enable-chroma-deltaq=1"
    if slow:
        cmd += " --speed 1"

    cmd += " " + bufer.name
    print(cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # print((proc.communicate()[1]).decode("utf-8"))
    proc.communicate()
    if temp:
        temp.close()

    out = BytesIO(bufer.read())
    out.read()
    bufer.close()
    return out


def nonimages_mv(i, output_dir):
    for f in i:
        Path.rename(f, output_dir / f.name)


if __name__ == '__main__':
    main()
