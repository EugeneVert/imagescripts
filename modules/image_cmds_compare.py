#!/usr/bin/env -S python3 -u

import os
import argparse
# import shutil
import subprocess
import tempfile

from io import BytesIO
from multiprocessing import Pool
from pathlib import Path

from PIL import Image
from termcolor import colored

from imagescripts_utils import bite2size, image_has_transparency

ENC_SETTINGS = {
    "png": {
        "any": {
            "optimize": True
        }
    },
    "jpeg": {
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
    "webp-l": {
        "any": {
            "quality": 100,
            "lossless": True,
            "method": 4
        }
    },
    "webp": {
        "any": {
            "quality": "$quality",
            "method": 6
        }
    }
}

CMD_ARGS_ALIASES = {
    "pil": [
        "png",
        "jpeg",
        "webp",
        "webp-l"
    ]
}

PERCENTAGE = 0


def parse_args(*args):
    parser = argparse.ArgumentParser(
        description="",
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-i', dest="path", nargs='?', required=True
    )
    parser.add_argument(
        '-o', dest="out_dir", type=str,
        help="output dir \n    (default: %(default)s)",
        default=str('./test'))
    parser.add_argument(
        '-c', dest="cmds", nargs='+', required=True,
        help=f"supported pil cmds: {[i for i in CMD_ARGS_ALIASES['pil']]}, example: 'pil:jpg:q90'\n" +
        "example Jpeg XL cjxl encoding: 'cjxl:-d 0.3 -s 8'\n" +
        "example AVIF avifenc encoding: 'avif: --min 7 --max 8 -a aq-mode=1 -a enable-chroma-deltaq=1'"
    )
    parser.add_argument(
        '-t', '--tolerance', type=int,
        help="Next command filesize tolerance\n    (default: %(default)s)",
        default=30)
    args = parser.parse_args(*args)
    return args


def main(*args):
    args = parse_args(*args)
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

    Path.mkdir(Path(args.out_dir), exist_ok=True)

    pool = Pool()
    res_cmds_count = {}
    for i in sorted(input_dir_images):
        print()
        print(f"Image: {i}")
        img = load_image(i, args)
        process_image(img, args, res_cmds_count=res_cmds_count)
        # pool.apply_async(
        #     std_wrapper, [('image_process', (img, args))],
        #     callback=collect_result)
    pool.close()
    pool.join()

    print(res_cmds_count)


def load_image(path, args):
    return Image.open(path)


class ImageBuffer():
    def __init__(self, cmd):
        self.image = BytesIO()
        self.cmd = cmd
        self.ext = ""

    def get_size(self):
        return self.image.tell()

    def image_generate(self, img):
        cmd_args = self.cmd.split(":")
        if cmd_args[0] == "pil":
            ext = cmd_args[1]
            i_ext = img.format.lower()
            if ext == "jpg":
                ext = "jpeg"
            kwargs_values = {}
            if len(cmd_args) > 1:
                for i in cmd_args:
                    if i[0] == 'q':
                        kwargs_values["quality"] = int(i[1:])
                    if i[0] == 'l':
                        kwargs_values["lossless"] = True
            if ext not in ENC_SETTINGS.keys():
                print("Output extension not supported")
                return 1
            kwargs_raw = (ENC_SETTINGS[ext][i_ext]
                          if i_ext in ENC_SETTINGS[ext]
                          else ENC_SETTINGS[ext]["any"])
            kwargs = {}
            for key, val in kwargs_raw.items():
                if val in ["$quality", "$lossless"]:
                    val = kwargs_values[val[1:]]
                kwargs[key] = val
            print(kwargs)
            if ext == 'webp-l':
                ext = 'webp'
            img.save(self.image, ext, **kwargs)
            if ext == "jpeg":
                ext = "jpg"
            self.ext = ext

        if cmd_args[0] == "cjxl":
            buffer = tempfile.NamedTemporaryFile(prefix="jxl_")
            buffer
            cmd = 'cjxl "' + img.filename + '" '
            for i in cmd_args[1:]:
                cmd += i + " "
            cmd += buffer.name
            print(cmd)
            proc = subprocess.Popen(cmd, shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # print((proc.communicate()[1]).decode("utf-8"))
            proc.communicate()
            self.image = BytesIO(buffer.read())
            self.image.read()
            self.ext = "jxl"
            buffer.close()

        if cmd_args[0] == "avif":
            cmd_args_index_param = 1
            if cmd_args[1] == "noalpha" and image_has_transparency(img):
                return
            else:
                cmd_args_index_param = 2
            if cmd_args[1] == "alpha" and not image_has_transparency(img):
                return
            else:
                cmd_args_index_param = 2

            buffer = tempfile.NamedTemporaryFile(prefix="avif_")
            buffer
            cmd = 'avifenc "' + img.filename + '" '
            for i in cmd_args[cmd_args_index_param:]:
                cmd += i + " "
            cmd += buffer.name
            print(cmd)
            proc = subprocess.Popen(cmd, shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # print((proc.communicate()[1]).decode("utf-8"))
            proc.communicate()
            self.image = BytesIO(buffer.read())
            self.image.read()
            self.ext = "avif"
            buffer.close()


def process_image(img, args, res_cmds_count={}):
    """Get input image path, generate output image path with format of best of cmd's."""
    enc_img_buffers = []
    for cmd in args.cmds:
        buff = ImageBuffer(cmd)
        buff.image_generate(img)
        enc_img_buffers.append(buff)

    img_filesize = os.path.getsize(img.filename)
    px_count = img.size[0] * img.size[1]
    m = 0

    for buff in enc_img_buffers:
        buff_filesize = buff.get_size()
        buff_bpp = round(buff_filesize*8/px_count, 2)
        percentage_of_original = "{:.2f}".format(
            100 * buff_filesize / img_filesize)

        print(buff.cmd)
        # print i/o size in human-readable format
        print(colored(
            f"{bite2size(img_filesize)} --> {bite2size(buff_filesize)} {buff_bpp}bpp   " +
            f"{percentage_of_original}%", attrs=['underline']))

        tolerance = args.tolerance  # %
        # First commands has value tolerance over next ones
        if m == 0 or buff_filesize < (1 - tolerance*0.01) * m[1]:
            if buff_filesize != 0:
                m = buff, buff_filesize

    if m[0].cmd not in res_cmds_count:
        res_cmds_count[m[0].cmd] = 1
    else:
        res_cmds_count[m[0].cmd] += 1

    if (float(100 * m[1] / img_filesize) < PERCENTAGE) or PERCENTAGE == 0:
        with open(args.out_dir + "/" + Path(img.filename).stem + "." + m[0].ext, "wb") as save_file:
            print("Saving buffer " + m[0].cmd)
            save_file.write(m[0].image.getbuffer())


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
        response = process(*process_args, **process_kwargs)  # call our process function
    except Exception as e:
        print(e)
    # rewind our buffers:
    sys.stdout.seek(0)
    sys.stderr.seek(0)
    return sys.stdout.read(), sys.stderr.read()


if __name__ == '__main__':
    main()
