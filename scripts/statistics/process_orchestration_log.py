"""Parse Orchestration File and Calculate Job Elapsed Time"""
import argparse
import sys
from datetime import datetime
import statistics
import numpy as np
from replay_configuration import ReplayConfigManager

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='helper script to extract elapsed timing from log')
    parser.add_argument('--log', type=str, help='path to config file')
    parser.add_argument('--block-times', action=argparse.BooleanOptionalAction, \
        default=False, help='collect times by block range')
    parser.add_argument('--config', type=str, help='path to config file used in run')

    args = parser.parse_args()
    timings = []

    if args.block_times and not args.config:
        sys.exit("Must provide config with --config option")

    # Open the file and read log_entry by log_entry
    with open(args.log, 'r', encoding='utf-8') as file:
        for log_entry in file:
            # Check if the specific phrase is in the current log_entry
            if "OrchWebSrv INFO Completed Job" in log_entry:
                complete_record = {}
                # Print the log_entry or perform other actions
                for part in log_entry.split(','):
                    if 'starttime' in part:
                        starttimestr = part.split(': ', 1)[1]
                        complete_record['starttime'] = datetime.strptime(
                        starttimestr, '%Y-%m-%dT%H:%M:%S')
                    elif 'endtime' in part:
                        endtimestr = part.split(': ', 1)[1]
                        complete_record['endtime'] = datetime.strptime(
                        endtimestr, '%Y-%m-%dT%H:%M:%S')
                    elif 'jobid' in part:
                        complete_record['jobid'] = part.split(': ', 1)[1].strip()
                    elif 'config' in part:
                        complete_record['config'] = part.split(': ', 1)[1].strip()
                    elif 'snapshot' in part:
                        complete_record['snapshot'] = part.split(': ', 1)[1].strip()
                # calc elapsed time
                timedelta = complete_record['endtime'] - complete_record['starttime']
                # Convert the difference to total minutes
                complete_record['total_minutes'] = int(timedelta.total_seconds())/60
                timings.append(complete_record)

    if args.block_times:
        replay_config_manager = ReplayConfigManager(args.config)
        for record in timings:
            block_manager = replay_config_manager.get(record['config'])
            config = block_manager.as_dict()
            block_span = config['end_block_id'] - config['start_block_id']
            average_time = round(record['total_minutes'] / block_span,2)
            blocks_for_3_hours = round(60 * 3 / average_time,0)
            print (f"{config['start_block_id']}, {config['end_block_id']}, {average_time}, {blocks_for_3_hours}")
    else:
        # Calculate average (mean)
        average = statistics.mean(list(record['total_minutes'] for record in timings))

        # Calculate standard deviation
        std_dev = statistics.stdev(list(record['total_minutes'] for record in timings))

        # Calculate median
        median = statistics.median(list(record['total_minutes'] for record in timings))

        # Calculate the 75th and 90th percentiles
        percentile_75 = np.percentile(list(record['total_minutes'] for record in timings), 75)
        percentile_90 = np.percentile(list(record['total_minutes'] for record in timings), 90)

        # get longest
        longest = max(list(record['total_minutes'] for record in timings))

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

        if std_dev > average:
            print("\nLONG RUNNING JOBS TOP 90%")
            print("-------------------------")
            for record in timings:
                if record['total_minutes'] > percentile_90:
                    # when config and snapshot exist print full
                    # field check for backwards compat
                    if 'config' in record and 'snapshot' in record \
                        and record['config'] and record['snapshot']:
                        print(f"Job {record['jobid']}\
 running time {round(record['total_minutes'],2)}\
 config {record['config']} with snapshot {record['snapshot']}")
                    else:
                        print(f"Job {record['jobid']}\
 running time {round(record['total_minutes'],2)}")
