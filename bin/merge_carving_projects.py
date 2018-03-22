import h5py
import os
from shutil import copyfile
import argparse
import warnings

parser = argparse.ArgumentParser(description='Merge ilastik carving projects.')
parser.add_argument('main_name', metavar='carving.ilp',
                    help='the main carving project (other carving projects\' '
                    'objects are inserted in a copy of this project)')
parser.add_argument('add_names', metavar='ilp-files_to_be_merged', nargs='+',
                    help='ilastik carving projects whose objects are to be '
                    'merged into the main carving project')
parser.add_argument('--override', action='store_true', help='Specify to '
                    'override existing objects. Objects are identified by '
                    'name')
parser.add_argument('--keep', action='store_true', help='Specify to '
                    'disregard objects with the same name and keep only '
                    'the first occurrence of an object. Objects are '
                    'identified by name')

args = parser.parse_args()

assert '.ilp' in args.main_name
assert all(['.ilp' in an for an in args.add_names])

res_name = args.main_name.replace('.ilp',
                                  '-' +
                                  '-'.join([os.path.split(an)[1].split('.')[0] for an in args.add_names]) +
                                  '.ilp')

print(f'name of merged project: {res_name}')

# copy main project to not alter existing project
copyfile(args.main_name, res_name)

adds = [h5py.File(an, 'r') for an in args.add_names]
res = h5py.File(res_name, 'r+')

obj_group = 'carving/objects'

if obj_group not in res:
    raise ValueError(f'No dataset "{obj_group}" in {args.main_name}. Is '
                     f'{args.main_name} a carving project and does it have at least one '
                     'saved object?')

for add in adds:
    try:
        objs = add[obj_group]
    except KeyError:
        warnings.warn(f'no carving objects found in {add.filename}')
        continue
    for obj in objs:
        new_obj = obj
        if obj in res[obj_group]:
            if args.override:
                del res[obj_group][obj]
            elif args.keep:
                continue
            else:
                new_obj += '-' + add.filename.split('.')[0]

        objs.copy(obj, res[obj_group], name=new_obj)

    add.close()

res.close()
