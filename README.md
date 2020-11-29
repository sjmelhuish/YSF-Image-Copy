# YSF-Image-Copy

This project comprises a Python script, the purpose of which is to facilitate the copying of picture image files onto &mu;SD cards used by certain amateur radio VHF/UHF transceivers. The image file will be re-formatted for compatibility and associated metadata files created/updated. The end result will be that image files are usable on the rig, allowing transmission over the air.

## Introduction

Various models of radio made by [Yaesu](https://www.yaesu.com/ "Yaesu home page") provide for image transfer
using Yaesu's C4FM mode - [Yaesu System Fusion](http://systemfusion.yaesu.com/what-is-system-fusion/ "What is System Fusion?").
Typically this is used with Yaesu's MH‑85A11U microphone, which has a built-in snapshot camera.
Some radio models have a screen suitable for viewing these images. Others do not, but still allow for 
image exchange, but with the pictures having to be transferred to a computer using the &mu;SD card first.

The purpose of this script is to allow for pictures from sources other than the MH‑85A11U microphone to be used.
Picture files are manipulated on a computer and transferred onto the rig's &mu;SD card.

## Files

The &mu;SD card as formatted within the rig contains a `PHOTO` directory, where received images are held.
One might naively expect that simply placing a JPEG picture file into this directory would make it 
available for viewing or transmitting.
Of course there are restrictions on image size, to match the small size of snapshots taken with the MH‑85A11U
and allowing for the small screen size.
But you might, for example, expect a 320 &times; 240 pixel image to work.

It is quickly found that this is not the case.
There are tighter restrictions on the images allowed other than just the extent.
The file size must be below 40kB and it seems the image must not contain EXIF data or be a progressive JPEG.
These both add to the file size, so it anyway makes sense to avoid these options, leaving more space
available for a better image quality setting or a smaller size with faster over-the-air transmission.

But again, even with these further restrictions a JPEG alone is not recognised.

Several users of camera-equipped rigs looked into this and found that the reason was that
as well as the JPEG file in the `PHOTO` directory it was necessary to have various entries in
files in the `QSOLOG` directory, namely `QDOPCTDIR.DAT` and `QDOFATDIR.DAT`.

Please refer to the following studies:

* [W5NYV / KB5MU](http://www.bigideatrouble.com/SystemFusionExploration.pdf "System Fusion Exploration - April 2015")
* [PH0PPL](https://docs.google.com/viewer?a=v&pid=sites&srcid=ZGVmYXVsdGRvbWFpbnxmbGZ1c2lvbndpa2l8Z3g6MjJhMGE0MjJlZWM5ZGEwZQ "YAESU FTM-400D – SDCARD EXPLORATION – AUGUSTUS 2015")
* [IU4GOX](https://docs.google.com/spreadsheets/d/1PwzVF22pcLmB04uWrRkx8IWbQs3NnVsqAb-y3qHnhVk/edit#gid=1180833404 "IU4GOX YEASU QSO Filesystem Structure")
* [KI6ZHD](http://www.trinityos.com/HAM/Yaesu-System-Fusion/Ysf-camera-mic-results/ysf-camera-mic-results.txt "Yaesu FT1/FT2/FTM100/FTM400 DATA jack with the Yaesu Camera Mic")

## Image Sizes

Two image sizes are supported:

* 160 &times; 120
* 320 &times; 240

Compression quality can be adjusted to size the file for transmission speed.
The file size limit is 40 kB.

## Usage
  `ysf-image-copy.py CALLSIGN RADIOID OUTDIR [-d DIRECTORY|-f PICFILE] [-u] [-t TEXT] [-c COLOUR]`
  
* `CALLSIGN`            is your call sign
* `RADIOID`             is the Radio ID to insert (find this under the GM settings on your radio)
* `OUTDIR`              is the output directory
  
| Option | Explanation |
| :-- | :-- |
  `-h --help`                          | Show this screen
  `-v --version`                       | Show version
  `-d DIRECTORY --dir=DIRECTORY`       | Name the input directory forbatch conversion
  `-f PICFILE --file=PICFILE`          | Convert a single file
  `-t TEXT --text=TEXT`                | Write text over image
  `-c COLOUR --colour=COLOUR`          | Colour for the text
  `-u`                                 | Update files at outdir instead of starting from scratch

The `-u` option is not yet supported.

## Licensing

This utility is licensed under the GPL. Please see the included licence file.

The bundled font, Amble-Bold, is licensed under the Apache licence. Please see the included Apache Licence file.