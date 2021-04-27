#!/usr/bin/env python

"""Imagescripts for image gallerys manipulation"""

# 2020 Eugene Vert; eugene.a.vert@gmail.com


import sys
import argparse


parser = argparse.ArgumentParser(description='Imagescripts for image gallerys manipulation')
subparser = parser.add_subparsers(help='sub-command help')
parser_size = subparser.add_parser('size', help='reduce images size', add_help=False)
parser_size.set_defaults(task='size')
parser_generate = subparser.add_parser('generate', help='generators', add_help=False)
parser_generate.add_argument('subtask', choices=['video', 'fromjson'])
parser_generate.set_defaults(task='generate')
parser_find = subparser.add_parser('find', help='sort files', add_help=False)
parser_find.add_argument('subtask', choices=['bpp', 'bnw', 'resizable', 'samesize', 'simmilar'])
parser_find.set_defaults(task='find')
args, _ = parser.parse_known_args()
sys.path.append(sys.path[0] + '/modules/')
task = args.task
print("TASK: " + task)

if task == 'size':
    import modules.imagesize as imagesize
    imagesize.main(sys.argv[2:])
elif task == 'generate':
    subtask = args.subtask
    if subtask == 'video':
        import modules.image_generate_video as img2video
        img2video.main(sys.argv[3:])
    if subtask == 'fromjson':
        import modules.image_json_generate_video as json2video
        json2video.main(sys.argv[3:])
elif task == 'find':
    subtask = args.subtask
    if subtask == 'bpp':
        import modules.image_find_bpp as bpp
        bpp.main(sys.argv[3:])
    if subtask == 'bnw':
        import modules.image_find_blacknwhite as bnw
        bnw.main(sys.argv[3:])
    if subtask == 'resizable':
        import modules.image_find_resizable as resizable
        resizable.main(sys.argv[3:])
    if subtask == 'samesize':
        import modules.image_find_samesize as samesize
        samesize.main(sys.argv[2:])
    if subtask == 'simmilar':
        import modules.image_find_similar as similar
        similar.main(sys.argv[2:])
