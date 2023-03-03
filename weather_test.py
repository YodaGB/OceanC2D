# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 19:44:06 2023

@author: Goutam
"""
import pandas as pd
import json
import os
import pickle
import sys
def get_input(local=False):
    if local:
        print("Reading local file covid19_cases.csv.")

        return "weather.csv"

    dids = os.getenv("DIDS", None)

    if not dids:
        print("No DIDs found in environment. Aborting.")
        return

    dids = json.loads(dids)

    for did in dids:
        filename = f"data/inputs/{did}/0"  # 0 for metadata service
        print(f"Reading asset file {filename}.")

        return filename
def run_covidstats(local=False):
    filename = get_input(local)
    if not filename:
        print("Could not retrieve filename.")
        return
    weather_full = pd.read_csv(filename)
    weather_truncated = weather_full.head(100)

    
    if local:
        print("Truncated weather ",weather_truncated)
        
    filename = "covid_stats.pickle" if local else "/data/outputs/result"
    with open(filename, "wb") as pickle_file:
        print(f"Pickling results in {filename}")
        pickle.dump(weather_truncated, pickle_file)
if __name__ == "__main__":
    print("Argv1 " ,sys.argv[1])
    local = len(sys.argv) == 2 and sys.argv[1] == "local"
    print("local ",local)
    run_covidstats(local)