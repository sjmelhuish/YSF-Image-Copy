# -*- coding: utf-8 -*-
""" ysf-image-copy

Usage:
  ysf-image-copy.py CALLSIGN RADIOID OUTDIR [-d DIRECTORY|-f PICFILE] [-u] [-t TEXT] [-c COLOUR]
  
Arguments:
  CALLSIGN            The RX location from internal list of RAS sites
  RADIOID             The Radio ID to insert
  OUTDIR              The output directory
  
Options:
  -h --help                          Show this screen
  -v --version                       Show version
  -d DIRECTORY --dir=DIRECTORY       Name the input directory forbatch conversion
  -f PICFILE --file=PICFILE          Convert a single file
  -t TEXT --text=TEXT                Write text over image
  -c COLOUR --colour=COLOUR          Colour for the text
  -u                                 Update files at outdir instead of starting from scratch
  
"""

import io
import binascii
from datetime import datetime, timedelta
import os
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from PIL import ImageFont
from PIL import ImageDraw 
from colour import Color
from docopt import docopt

print ("YSF-Image-Copy Running")

def get_geotagging(exif):

    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging

def encodegps(exif):
    blank_gps = "                    "
    
    # exif = get_exif(filename)

    if exif:

        # print(f"exif from {filename}:")
        # print(exif)
        try:
            geotags = get_geotagging(exif)
        except ValueError:
            # No EXIF GPS data
            return blank_gps
        try:
            print(f"geotags from image:")
            print(f'[{geotags}]')
            print(geotags['GPSLatitude'])
            print(geotags['GPSLongitude'])
            return '{:1.1}{:03d}{:02d}{:04d}{:1.1}{:03d}{:02d}{:04d}'.format(
                geotags['GPSLatitudeRef'],
                int(geotags['GPSLatitude'][0]),
                int(geotags['GPSLatitude'][1]),
                int(100*geotags['GPSLatitude'][2]),
                geotags['GPSLongitudeRef'],
                int(geotags['GPSLongitude'][0]),
                int(geotags['GPSLongitude'][1]),
                int(100*geotags['GPSLongitude'][2]),
            )
        except KeyError:
            # GPS data missing?
            return blank_gps

    return blank_gps


def get_date_taken(exif):
    try:
        if exif:
            dto_str = exif[36867]
            return datetime.strptime(dto_str, '%Y:%m:%d %H:%M:%S')
        else:
            return datetime.now()
    except KeyError:
        # No EXIF data for datetime
        return datetime.now()

def getfilesize(filename):
    b = os.path.getsize(filename)
    return b.to_bytes(4, byteorder='big', signed=False)

