#!/usr/bin/env python3

r"""given a pdf file with large white margins
this scrips will remove them.
"""

import os
import argparse
import pdfCropMargins
import subprocess
import shutil


def crop_file(filename):

    if filename == "" or not os.path.exists(filename):
        print("No valid filename provided")
        exit()

    # make a backup iof the file
    bk_file = os.path.splitext(filename)[0] + "_bk.pdf"
    shutil.copyfile(filename, bk_file)

    cmd = f"pdf-crop-margins -v -s -u {filename}"

    proc = subprocess.Popen(cmd.split())
    proc.wait()

    fname = os.path.basename(filename)
    cropped_file = os.path.splitext(fname)[0] + "_cropped.pdf"

    shutil.move(cropped_file, filename)


if __name__ == "__main__":
    description = __doc__
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=formatter)
    
    parser.add_argument('-f', '--file', help="""Pdf file to crop.""")

    args = parser.parse_args()
    filename = args.file

    crop_file(filename)
