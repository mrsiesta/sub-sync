#!/usr/bin/python
__author__ = 'Dylan Williams'
from datetime import datetime, timedelta
import argparse
import codecs
import chardet
import os
import sys
import time

# TODO
#  Support additional file formats
#  Convert between different subtitle formats
#  Create API and web frontend with cherrypy
#  Verbosity levels

parser = argparse.ArgumentParser(description='A simple script for adjusting subtitle time offset')
parser.add_argument('-s', '--sub_in', help='The file path of the sub to adjust')
parser.add_argument('-a', '--amount', type=float, help='The amount of time to adjust by')
parser.add_argument('-o', '--sub_out', help='The output file path')
args = parser.parse_args()

sub_file = args.sub_in
output_file = args.sub_out
delta = args.amount
delta_s = int(delta)
delta_ms = int(str(delta).split('.')[1]) * 10  # Need to multiply by 10 for correct ms precision


def adj_time(time_str):
    new_time = datetime.strptime(time_str, '%H:%M:%S,%f') + timedelta(seconds=delta_s, milliseconds=delta_ms)
    time_formatted = datetime.strftime(new_time, '%H:%M:%S,%f')
    return time_formatted


def build_sub_dict(sub, subs_dict):
    # Parse sub
    sub_parts = sub.strip().split('\r\n')
    sub_id = int(sub_parts[0])
    pos_start, pos_end = sub_parts[1].split(' --> ')
    text = '\r\n'.join(sub_parts[2:])
    # Update positions
    dt_start = adj_time(pos_start)
    dt_end = adj_time(pos_end)
    new_pos = '%1.12s' % dt_start + ' --> ' + '%1.12s' % dt_end
    subs_dict[sub_id] = {'pos': new_pos, 'text': text}
    return subs_dict


def create_formatted_subs(unformatted_sub_list):
    subs_blob = ''.join(unformatted_sub_list)
    subs_list = [i for i in subs_blob.split('\r\n\r\n')]
    subs_dict = {}
    sys.stdout.write('Updating timestamps by %s seconds!' % delta)
    # Build subs_dict and update times
    for i in subs_list:
        if i != '':
            try:
                build_sub_dict(i, subs_dict)
                sys.stdout.write('!')
            except Exception, e:
                print('%s' % str(e))

    # Put the new blob back together and write it out to new file
    new_subs = ''
    for i in range(1, len(subs_dict)):
        try:
            line = '%s\r\n%s\r\n%s\r\n\r\n' % (i, subs_dict[i]['pos'], subs_dict[i]['text'])
            new_subs += line
        except KeyError:
            print('Failed to write line due to input line %s' % i)
            if 'pos' not in subs_dict[i]:
                print('subs_dict missing pos value for sub line %s' % i)
            if 'text' not in subs_dict[i]:
                print('subs_dict missing text value for sub line %s' % i)
    return new_subs


def read_subs_in():
    # Test for BOM-UTF8 file
    _bytes = min(32, os.path.getsize(sub_file))
    raw = open(sub_file, 'rb').read(_bytes)
    if raw.startswith(codecs.BOM_UTF8):
        encoding = 'utf-8-sig'
    else:
        result = chardet.detect(raw)
        encoding = result['encoding']

    if encoding == 'ascii':
        f_in = open(sub_file, 'r')
    else:
        f_in = codecs.open(sub_file, 'r', encoding=encoding)
        
    subs_raw = f_in.readlines()
    f_in.close()
    return subs_raw


def verify_files():
    # Test we can access sub file
    print('Attempting to read subtitle file.. %s' % sub_file)
    if not os.path.isfile(sub_file):
        print(' **ERROR  Input file not found:\n\t%s' % sub_file)
        sys.exit(1)
    if '.srt' not in sub_file:
        print(' **ERROR  Currently only srt formatted files are accepted.')
        sys.exit(1)

    # Test we can write to the output file
    try:
        with open(output_file, 'a'):
            pass
    except IOError, e:
        print(' ** ERROR  The output file destination is not writable.\n%s' % e)
        sys.exit(1)
    return


def write_subs_out(new_subs):
    with open(output_file, 'w') as f_out:
        f_out.write(new_subs)
    

def main():
    start_time = time.time()
    verify_files()
    raw_subs_list = read_subs_in()
    formatted_subs = create_formatted_subs(raw_subs_list)
    write_subs_out(formatted_subs)
    t_time = time.time() - start_time
    print('\n\n  Wrote  %s  in %3.2f seconds\n' % (output_file, t_time))


if __name__ == '__main__':
    main()