def dec2hex(val):
    v = val%100
    return v%10 + 16*(v//10)

def writedate(binary_stream, when):

    t = when.timetuple()
    for z in t[:6]:
        n = dec2hex(z)
        # print("{:02d} -> {:02d} (0x{:02x})".format(z,n,n))
        binary_stream.write (n.to_bytes(1, byteorder='big', signed=False))

def print_output(binary_stream, chunksize):
    binary_stream.seek(0)
    while binary_stream.readable():
        addr = binary_stream.tell()
        d = binary_stream.read(chunksize)
        if len(d) == 0:
            break
        print("{:04x}".format(addr), " ".join(["{:02x}".format(x) for x in d]))

def picfilename(radio_id, seq_num):
    return "H{:.5}{:06d}.jpg".format(radio_id, seq_num)


def write_log(binary_stream, picfile, call_sign, radio_id, outdir, picnum, text, colour):
    print(f'Write log entry for {picfile}')
    image = Image.open(picfile)
    exif = image.getexif()
    binary_stream.write(bytes(b'\x00\x00\x00\x00')) # Head
    binary_stream.write(bytes(b'\x20\x20\x20\x20\x20')) # Node ID
    binary_stream.write(bytes('ALL       ', 'ASCII')) # Dest
    binary_stream.write(bytes('      ', 'ASCII')) # 6 spaces
    binary_stream.write(bytes(radio_id, 'ASCII')) # Radio ID
    binary_stream.write(bytes(call_sign.ljust(16), 'ASCII')) # Callsign in 16-char field
    writedate(binary_stream, datetime.now() - timedelta(hours = 1))
    writedate(binary_stream, datetime.now())
    taken = get_date_taken(exif)
    writedate(binary_stream, taken)
    binary_stream.write(
        bytes('{:11.11}'.format(os.path.basename(picfile)), 'ASCII')
    ) # Description
    binary_stream.write(bytes('     ', 'ASCII')) # 5 spaces
    outname = picfilename(radio_id, picnum)
    fulloutname =  os.path.join(outdir, 'PHOTO', outname)
    print(f'Convert {picfile} -> {outname}')
    shrink_image(image,fulloutname, text, colour)
    binary_stream.write(getfilesize(fulloutname))
    binary_stream.write(bytes(outname, 'ASCII')) # Filename
    binary_stream.write(bytes(encodegps(exif), 'ASCII')) # GPS
    binary_stream.write(bytes('        ', 'ASCII')) # 8 spaces

def paint_text(img, text):
    # Get drawing context
    draw = ImageDraw.Draw(img)
    # Amble-Bold will be included in distribution
    font = ImageFont.truetype('Amble-Bold.ttf', 48)
    with_newlines = text.replace('\\','\n')
    c = Color(colour)
    ct = tuple(int(255*v) for v in c.rgb)
    draw.text((5,5), with_newlines,ct,font=font)


def shrink_image(image, saveto, text, colour):
    print(f'Write -> {saveto}')
    # image = Image.open(picpath)
    image.thumbnail((320,240))
    if text != None:
        paint_text(image, text)
    image.save(saveto)

def write_fat(logpath, pic_count):
    with open(os.path.join(outdir, 'QSOLOG','QSOPCTFAT.DAT'), 'wb') as f:
        for pnum in range(pic_count):
            f.write(bytes(b'\x40'))
            addr = 0X80 * pnum
            f.write(addr.to_bytes(3, byteorder='big', signed=False))

def write_mng(logpath, msg_count, pic_count, grp_count):
    with open(os.path.join(outdir, 'QSOLOG','QSOMNG.DAT'), 'wb') as f:
        f.write(msg_count.to_bytes(2, byteorder='big', signed=False))
        f.write(bytes(b'\xff' * 14)) # Padding
        f.write(pic_count.to_bytes(2, byteorder='big', signed=False))
        f.write(grp_count.to_bytes(2, byteorder='big', signed=False))
        f.write(bytes(b'\xff' * 12)) # Padding

if __name__ == '__main__':
    arguments = docopt(__doc__, version='YSF Image Copy 0.0')
    print(arguments)

    file_name = arguments['--file']
    dir_name = arguments['--dir']
    text = arguments['--text']
    colour = arguments['--colour']
    outdir = arguments['OUTDIR']
    radioid = arguments['RADIOID']
    callsign = arguments['CALLSIGN']

    if colour == None:
        colour = 'red' 

    next_pic_num = 1

    with io.BytesIO() as bs:
        if file_name is not None:
            write_log(bs, file_name, callsign, radioid, outdir, next_pic_num, text, colour)
            next_pic_num += 1

        if dir_name is not None:
            for filename in os.listdir(dir_name):
                try:
                    fullfname = os.path.join(dir_name, filename)
                    write_log(bs, fullfname, callsign, radioid, outdir, next_pic_num, text, colour)
                    next_pic_num += 1
                except IOError as e:
                    print("cannot convert", filename, e)

        with open(os.path.join(outdir, 'QSOLOG','QSOPCTDIR.DAT'), 'wb') as f:
            f.write(bs.getvalue())

    write_fat(outdir, next_pic_num)
    write_mng(outdir, 0, next_pic_num, 0)
