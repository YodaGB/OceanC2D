# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 17:38:35 2023

@author: Goutam
"""

#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pickle
import sys

#import arff
#import matplotlib
import numpy
#from matplotlib import pyplot
#from sklearn import gaussian_process
#import csv


def get_input(local=False):
    if local:
        print("Reading local file salary_data.csv.")

        return "salary_data.csv"

    dids = os.getenv("DIDS", None)

    if not dids:
        print("No DIDs found in environment. Aborting.")
        return

    dids = json.loads(dids)

    for did in dids:
        filename = f"data/inputs/{did}/0"  # 0 for metadata service
        print(f"Reading asset file {filename}.")

        return filename

def run_myalgo(local=False):
    #npoints = 15

    filename = get_input(local)
    if not filename:
        print("Could not retrieve filename.")
        return
    arr = numpy.loadtxt(filename,
                 delimiter=",", dtype=str)

    if local:
        print("Array ",arr)
        
    filename = "myalgo.pickle" if local else "/data/outputs/result"
    with open(filename, "wb") as pickle_file:
        print(f"Pickling results in {filename}")
        pickle.dump(arr, pickle_file)


if __name__ == "__main__":
    local = len(sys.argv) == 2 and sys.argv[1] == "local"
    run_myalgo(local)