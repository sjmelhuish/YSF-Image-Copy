import io
import binascii
from datetime import datetime, timedelta
import os
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS

from shutil import copyfile # Used to copy jpg. Not if we write it?

photofilename = r'TestImages/StileNoExif.JPG'
exiffilename = r'TestImages/StileExif.JPG'
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

def get_decimal_from_dms(dms, ref):

    degrees = dms[0][0] / dms[0][1]
    minutes = dms[1][0] / dms[1][1] / 60.0
    seconds = dms[2][0] / dms[2][1] / 3600.0

    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 5)

def get_coordinates(geotags):
    lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])

    lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])

    return (lat,lon)

def encodegps(filename):
    exif = get_exif(filename)
    geotags = get_geotagging(exif)
    #print(get_coordinates(geotags))
    return '{:1.1}{:03d}{:02d}{:04d}{:1.1}{:03d}{:02d}{:04d}'.format(
        geotags['GPSLatitudeRef'],
        geotags['GPSLatitude'][0][0],
        geotags['GPSLatitude'][1][0],
        geotags['GPSLatitude'][2][0],
        geotags['GPSLongitudeRef'],
        geotags['GPSLongitude'][0][0],
        geotags['GPSLongitude'][1][0],
        geotags['GPSLongitude'][2][0],
    )

def get_date_taken(path):
    dto_str = Image.open(path)._getexif()[36867]
    return datetime.strptime(dto_str, '%Y:%m:%d %H:%M:%S')

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
        print("{:02d} -> {:02d} (0x{:02x})".format(z,n,n))
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

binary_stream = io.BytesIO()

binary_stream.write(bytes(b'\x00\x00\x00\x00')) # Head
binary_stream.write(bytes(b'\x20\x20\x20\x20\x20')) # Node ID
binary_stream.write(bytes('ALL       ', 'ASCII')) # Dest
binary_stream.write(bytes('      ', 'ASCII')) # 6 spaces
binary_stream.write(bytes(radio_id, 'ASCII')) # Radio ID
binary_stream.write(bytes('G4TJC     ', 'ASCII')) # Call sign
binary_stream.write(bytes('      ', 'ASCII')) # 6 spaces
writedate(binary_stream, datetime.now() - timedelta(hours = 1))
writedate(binary_stream, datetime.now())
taken = get_date_taken(exiffilename)
writedate(binary_stream, taken)
binary_stream.write(
    bytes('{:11.11}'.format(os.path.basename(photofilename)), 'ASCII')
) # Description
binary_stream.write(bytes('     ', 'ASCII')) # 5 spaces
binary_stream.write(getfilesize(photofilename))
outname = picfilename(radio_id,1)
binary_stream.write(bytes(outname, 'ASCII')) # Call sign
binary_stream.write(bytes(encodegps(exiffilename), 'ASCII')) # GPS
binary_stream.write(bytes('        ', 'ASCII')) # 8 spaces


print_output(binary_stream, 16)

#exif = get_exif(photofilename)
print(outname)

with open(os.path.join(outdir, 'QSOLOG','QSOPCTDIR.DAT'), 'wb') as f:
    f.write(binary_stream.getvalue())
binary_stream.close()

with open(os.path.join(outdir, 'QSOLOG','QSOPCTFAT.DAT'), 'wb') as f:
    f.write(bytes(b'\x40\x00\x00\x00'))


copyfile(photofilename, os.path.join(outdir, 'PHOTO', outname))

