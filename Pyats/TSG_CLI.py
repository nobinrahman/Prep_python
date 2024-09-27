#!/bin/env python

import sys

sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
from tabulate import tabulate
from datetime import datetime
from dateutil import parser
import os
import ast
import re
import csv
import random
import logging
import collections
import sste_snmp
import sste_common
import sste_tgn
import yaml
import pdb
import json
import collections
import sste_cli_keys
from pyats import aetest
import time
from ixnetwork_restpy import SessionAssistant
from stcrestclient import stchttp

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
from ats.log.utils import banner
from pyats.aetest.loop import Iteration
import time
from texttable import Texttable
from genie.utils import Dq
from genie.testbed import load
import msft_tsg_pattern

def tree(): return collections.defaultdict(tree)


try:
    cli_mapping = sste_cli_keys.cli_mapping
    cli_parser_exclude_keys = sste_cli_keys.cli_parser_exclude_keys
    cli_parser_non_matching_keys = sste_cli_keys.cli_parser_non_matching_keys
except ImportError:
    cli_parser_exclude_keys = {}
    cli_parser_non_matching_keys = {}
    cli_mapping = {}
    pass

coredump_list = []
showtech_list = []
#only dump physical interface which is up
interface_list = []
pkts_sec_value1 = 10
pkts_sec_value1 = 3
count_value1 = 10

def check_context(script_args):
    ##check dumper and trace
    global coredump_list, showtech_list, interface_list
    module_args = {}
    module_args['timeout'] = 300
    module_args['sste_commands'] = '["show context"]'
    output = sste_common.exec_commands(module_args, script_args)
    if output.count('Core location') and output.count('user requested') == 0 :
        contextPIB = output.split('Core for pid =')[-1].split('(')[-1].split(')')[0]
        contextLocation = output.split('Core location:')[-1].split('CPU0:')[-1].split()[0]
        contextLocation = contextLocation.replace(',', '')
        contextProcess = output.split('Core for process:')[-1].split()[0]
        core_dict = [contextLocation + '/' + contextProcess, contextProcess]
        coredump_list.append(core_dict)

        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show tech syslog"]'
        stoutput = sste_common.exec_commands(module_args, script_args)
        if stoutput.count('harddisk:/showtech/'):
            stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
            showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
            showtech_list.append(showtech_dict)
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show tech bundle"]'
        stoutput = sste_common.exec_commands(module_args, script_args)
        if stoutput.count('harddisk:/showtech/'):
            stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
            showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
            showtech_list.append(showtech_dict)
        log.error('\ncrash may happened, check the Traceback info')
        log.info(coredump_list)
        log.info(showtech_list)
        return True
    return False


def show_tech(script_args):
    global coredump_list, showtech_list
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show tech-support syslog"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
        showtech_list.append(showtech_dict)
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show tech-support bundle"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
        showtech_list.append(showtech_dict)
    log.info(showtech_list)
    return



