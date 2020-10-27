#!/usr/bin/env python3
"""
From Zips(frames + json(filename + duration)) in folder To video
"""
import os
import json
import zipfile
import tempfile
from pathlib import Path
import ffmpeg

def main(argv):
    if len(argv) >= 2:
        print('by argument')
        target_dir = os.path.abspath(argv[1])
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
            with open(tempdir + '/animation.json') as animfile,\
                 open(tempdir + '/concat_demuxer', 'x') as demuxerf:
                animdata : dict = json.load(animfile)
                # print(animdata)
                for i in list(animdata.values())[0]['frames']:
                    if 'file' not in i and 'delay' not in i:
                        continue
                    demuxerf.write("file '" + tempdir + '/' + i['file'] + "'\n")
                    demuxerf.write('duration ' + str(i['delay']/1000) + '\n')
                demuxerf.write("file '" + tempdir + '/' + i['file'] + "'\n")
                demuxerf.close()
                print(Path.name)
            (
                ffmpeg
                .input(demuxerf.name,f='concat', safe=0)
                .filter('pad', 'ceil(iw/2)*2', 'ceil(ih/2)*2')
                .output(str(Path('.')) + '/' + f.stem + '.mp4')
                .run()
            )


if __name__ == '__main__':
    import sys
    main(sys.argv)
