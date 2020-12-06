#!/usr/bin/env python3
"""
From Zips(frames + json(filename + duration)) in folder To video
"""
import os
import json
import zipfile
import tempfile
import argparse
from pathlib import Path
import ffmpeg

def main(*args):
    parser = argparse.ArgumentParser(
        description='Generate video from zips(frames+json)')
    parser.add_argument('path', nargs='?',
                        help='Dir with zips')
    parser.add_argument('-crf', dest='crf', type=int, default=12,
                        help='Specify video CRF')
    args = parser.parse_args(*args)
    if args.path:
        print('by argument')
        target_dir = os.path.abspath(args.path)
    else:
        print('by cwd')
        target_dir = os.getcwd()
    os.chdir(os.path.abspath(target_dir))
    files = Path('.').glob('*.zip')
    for f in files:
        print(f)
        with zipfile.ZipFile(f.name, 'r') as zipf,\
             tempfile.TemporaryDirectory() as tempdir:
            zipf.extractall(tempdir)
            demuxerf = Path(tempdir + '/concat_demuxer')

            # find animation data json
            if os.path.exists(tempdir + '/animation.json'):
                # {"smthg": {..., 'frames': {'file': 'FRAME' 'delay': DELAY}}}
                animdatafile = tempdir + '/animation.json'
                animdatatype = 1
            elif os.path.exists(f.name + '.js'):
                # {..., 'frames': {'file': 'FRAME' 'delay': DELAY}}
                animdatafile = f.name + '.js'
                animdatatype = 2
            elif os.path.exists(f.name[:-4] + '.js'):
                # {..., 'frames': {'file': 'FRAME' 'delay': DELAY}}
                animdatafile = f.name[:-4] + '.js'
                animdatatype = 2
            else:
                print("Error, no animation data file")
                raise IOError("can't find animation data")

            # open animation data and create demuxer file for ffmpeg
            with open(animdatafile) as animfile,\
                 open(tempdir + '/concat_demuxer', 'x') as demuxerf:
                animdata: dict = json.load(animfile)
                # print(animdata)
                if animdatatype == 1:
                    for i in list(animdata.values())[0]['frames']:
                        if 'file' not in i and 'delay' not in i:
                            continue
                        demuxerf.write("file '" + tempdir + '/' + i['file'] + "'\n")
                        demuxerf.write('duration ' + str(i['delay']/1000) + '\n')
                elif animdatatype == 2:
                    for i in animdata['frames']:
                        if 'file' not in i and 'delay' not in i:
                            continue
                        demuxerf.write("file '" + tempdir + '/' + i['file'] + "'\n")
                        demuxerf.write('duration ' + str(i['delay']/1000) + '\n')
                demuxerf.write("file '" + tempdir + '/' + i['file'] + "'\n")
                demuxerf.close()
                print(Path.name)
                out_name = str(Path('.')) + '/' + f.stem
            (
                ffmpeg
                .input(demuxerf.name,f='concat', safe=0)
                .filter('pad', 'ceil(iw/2)*2', 'ceil(ih/2)*2')
                .output(out_name + '.mp4', crf=args.crf, preset='veryslow')
                .run()
            )


if __name__ == '__main__':
    main()
