#!/usr/bin/python
__author__ = 'Dylan Williams'
from datetime import datetime, timedelta
import argparse
import codecs
import chardet
import os
import sys
import time

# Improvements:
#  Support more than just srt files
#  Convert between different subtitle formats
#  Create API and web frontend with cherrypy
#  Verbosity levels

# Get input and output filenames, get delta
parser = argparse.ArgumentParser(description='A simple script for adjusting subtitle time offset')
parser.add_argument('-s', '--sub_in', help='The file path of the sub to adjust')
parser.add_argument('-a', '--amount', type=float, help='The amount of time to adjust by')
parser.add_argument('-o', '--sub_out', help='The output file path')
args = parser.parse_args()

f_input = args.sub_in
if not os.path.isfile(f_input):
    print(' **ERROR  Input file not found:\n\t%s' % f_input)
    sys.exit(1)
if '.srt' not in f_input:
    print(' **ERROR  Currently only srt formatted files are accepted.')
    sys.exit(1)

f_output = args.sub_out
try:
    with open(f_output, 'a') as output_test:
        pass
except Exception, e:
    print(' ** ERROR  The output file destination is not writable.\n%s' % e)
    sys.exit(1)

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

if encoding == 'ascii':
    f_in = open(f_input, 'r')
else:
    f_in = codecs.open(f_input, 'r', encoding=encoding)

subs_raw = f_in.readlines()
f_in.close()

s_time = time.time()
# Read in file
print('Reading file.. %s' % f_input)
subs_blob = ''.join(subs_raw)
subs_list = [i for i in subs_blob.split('\r\n\r\n')]
subs_dict = {}
sys.stdout.write('Updating timestamps by %s seconds!' % delta)
# Build subs_dict and update times
for i in subs_list:
    if i != '':
        try:
            lx = i.strip().split('\r\n')
            id = int(lx[0])
            pos_start, pos_end = lx[1].split(' --> ')
            text = '\r\n'.join(lx[2:])
            # Update positions
            dt_start = datetime.strftime(datetime.strptime(pos_start, '%H:%M:%S,%f') +
                                             timedelta(seconds=delta_s, milliseconds=delta_ms), '%H:%M:%S,%f')
            dt_end = datetime.strftime(datetime.strptime(pos_end, '%H:%M:%S,%f') +
                                           timedelta(seconds=delta_s, milliseconds=delta_ms), '%H:%M:%S,%f')
            pos = '%1.12s' % dt_start + ' --> ' + '%1.12s' % dt_end
            subs_dict[id] = {'pos': pos, 'text': text}
            sys.stdout.write('!')
        except Exception, e:
            print('%s' % str(e))

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

with open(f_output, 'w') as f_out:
    f_out.write(new_subs)

t_time = time.time() - s_time
print('\n\n  Wrote  %s  in %3.2f seconds\n' % (f_output, t_time))