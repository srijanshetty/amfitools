'''
Fetch data from AMFI services and parse it to a machine consumable format
'''
import json
import pathlib
import logging
import os
import re
import sys
import time
from typing import Dict, List

import requests

# Log level
logging.getLogger().setLevel('CRITICAL')

# Config values
AMFI_URL = 'https://www.amfiindia.com/spages/NAVAll.txt'
PATH = '.amfi.json'
STALENESS = 84600

def request_text_array(url: str) -> List[str]:
    '''
    Request an endpoint and return array of lines
    '''
    response = requests.get(url)

    # Get the text and split it out on line endings
    return response.text.split('\n')

def write_json_to_file(data: Dict[str, float], target: pathlib.Path) -> None:
    '''
    Dump JSON to file
    '''
    logging.warning('Writing data to %s', target)

    with open(target, 'w') as target_handle:
        json.dump(data, target_handle)

def generate_amfi_file(url: str) -> Dict[str, float]:
    '''
    Prune the file for empty data
    '''

    # Fetch data from source
    logging.warning('Will fetch data for AMFI from: %s', url)
    data = request_text_array(url)

    # Data lines begin with a number prefix
    pattern = re.compile(r'^\d+')

    logging.info('Processing AMFI data')
    result: Dict[str, float] = {}
    for line in data:
        if pattern.match(line):
            item = line.split(';')
            try:
                result[item[3]] = float(item[4])
            except ValueError:
                logging.error('No price for %s', item[3])

    return result

def normalize_key(key: str) -> str:
    '''
    Normalize strings for comparison
    '''
    return key.lower().replace(' ', '').replace('-', '')

def main():
    '''
    Main entry point
    '''

    # Remove spaces and whitespace from query
    query = normalize_key(sys.argv[1])

    # Path to store the file in
    file_name = pathlib.Path(pathlib.Path.home(), PATH)

    # Generate or load the data from AMFI
    data = None
    if os.path.exists(file_name):
        file_stat = os.stat(file_name)

        # This only checks if the file is older than 24hrs
        if int(time.time()) - file_stat.st_mtime < STALENESS:
            with open(file_name, 'r') as file_pointer:
                data = json.load(file_pointer)


    # If data is still None, regenerate
    if data is None:
        data = generate_amfi_file(AMFI_URL)

        # Store to file if specified
        write_json_to_file(data, file_name)

    # Query the data
    for key, value in data.items():
        if query in normalize_key(key):
            print(f'{key:<50} {value:>20}')

if __name__ == "__main__":
    main()
