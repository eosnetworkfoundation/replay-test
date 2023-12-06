"""Parse Config File and Checks"""
import json
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='helper script to validates manifest that drives chicken dance')
    parser.add_argument('--config', type=str, help='path to config file')

    args = parser.parse_args()
    continuity = {}

    with open(args.config, 'r', encoding='utf-8') as file:
        # Parse the JSON data
        data = json.load(file)
        for record in data:
            continuity[record['start_block_id']] \
                = { 'end_block_id':record['end_block_id'], 'checked':False }

    # also validates keys are ints
    sorted_start_blocks = sorted(continuity, key=int)
    biggest_start_block_id = sorted_start_blocks[-1]
    # all end block except for the vary last have a corresponding start block
    for key, block in continuity.items():
        # check this end block has a correcsponding start
        # and end block is an int
        if key == biggest_start_block_id:
            block['checked'] = True
        elif continuity[block['end_block_id']] \
            and isinstance(int(block['end_block_id']), int):
            block['checked'] = True

    for key, block in continuity.items():
        if not block['checked']:
            print(f"Error: start block id {key} does not have following record")
        else:
            print(f"Good: Validated range {key} to {block['end_block_id']}")