##@aetest.skip(reason='debug')
class CommonSetup(aetest.CommonSetup):
    global coredump_list, showtech_list, interface_list
    @aetest.subsection
    def establish_connections(self, testscript, testbed, steps, test_data):
        result = True
        step_txt = "Connecting to UUT"

        with steps.start(step_txt) as s:
            try:
                testscript.parameters['timing'] = tree()
                testscript.parameters['script_args'] = tree()
                log.info('##########script_args')
                log.info(testscript.parameters['script_args'])
                if 'connect_via' in test_data:
                    testscript.parameters['script_args']['sste_connect_via'] = test_data['connect_via']
                testscript.parameters['script_args']['uut'] = sste_common._get_connection(
                    testscript.parameters['script_args'], testbed, test_data['UUT'])
                args = {'sste_commands': '[\'show version\']'}
                sste_common.exec_commands(args, testscript.parameters['script_args'])
                sste_common.get_version_info(testscript.parameters['script_args'], testbed)
                # args = {}
                # args['sste_commands'] = ['show running-config | file harddisk:/xr_cli_automation_backup_config']
                # sste_common.exec_commands(args, testscript.parameters['script_args'])

                # args = {}
                # args['sste_commands'] = ['clear context']
                # sste_common.exec_commands(args, testscript.parameters['script_args'])

                # args = {}
                # args['sste_commands'] = ['clear log']
                # sste_common.exec_commands(args, testscript.parameters['script_args'])
                # args = {}
                # args['sste_commands'] = ['dir harddisk:']
                # output = sste_common.exec_commands(args, testscript.parameters['script_args'])
                # if output.count('backup_cli.cfg'):
                #     args = {}
                #     args['sste_commands'] = ['delete harddisk:/backup_cli.cfg']
                #     sste_common.exec_commands(args, testscript.parameters['script_args'])

                # args = {}
                # args['sste_commands'] = ['copy running-config harddisk:/backup_cli.cfg']
                # sste_common.exec_commands(args, testscript.parameters['script_args'])


            except Exception as e:
                log.error(str(e))
                result = False
                self.failed(step_txt + ": Failed")

        log.info('##########test_data')
        log.info(test_data)

        # if 'tgn' in test_data:
        #     step_txt = "Connecting to TGN"
        #     with steps.start(step_txt, continue_=True) as s:
        #         try:
        #             if not sste_tgn.tgn_connect(testscript.parameters['script_args'], testbed, test_data['tgn'],
        #                                         test_data):
        #                 s.failed(step_txt + ": Failed")
        #         except Exception as e:
        #             log.error(str(e))
        #             s.failed(step_txt + ": Failed")

        testscript.parameters['script_args']['testsuitename'] = "TSG_CLI_TEST"
        if 'testsuite' in test_data:
            testscript.parameters['script_args']['testsuitename'] = test_data['testsuite']

        testcase_calss = []
        testcase_data = tree()
        if 'test_list' in test_data:

            for testcasename, data in test_data['test_list'].items():
                if data['testclass'] not in testcase_calss:
                    testcase_class.append(data['testclass'])
                    if data['testclass'] not in testcase_data:
                        testcase_data[data['testclass']] = []
                    testcase_data[data['testclass']].append(testcasename)


 

