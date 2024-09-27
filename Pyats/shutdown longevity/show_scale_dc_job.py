import os
import sys
import yaml
import itertools
from pathlib import Path
from ats.easypy import run


os.environ['IP'] = ''
test_data = {}
tb = ""
def main(runtime):


    if not runtime.args.logical_testbed_file:
        print("Missing Required Testcase Datafile: -logical_testbed_file PATH_TO_DATAFILE")
        exit()
    else:
       with open(runtime.args.logical_testbed_file) as file:
           test_data = yaml.load(file, Loader=yaml.FullLoader)
           test_data['runtime'] = runtime

    if not runtime.args.testbed_file:
        print("Missing Required Testbed File: -testbed_file PATH_TO_TESTBEDFTLE")
        exit()
    else:
        tb = runtime.args.testbed_file

    if '-uut' in sys.argv:
        print(sys.argv.index('-uut'))
        if  sys.argv[sys.argv.index('-uut') + 1]:
            test_data['UUT'] = sys.argv[sys.argv.index('-uut') + 1]
  
    args = itertools.cycle(sys.argv)
    max_arg_len = len(sys.argv)
    for i in range(max_arg_len):
        nextargv = next(args)
        if nextargv.startswith("-") and nextargv not in ['-testcase','-testdata','-uut']:
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

    testscript_list = ['show_scale_dc.py']
    
    mypath = os.path.dirname(os.path.abspath(__file__))
    if Path(__file__).is_symlink():
        mypath = os.path.dirname(os.readlink(__file__))
    for script_name in testscript_list:
        run(testscript=mypath +"/"+ script_name, testbed_file=tb, test_data=test_data)
