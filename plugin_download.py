"""
This module downloads files uploaded to Waggle Beehive via the defined plugin

Script modified Bhupendra Raut's Mobotix Analysis at: 
https://github.com/RBhupi/Konza_Mobo_Analysis
"""

import argparse
import os

import datetime
from zoneinfo import ZoneInfo

import sage_data_client
import requests

def readtofile(uurl, fname, input_args):
    """
    Given a URL, read data to local files

    Parameters
    ----------
    uurl : str
        HTML consisting of file to download from Beehive
    fname : str
        Path for local location to store data into
    input_args : dictionary
        Input Argument dictionary
    """
    r = requests.get(uurl,
                     auth=(input_args.user, input_args.password),
                     timeout=25)
    print(r.status_code)
    if r.status_code == 200:
        print("Downloading ... ", fname)
        with open(fname, 'wb') as out:
            for bits in r.iter_content():
                out.write(bits)
    elif r.status_code == 404:
        print("404 Error: File Not Found")
    else:
        print("HTML Request Status - ", r.status_code)
    return True

def download_files_beehive(df, input_args):
    """
    Download files from Beehive given a pandas dataframe of their
    HTML locations

    Parameters
    ----------
    df : Pandas DataFrame
        Dataframe generated from Beehive JSON of file locations
    file_ext : str
        File extension of the files to download
    out_dir : str
        Path defined to save files to
    username : str
        Waggle/SAGE UI username
    password : str
        Waggle/SAGE UI authorized password
    """
    print("in download")
    url_locations = []
    beehive_timestamp = []
    beehive_files = []
    if "image_sampler" or "imagesampler" in input_args.plugin:
        print("in image_sampler")
        for i in range(len(df)):
            if input_args.extension in df.iloc[i].value:
                url_locations.append(df.iloc[i].value)
                beehive_timestamp.append(df.iloc[i].timestamp)
                beehive_files.append(input_args.node +
                                     "_" +
                                     beehive_timestamp[i].strftime("%Y%m%d_%H%M%S") +
                                     '_' + 
                                     df.iloc[i]["meta.filename"])
    else:
        for i in range(len(df)):
            if input_args.extension in df.iloc[i].value:
                url_locations.append(df.iloc[i].value)
                beehive_timestamp.append(df.iloc[i].timestamp)
                beehive_files.append(df.iloc[i]["meta.filename"])

    # Download and save to output directory
    for i, beehive_timestamp in enumerate(beehive_timestamp):
        filename = os.path.join(input_args.outdir, beehive_files[i])
        print(beehive_timestamp, filename)
        readtofile(url_locations[i], filename, input_args)

def main(input_args):
    """Download data from Beehive for the Plugin in Question"""

    print("\n")
    print("Node: ", input_args.node)
    print("Plugin: ", input_args.plugin)
    print("Task: ", input_args.task)
    print("Start Date: ", input_args.start_date)
    print("End Date: ", input_args.end_date)
    print("\n")

    # Define the JSON output for files in question
    if "image_sampler" or "imagesampler" in input_args.plugin:
        df = sage_data_client.query(start=input_args.start_date,
                                    end=input_args.end_date,
                                    filter={"vsn": input_args.node,
                                            "task": input_args.task,
                                            }
        )
    else:
        df = sage_data_client.query(start=input_args.start_date,
                                    end=input_args.end_date,
                                    filter={"vsn": input_args.node,
                                            "plugin": input_args.plugin,
                                            }
        )
    print(df)
    print("\n")
    print(df.iloc[0]["meta.plugin"])

    # Download the files
    download_files_beehive(df, input_args)

if __name__ == '__main__':

    # Define current time in utc
    now_utc = datetime.datetime.now(ZoneInfo("UTC"))

    parser = argparse.ArgumentParser(
        description="Script for Downloading Files Uploaded to Beehive via Plugins")
    parser.add_argument("--outdir",
                        type=str,
                        dest="outdir",
                        default=".",
                        help="[str] Directory where to output files to"
                        )
    parser.add_argument("--node",
                        type=str,
                        dest="node",
                        default="W09F",
                        help="[str] Waggle Node Where the Plugin Ran"
                        )
    parser.add_argument("--plugin",
                        type=str,
                        dest="plugin",
                        default="10.31.81.1:5000/local/waggle-parsivel-io.*",
                        help="[str] Waggle Plugin to Download Files From"
                        )
    parser.add_argument("--username",
                        type=str,
                        dest="user",
                        default="user",
                        help="[str] Waggle Account User Name"
                        )
    parser.add_argument("--password",
                        type=str,
                        dest="password",
                        default="password",
                        help="[str] Waggle Account Authorization Password"
                        )
    parser.add_argument("--start",
                        type=str,
                        default=(now_utc -
                                 datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:00Z'),
                        dest="start_date",
                        help="[str] Date to Start Downloading Data in YYYY-MM-DDThh:mm:ssZ format"
                        )
    parser.add_argument("--end",
                        type=str,
                        dest="end_date",
                        help="[str] Date to End Downloading Data in YYYY-MM-DDThh:mm:ssZ format",
                        default=now_utc.strftime('%Y-%m-%dT%H:%M:00Z')
                        )
    parser.add_argument("--ext",
                        type=str,
                        default="csv",
                        dest="extension",
                        help="[str] Extension of Files to Download"
                        )
    parser.add_argument("--task",
                        type=str,
                        default=None,
                        dest="task",
                        help="[str] Specific task assigned to various Plugins"
                        )
    args = parser.parse_args()

    main(args)
