#!/usr/bin/python
__author__ = 'siesta'
from datetime import datetime, timedelta
import argparse
import codecs
import chardet
import os
import sys
import pdb

# Improvements:
#  Support more than just srt files
#  Convert between different subtitle formats
#  Create API and web frontend with cherrypy
#  Add verbosity to output

# Get input and output filenames, get delta
parser = argparse.ArgumentParser(description='Simple script for adjusting subtitle time offset')
parser.add_argument('-s', '--sub_in', help='the file path of the sub to adjust')
parser.add_argument('-a', '--amount', type=float, help='the file path of the sub to adjust')
parser.add_argument('-o', '--sub_out', help='the location to output the adjusted subtitle')
args = parser.parse_args()


# TODO: Make sure file exists, if not raise exception
f_input = args.sub_in
f_output = args.sub_out
delta = args.amount
delta_s = int(delta)
delta_ms = int(str(delta).split('.')[1])
# Test for BOM-UTF8 file
_bytes = min(32, os.path.getsize(f_input))
raw = open(f_input, 'rb').read(_bytes)
if raw.startswith(codecs.BOM_UTF8):
    encoding = 'utf-8-sig'
else:
    result = chardet.detect(raw)
    encoding = result['encoding']

f_in = codecs.open(f_input, 'r', encoding=encoding)
subs_raw = f_in.readlines()
f_in.close()

# Read in file
print('Reading file..\n  %s\n' % f_input)
subs_blob = ''.join(subs_raw)
subs_list = [i for i in subs_blob.split('\r\n\r\n')]
subs_dict = {}
print('Updating timestamps by %s seconds!' % delta)
# Build subs_dict and update times
for i in subs_list:
    if i != '':
        try:
            lx = i.strip().split('\r\n')
            id = int(lx[0])
            pos_start, pos_end = lx[1].split(' --> ')
            text = '\r\n'.join(lx[2:])
            # Update positions
            dt_start = datetime.strftime(str(datetime.strptime(pos_start, '%H:%M:%S,%f') + timedelta(seconds=delta_s, milliseconds=delta_ms)), '%H:%M:%S,%f')
            dt_end = datetime.strftime(str(datetime.strptime(pos_end, '%H:%M:%S,%f') + timedelta(seconds=delta_s, milliseconds=delta_ms)), '%H:%M:%S,%f')
            pos = '%1.12s' % dt_start + ' --> ' + '%1.12s' % dt_end
            subs_dict[id] = {'pos': pos, 'text': text}
            sys.stdout.write('!')
        except Exception, e:
            print('%s' % str(e))
            pdb.set_trace()

print('\n\nAssembling new subfile\n')

# Put the new blob back together and write it out to new file
new_subs = ''
for i in range(1, len(subs_dict)):
    try:
        line = '%s\r\n%s\r\n%s\r\n\r\n' % (i, subs_dict[i]['pos'], subs_dict[i]['text'])
        new_subs += line
    except Exception, e:
        print('Failed to write line due to input line %s' % i)
        try:
            _pos = subs_dict[i]['pos']
        except Exception:
            print('subs_dict missing pos value for sub line %s' % i)
        try:
           _text = subs_dict[i]['text']
        except Exception:
            print('subs_dict missing text value for sub line %s' % i)

print('Writing file:\n  %s' % f_output)
with open(f_output, 'w') as f_out:
    f_out.write(new_subs)

print('All done.')