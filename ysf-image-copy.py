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
#from shutil import copyfile # Used to copy jpg. Not if we write it?

from docopt import docopt

# photofilename = r'TestImages/StileNoExif.JPG'
# exiffilename = r'TestImages/StileExif.JPG'
outdir = r'TestOut'

radio_id = 'E0Spx'
callsign = 'G4TJC'

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

# def get_decimal_from_dms(dms, ref):

#     degrees = dms[0][0] / dms[0][1]
#     minutes = dms[1][0] / dms[1][1] / 60.0
#     seconds = dms[2][0] / dms[2][1] / 3600.0

#     if ref in ['S', 'W']:
#         degrees = -degrees
#         minutes = -minutes
#         seconds = -seconds

#     return round(degrees + minutes + seconds, 5)

# def get_coordinates(geotags):
#     lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])

#     lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])

#     return (lat,lon)

def encodegps(filename):
    exif = get_exif(filename)
    # print(f"exif from {filename}:")
    # print(exif)
    try:
        geotags = get_geotagging(exif)
    except ValueError:
        # No EXIF GPS data
        return "                    "
    try:
        print(f"geotags from {filename}:")
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
        return "                    "

def get_date_taken(path):
    try:
        dto_str = Image.open(path)._getexif()[36867]
        return datetime.strptime(dto_str, '%Y:%m:%d %H:%M:%S')
    except KeyError:
        # No EXIF data for datetime
        return datetime.now()

def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()

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


def write_log(binary_stream, picfile, outdir, picnum, text, colour):
    print(f'Write log entry for {picfile}')
    binary_stream.write(bytes(b'\x00\x00\x00\x00')) # Head
    binary_stream.write(bytes(b'\x20\x20\x20\x20\x20')) # Node ID
    binary_stream.write(bytes('ALL       ', 'ASCII')) # Dest
    binary_stream.write(bytes('      ', 'ASCII')) # 6 spaces
    binary_stream.write(bytes(radio_id, 'ASCII')) # Radio ID
    # binary_stream.write(bytes('G4TJC     ', 'ASCII')) # Call sign
    # binary_stream.write(bytes('      ', 'ASCII')) # 6 spaces
    binary_stream.write(bytes(callsign.ljust(16), 'ASCII')) # Callsign in 16-char field
    writedate(binary_stream, datetime.now() - timedelta(hours = 1))
    writedate(binary_stream, datetime.now())
    taken = get_date_taken(picfile)
    writedate(binary_stream, taken)
    binary_stream.write(
        bytes('{:11.11}'.format(os.path.basename(picfile)), 'ASCII')
    ) # Description
    binary_stream.write(bytes('     ', 'ASCII')) # 5 spaces
    outname = picfilename(radio_id, picnum)
    fulloutname =  os.path.join(outdir, 'PHOTO', outname)
    print(f'Convert {picfile} -> {outname}')
    shrink_image(picfile,fulloutname, text, colour)
    binary_stream.write(getfilesize(fulloutname))
    binary_stream.write(bytes(outname, 'ASCII')) # Call sign
    binary_stream.write(bytes(encodegps(picfile), 'ASCII')) # GPS
    binary_stream.write(bytes('        ', 'ASCII')) # 8 spaces

def load_font():
    fonts = [
        'verdana.ttf',
        'helvetica.ttf',
        'arial.ttf',
        'tahoma.ttf',
        'sans-serif.ttf',
    ]

    for font_name in fonts:
        try:
            font = ImageFont.truetype(font_name, 48)
            return font
        except OSError as e:
            print("Font problem.", e, font_name)

    return ImageFont.load_default()


def shrink_image(picpath, saveto, text, colour):
    print(f'{picpath} -> {saveto}')
    image = Image.open(picpath)
    image.thumbnail((320,240))
    draw = ImageDraw.Draw(image)
    font = load_font()
    with_newlines = text.replace('\\','\n')
    c = Color(colour)
    ct = tuple(int(255*v) for v in c.rgb)
    draw.text((0,0), with_newlines,ct,font=font)
    image.save(saveto)

def process_pic(file_name, outdir, picnum):
    with io.BytesIO() as bs:
        write_log(bs, file_name, outdir, picnum)

        #print_output(bs, 16)

        #exif = get_exif(photofilename)
        #print(outdir)

        with open(os.path.join(outdir, 'QSOLOG','QSOPCTDIR.DAT'), 'wb') as f:
            f.write(bs.getvalue())


if __name__ == '__main__':
    arguments = docopt(__doc__, version='YSF Image Copy 0.0')
    print(arguments)

    file_name = arguments['--file']
    dir_name = arguments['--dir']
    text = arguments['--text']
    colour = arguments['--colour']

    if colour == None:
        colour = 'red' 

    next_pic_num = 1

    with io.BytesIO() as bs:
        if file_name is not None:
            write_log(bs, file_name, outdir, next_pic_num, text, colour)
            next_pic_num += 1

        if dir_name is not None:
            for filename in os.listdir(dir_name):
                try:
                    fullfname = os.path.join(dir_name, filename)
                    write_log(bs, fullfname, outdir, next_pic_num, text, colour)
                    next_pic_num += 1
                except IOError as e:
                    print("cannot convert", filename, e)

        with open(os.path.join(outdir, 'QSOLOG','QSOPCTDIR.DAT'), 'wb') as f:
            f.write(bs.getvalue())
            
    with open(os.path.join(outdir, 'QSOLOG','QSOPCTFAT.DAT'), 'wb') as f:
        for pnum in range(next_pic_num):
            f.write(bytes(b'\x40'))
            addr = 0X80 * pnum
            f.write(addr.to_bytes(3, byteorder='big', signed=False))

    # copyfile(photofilename, os.path.join(outdir, 'PHOTO', outname))
