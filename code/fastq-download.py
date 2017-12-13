#!/usr/bin/env python

"""Download FASTQ files from core FTP server.

Usage:
  fastq-download.py <md5file> <remotedir> <outdir>

Arguments:
  md5file       The file with md5 checksums provided by the core.
  remotedir     The path on the remote filesystem to the FASTQ files.
  outdir        The path on the local filesystem to save the FASTQ files.

Options:
  -h --help     Show this screen.

"""

# Example usage:
#   python code/fastq-download.py data/md5-core/YG-PYT-171013.md5 /Genomics/NGS-2017/171013_700819F_0577_ACAWPAACXX-YG-PYT-Flowcell-C/FastQ /project2/gilad/singlecell-qtl/fastq
#
# Implementation details:
#
# The md5 file has 2 columns, no header, and is space-delimted. The first column
# is the md5 checksum. The second column is the file, though the path is not the
# same as on the FTP server, and thus must be discarded. Also the file contains
# the checksums for other miscellaneous files that need to be skipped. This
# script only donwloads fastq.gz files, and also exlcudes the Undetermined
# files. Here are two example lines from an input file:
#
# 325d0c181a861ca7e512ebc6ff3090dd  /media/data1/NewSequencerRuns/171013_700819F_0577_ACAWPAACXX/Unaligned_YG-PYT-FC-C/YG-PYT-FC-C-04072017-A01_S1_L001_R1_001.fastq.gz
# b6d1245f26418113a26395ef37139442  /media/data1/NewSequencerRuns/171013_700819F_0577_ACAWPAACXX/Unaligned_YG-PYT-FC-C/YG-PYT-FC-C-04072017-A02_S2_L001_R1_001.fastq.gz
#
# The downloaded files are further organized on the local filesystem. Each FASTQ
# is put in a subdirectory corresponding to the C1 chip the single cell came
# from. It will look something like this:
#
# fastq
# ├── 03162017
# │   ├── YG-PYT-FC-A-03162017-A01_S1_L001_R1_001.fastq.gz
# │   ├── YG-PYT-FC-A-03162017-A02_S2_L001_R1_001.fastq.gz
# │   ├── YG-PYT-FC-A-03162017-A03_S3_L001_R1_001.fastq.gz
# │   ├── YG-PYT-FC-A-03162017-A04_S4_L001_R1_001.fastq.gz
# │   └── YG-PYT-FC-A-03162017-A05_S5_L001_R1_001.fastq.gz
# ├── 03172017
# ├── 03232017
# ├── 03302017
# ├── 03312017
# ├── 04052017
# ├── 04072017
# └── 04132017
#
# The script does 1 of 3 things depending on the download status of the file:
#
# 1. If the file exists on the remote server, but not on the local machine, the
# file is downloaded and its md5 checksum verified. If they don't match, the
# file is removed.
#
# 2. If the file exists on the remote server and on the local machine, its md5
# checksum is verified. If they don't match, the file is removed.
#
# 3. If the file does not exist on the remote server, a warning message is sent
# to standard error and the file is skipped.

import docopt
import getpass
import hashlib
import os
import pysftp
import sys

def main(md5file, remotedir, outdir = ".", hostname = "fgfftp.uchicago.edu",
         username = "gilad"):

    # Connect to server
    p = getpass.getpass("Authenticate: ")
    sftp = pysftp.Connection(hostname, username = username, password = p)

    # Import md5 checksums computed by core
    md5_core = open(md5file, "r")

    # Download each file individually and verify the md5 checksum
    for line in md5_core:
        cols = line.strip().split()
        md5 = cols[0]
        fname = os.path.basename(cols[1])
        if "Undetermined" in fname or fname[-8:] != "fastq.gz":
            continue
        sys.stdout.write("Downloading %s\n"%(fname))
        # Organize the FASTQ files into subdirectories based on the C1 chip
        chip = fname.split("-")[4]
        outdir_chip = outdir + "/" + chip
        os.makedirs(outdir_chip, exist_ok = True)
        localpath = outdir_chip + "/" + fname
        remotepath = remotedir + "/" + fname
        #import ipdb; ipdb.set_trace()
        if not sftp.exists(remotepath):
            sys.stderr.write("Does not exist on remote server:\t%s\n"%(remotepath))
            continue
        elif os.path.exists(localpath):
            sys.stderr.write("Already exists:\t%s\n"%(remotepath))
        else:
            sftp.get(remotepath, localpath)
        if not os.path.exists(localpath):
            sys.stderr.write("Download failed:\t%s\n"%(remotepath))
            continue
        with open(localpath, "rb") as fq:
            md5_local = hashlib.md5(fq.read()).hexdigest()
            if md5_local != md5:
                sys.stderr.write("Download incomplete:\t%s\n"%(remotepath))
                os.remove(localpath)

    md5_core.close()
    sftp.close()

if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(md5file = args["<md5file>"],
         remotedir = args["<remotedir>"],
         outdir = args["<outdir>"])
