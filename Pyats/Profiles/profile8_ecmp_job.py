import os
import sys
import yaml
import logging
import itertools
from pathlib import Path
import random
import re
import ast
import time
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
from ats.log.utils import banner

from ats.easypy import run


os.environ['IP'] = ''
test_data = {}
tb = ""

def get_time(time):
    multiplier = 1
    pattern = "(\d*).*s"
    if time.endswith("ms"):
        multiplier  = 0.001
        pattern = "(\d*).*ms"
    result = re.search(pattern,time)
    if result:
        return int(result.group(1)) * multiplier
    return 0

def main(runtime):

    if not runtime.args.logical_testbed_file:
        print("Missing Required Testcase Datafile: -logical_testbed_file PATH_TO_DATAFILE")
        exit()
    else:
       with open(runtime.args.logical_testbed_file) as file:
           test_data = yaml.load(file, Loader=yaml.FullLoader)
           test_data['runtime'] = runtime

    if '-uut' in sys.argv:
        if  sys.argv[sys.argv.index('-uut') + 1]:
            test_data['UUT'] = sys.argv[sys.argv.index('-uut') + 1]

    if '-userid' in sys.argv:
        if  sys.argv[sys.argv.index('-userid') + 1]:
            test_data['userid'] = sys.argv[sys.argv.index('-userid') + 1]
    if '-upload_log' in sys.argv:
        if  sys.argv[sys.argv.index('-upload_log') + 1]:
            test_data['upload_result'] = sys.argv[sys.argv.index('-upload_log') + 1]

    args = itertools.cycle(sys.argv)
    max_arg_len = len(sys.argv)
    for i in range(max_arg_len):
        nextargv = next(args)
        if nextargv.startswith("-") and nextargv not in ['-testdata','-uut','-upload_log']:
            if len(nextargv) > 1:
                if i + 1 <= max_arg_len - 1:
                    if not sys.argv[i+1].startswith("-"):
                        test_data[nextargv.split("-")[1]] = sys.argv[i+1]
                    else:
                        test_data[nextargv.split("-")[1]] = ""
                else:
                    test_data[nextargv.split("-")[1]] = ""
            else:
                print("invalid args %s" % (nextargv))
                exit()

    pdb = False

    if not runtime.args.testbed_file:
        print("Missing Required Testbed File: -testbed_file PATH_TO_TESTBEDFTLE")
        exit()
    else:
        tb = runtime.args.testbed_file

    if Path(__file__).is_symlink():
        mypath = os.path.dirname(os.readlink(__file__))
    else:
        mypath = os.path.dirname(os.path.abspath(__file__))

    run(testscript=mypath +"/profile8_ecmp.py", testbed_file=tb, test_data=test_data)
