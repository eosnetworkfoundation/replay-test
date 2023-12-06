"""Parse Orchestration File and Calculate Job Elapsed Time"""
import argparse
from datetime import datetime
import statistics
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='helper script to extract elapsed timing from log')
    parser.add_argument('--log', type=str, help='path to config file')

    args = parser.parse_args()
    timings = []

    # Open the file and read log_entry by log_entry
    with open(args.log, 'r', encoding='utf-8') as file:
        for log_entry in file:
            # Check if the specific phrase is in the current log_entry
            if "OrchWebSrv INFO Completed Job" in log_entry:
                # Print the log_entry or perform other actions
                for part in log_entry.split(','):
                    if 'starttime' in part:
                        starttimestr = part.split(': ', 1)[1]
                        starttime = datetime.strptime(starttimestr, '%Y-%m-%dT%H:%M:%S')
                    elif 'endtime' in part:
                        endtimestr = part.split(': ', 1)[1]
                        endtime = datetime.strptime(endtimestr, '%Y-%m-%dT%H:%M:%S')
                    elif 'jobid' in part:
                        jobid = part.split(': ', 1)[1].strip()
                # calc elapsed time
                timedelta = endtime - starttime
                # Convert the difference to total seconds
                total_minutes = int(timedelta.total_seconds())/60
                timings.append(total_minutes)
                #print(f"Job {jobid} elapsed time in minutes {total_minutes}")

    # Calculate average (mean)
    average = statistics.mean(timings)

    # Calculate standard deviation
    std_dev = statistics.stdev(timings)

    # Calculate median
    median = statistics.median(timings)

    # Calculate the 75th and 90th percentiles
    percentile_75 = np.percentile(timings, 75)
    percentile_90 = np.percentile(timings, 90)

    # get longest
    longest = max(timings)

    # Print the results
    print("JOB TIMING ALL TIMES IN MINUTES")
    print("-------------------------------")
    print(f"Number of Jobs: {len(timings)}")
    print(f"Average: {round(average,2)}")
    print(f"Standard Deviation: {round(std_dev,2)}")
    print(f"Median: {round(median,2)}")
    print(f"75th Percentile: {round(percentile_75,2)}")
    print(f"90th Percentile: {round(percentile_90,2)}")
    print(f"Longest Running Job {round(longest,2)} mins")