#@aetest.skip(reason='debug')
class TSG_CLI_TEST(aetest.Testcase):
    global coredump_list, showtech_list, interface_list
    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):    
            log.info(banner("TSG_CLI_TEST"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.router = genietestbed.devices[test_data['UUT']]
            retry = 0
            while retry < 10:
                try:
                    self.router.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')
            self.router.execute('term length 0', timeout = 300)
            self.router.execute('term width 0', timeout = 300)
            output = self.router.execute('show version', timeout = 300)

            # Split the output into lines
            lines = output.strip().split('\n')


            # Initialize variables to capture platform and version
            platform = None
            version = None

            # Iterate over each line
            for line in lines:
                # Strip any leading or trailing whitespace
                line = line.strip()
                # Check if the line starts with "Version"
                if line.startswith('Version'):
                    # Split the line by colon (:) to get the version information
                    version_info = line.split(':')
                    # Get the version number part and strip any leading or trailing whitespace
                    version = version_info[1].strip()
                # Check if the line contains "Cisco" and "Software"
                elif ("Cisco" in line and "Chassis" in line) or ("cisco" in line and "processor" in line):
                    # Split the line by comma (,) to get platform and version
                    platform_info = line.split()
            
                    # Get the platform name part and strip any leading or trailing whitespace
                    platform = platform_info[1].strip()
            
            # Print the captured platform and version
            log.info(f"Platform:{platform}")
            log.info(f"Version:{version}")

            output = self.router.execute('show run hostname', timeout = 300)
            role = (output.strip().split('hostname'))[-1]
            log.info(f"Role:{role}")



            # Create a list of lists for the table
            table_data = [
                ["Platform", platform],
                ["Version", version],
                ["Role", role]
            ]

            # Create the table using tabulate
            table = tabulate(table_data, headers=["Items", "Value"], tablefmt="grid")
            log.info(table)

            file_path_general = "/scratch/msftcvtauto/TSG_CLI/tsg_cli_general.csv"

            # Writing to CSV
            with open(file_path_general, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(table_data)


            cli_str = os.getenv('cli')
            time_diff_list = []
            
            # Check if the 'cli' environment variable was set
            if cli_str:
                log.info(f"CLI commands as string: {cli_str}")
            
                # Safely evaluate the string as a Python literal (list)
                try:
                    cli_commands = ast.literal_eval(cli_str)
                    if isinstance(cli_commands, list):
                        log.info(f"CLI commands as list: {cli_commands}")
                        for cli_command in cli_commands:
                            output = self.router.execute(cli_command, timeout=7200)
                            log.info(f"Executed command: {cli_command}")
            
                            # Split the lines of output and get the first line
                            lines = output.strip().split('\n')
                            line1 = lines[0] if lines else ''
                            
                            # Remove the date and timezone information
                            timestamp1 = line1.split(' ')[-2]  # Extract the time part
            
                            output_show_clock = self.router.execute('show clock', timeout=300)
                            lines = output_show_clock.strip().split('\n')
                            timestamp_line = lines[0] if lines else ''
                            timestamp2 = timestamp_line.split(' ')[-2] if timestamp_line else ''
            
                            format_str = "%H:%M:%S.%f"
                            time1 = datetime.strptime(timestamp1, format_str)
                            time2 = datetime.strptime(timestamp2, format_str)
                            time_diff = time2 - time1
                            
                            # Convert time_diff to total seconds including microseconds
                            time_diff_seconds = time_diff.total_seconds()
                            time_diff_list.append(time_diff_seconds)
            
                            log.info(f"Time difference for command '{cli_command}': {time_diff_seconds} seconds")
            
                    else:
                        log.error("The 'cli' environment variable is not a list")
                except (ValueError, SyntaxError) as e:
                    log.error(f"Error evaluating 'cli' as a list: {e}")
            else:
                log.error("The 'cli' environment variable is not set")
            
            # After the loop, log the list of all time_diff values in seconds
            log.info(f"All time differences in seconds: {time_diff_list}")


            # Create the table using tabulate
            cli_time_pairs = list(zip(cli_commands, time_diff_list))
            tsg_table = tabulate(cli_time_pairs, headers=['CLI Command', 'Time Difference (s)'], tablefmt='grid')
            

            log.info(table)
            # Print the table
            log.info(tsg_table)

            output = self.router.execute('show run hostname', timeout=7200)
            hostname = output.split()[-1]
            log.info(f"hostname: {hostname}")
            

            # output = self.router.execute('show version', timeout = 300)

            # # Split the output into lines
            # lines = output.strip().split('\n')

            # version = None

            # # Iterate over each line
            # for line in lines:
            #     # Strip any leading or trailing whitespace
            #     line = line.strip()
            #     # Check if the line starts with "Version"
            #     if line.startswith('Version'):
            #         # Split the line by colon (:) to get the version information
            #         version_info = line.split(':')
            #         # Get the version number part and strip any leading or trailing whitespace
            #         version = version_info[1].strip()
            
            # Print the captured version
            log.info(f"Version:{version}")


            output = self.router.execute('show clock', timeout=7200)
            time = output.split()[-3:]
            formatted_time = ''.join(time)
            log.info(f"Time: {formatted_time}")

            # Construct the filename based on variables
            file_name = f"{hostname}_{version}_{formatted_time}_tsg_cli.csv"


            #########Connecting to MSFT_PYATS_SERVER###########
            log.info(banner("Connecting to MSFT_PYATS_SERVER"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['ucs-msft-2']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    show_tech(script_args)
                    self.failed('can not connect to controller sucessfully')

            output = self.controller.execute('cd /scratch/msftcvtauto/TSG_CLI/', timeout = 300)
            output = self.controller.execute(f"touch {file_name}", timeout=300)

            output = self.controller.execute(f"chmod 777 {file_name}", timeout=300)
            self.controller.disconnect()

            #file_path_tsg_cli_time = "/scratch/msftcvtauto/TSG_CLI/tsg_cli_time.csv"
            file_path_tsg_cli_time = f"/scratch/msftcvtauto/TSG_CLI/{file_name}"

            # Writing to CSV
            with open(file_path_tsg_cli_time, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Write the headers first
                writer.writerow(['CLI', 'Time(sec)'])
                writer.writerows(cli_time_pairs)

            if msft_tsg_pattern.check_context_syslog(self.router):
                self.failed('crash happened\n')




class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def upload_log(self):
        pass

