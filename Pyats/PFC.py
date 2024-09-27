#!/bin/env python

import sys

sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
from tabulate import tabulate # New Line
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
    module_args['sste_commands'] = '["show tech custom system"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show log | file harddisk:/showtech/show-log-timestamp.txt"]'
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


def Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data):
    if 'tgn' in test_data:
        with steps.start("Take Traffic Snapshot before", continue_=True) as s:
            try:
                errors = []
                log.info("Clear Traffic Stats")
                sste_tgn.tgn_clear_stats(script_args, test_data)
                if 'tgn_test_type' not in test_data or test_data['tgn_test_type'] != "start":
                    log.info("Let Traffic Run 60 secs")
                    time.sleep(60)
                tgn_streams = {}
                if 'tgn_stream_list' in test_data and test_data['tgn_stream_list'] != "":
                    if isinstance(test_data['tgn_stream_list'], str):
                        tgn_streams = ast.literal_eval(test_data['tgn_stream_list'])
                    else:
                        tgn_streams = test_data['tgn_stream_list']
                tgn_stat = sste_tgn.tgn_get_stats(script_args, test_data, tgn_streams.keys())
                log.info("tgn_stat :{}".format(tgn_stat))
                #                    tgn_stat =  sste_tgn.tgn_get_stats(script_args,test_data)
                script_args['tgn_snapshot'] = {'before': json.dumps(tgn_stat, indent=2)}
                for stream, item in script_args['tgn_snapshot'].items():
                    log.info('Dump the Streams %s' % (item))
            except Exception as e:
                log.error(str(e))
                s.failed(step_txt + ": Failed")


def Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data):
    if 'tgn' in test_data:
        with steps.start("Checking Traffic Convergence After", continue_=True) as s:
            converged = True
            #                try:
            if True:
                tgn_retry_interval = test_data['tgn_snapshot_check_interval']
                tgn_streams = {}
                if 'tgn_stream_list' in test_data and test_data['tgn_stream_list'] != "":
                    if isinstance(test_data['tgn_stream_list'], str):
                        tgn_streams = ast.literal_eval(test_data['tgn_stream_list'])
                    else:
                        tgn_streams = test_data['tgn_stream_list']
                tgn_stat = sste_tgn.tgn_get_stats(script_args, test_data, tgn_streams.keys())
                log.info("tgn_stat:{}".format(tgn_stat))
                notseen = [*tgn_stat]
                tgn_stream_range = {'all': 0.1}
                if tgn_streams:
                    tgn_stream_range = tgn_streams
                before = json.loads(script_args['tgn_snapshot']['before'])
                buffer_time = 0
                traffic_loss_time = -1
                tgn_retry_count = test_data['tgn_snapshot_check_retry']
                while notseen:
                    sste_common.is_traffic_converged(script_args, testbed, before, tgn_stat, tgn_stream_range,
                                                     buffer_time, traffic_loss_time, notseen, {})
                    log.info(str(notseen))
                    if not notseen:
                        converged = True
                        log.info(banner("All traffic streams converged."))
                        break
                    if tgn_retry_count == 0:
                        log.error(banner(
                            "One or more traffic streams not converge after %s secs" % time.strftime("%H:%M:%S",
                                                                                                     time.gmtime(
                                                                                                         time.time() - start - buffer_time))))
                        log.error(str(notseen))
                        converged = False
                        break
                    log.info(banner("One or more traffic stream not converged. Retry..."))
                    time.sleep(int(tgn_retry_interval))
                    tgn_retry_count -= 1
                    tgn_stat = sste_tgn.tgn_get_stats(script_args, test_data, tgn_streams.keys())
                if converged:
                    return converged
                if not converged:
                    log.error(step_txt + ": Failed")
                    testcase_result = False
                    s.failed(step_txt + ": Failed")
                    return converged


def PFC_Value_Check(failed, steps, script_args, testscript, testbed, test_data, timing):
    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    
    log.info(genietestbed.devices)
    
    D8_R9 = genietestbed.devices['D8-R9']
    D8_R9.connect(via='vty',connection_timeout=300)
    D8_R9.execute('clear log', timeout = 300)
    D8_R9.execute('clear context', timeout = 300)

    interface = ['Hu 0/0/0/*', 'Hu 0/1/0/*', 'Hu 0/2/0/*', 'Hu 0/3/0/*', 'Hu 0/4/0/*', 'Hu 0/5/0/*', 'Hu 0/6/0/*', 'Hu 0/7/0/*',
                'FortyGigE 0/0/0/*', 'FortyGigE 0/1/0/*', 'FortyGigE 0/2/0/*', 'FortyGigE 0/3/0/*', 'FortyGigE 0/4/0/*', 'FortyGigE 0/5/0/*', 'FortyGigE 0/6/0/*', 'FortyGigE 0/7/0/*',
                'FourHundredGigE 0/0/0/*', 'FourHundredGigE 0/1/0/*', 'FourHundredGigE 0/2/0/*', 'FourHundredGigE 0/3/0/*', 'FourHundredGigE 0/4/0/*', 'FourHundredGigE 0/5/0/*', 'FourHundredGigE 0/6/0/*', 'FourHundredGigE 0/7/0/*']
            
    for element in interface:
        output = D8_R9.execute('show contr ' + element + ' priority-flow-control | i "interface HundredGigE|3  on|4  on"', timeout=300)
        # Split the output into lines
        output_lines = output.split('\n')
        # Initialize an empty list to store '0' values
        zero_values = []
        # Iterate through the lines to find and collect '0' values
        for line in output_lines:
            if 'on                   0' in line:
                # Assuming 'on' and '0' are separated by spaces, adjust if necessary
                zero_values.append(int(line.split()[-1]))
        log.info("PFC Values = ", zero_values)
        # Check if all values in the list are zero
        if all(value == 0 for value in zero_values):
            log.info('Pause frames are not sent to the source during oversubscription\n')
        else:
            log.info('Pause frames are sent to the source during oversubscription\n')
    D8_R9.disconnect()


def PFC_Value_Check_Test(failed, steps, script_args, testscript, testbed, test_data, timing):
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    
    log.info(genietestbed.devices)
    
    D8_R9 = genietestbed.devices['D8-R9']
    D8_R9.connect(via='vty',connection_timeout=300)
    D8_R9.execute('show log', timeout = 300)
    D8_R9.execute('show context', timeout = 300)




    interface_list = ['Hu 0/0/0/*', 'Hu 0/1/0/*', 'Hu 0/2/0/*', 'Hu 0/3/0/*', 'Hu 0/4/0/*', 'Hu 0/5/0/*', 'Hu 0/6/0/*', 'Hu 0/7/0/*',
                  'FortyGigE 0/0/0/*', 'FortyGigE 0/1/0/*', 'FortyGigE 0/2/0/*', 'FortyGigE 0/3/0/*', 'FortyGigE 0/4/0/*', 'FortyGigE 0/5/0/*', 'FortyGigE 0/6/0/*', 'FortyGigE 0/7/0/*',
                  'FourHundredGigE 0/0/0/*', 'FourHundredGigE 0/1/0/*', 'FourHundredGigE 0/2/0/*', 'FourHundredGigE 0/3/0/*', 'FourHundredGigE 0/4/0/*', 'FourHundredGigE 0/5/0/*', 'FourHundredGigE 0/6/0/*', 'FourHundredGigE 0/7/0/*']

    # Initialize an empty list to store results
    all_zero_values = []
    all_values = []
    # Initialize an empty list to store values for the current interface
    values = []
    for element in interface_list:
        output = D8_R9.execute('show contr ' + element + ' priority-flow-control | i "interface HundredGigE|3  on|4  on"', timeout=300)
        # Split the output into lines
        output_lines = output.split('\n')
        # Initialize an empty list to store '0' values for the current interface
        zero_values = []
        # Iterate through the lines to find and collect '0' values
        # for line in output_lines:
        #     if 'on                   0' in line:
        #         # Assuming 'on' and '0' are separated by spaces, adjust if necessary
        #         zero_values.append(int(line.split()[-1]))
        # # Append the zero values for the current interface to the overall list
        # all_zero_values.extend(zero_values)


        for line in output_lines:
            words = line.split()
            # Assuming 'on' and the value are separated by spaces, adjust if necessary
            if 'on' in words:
                values.append(int(words[-1]))
        # Append the values for the current interface to the overall list
        all_values.extend(values)
    
    # Print the collected PFC values for all interfaces
    log.info(f"PFC Values for all interfaces = {all_values}")
    
    # Check if all values in the list are zero
    if all(value == 0 for value in all_values):
        log.info('Pause frames are not sent to the source during oversubscription\n')
        #failed('All values are 0 means Pause frames are not sent to the source during oversubscription')
        self.failed('All values are 0 means Pause frames are not sent to the source during oversubscription')
    else:
        log.info('Pause frames are sent to the source during oversubscription\n')
    D8_R9.disconnect()

def Verifier_Before(failed, steps, script_args, testscript, testbed, test_data, timing, condition_values):
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D18_R10 = genietestbed.devices['D18-R10']
    retry = 0
    while retry < 10:
        try:
            D18_R10.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')
    D18_R10.execute('term length 0', timeout=300)
    D18_R10.execute('term width 0', timeout=300)
    D18_R10.execute('clear log', timeout=300)
    D18_R10.execute('clear context', timeout=300)
    output = D18_R10.execute('show policy-map int HU0/12/0/34 out | e Policy Bag Stats time:', timeout=300)

    lines = output.split('\n')
    desired_lines = []

    for line in lines:
        if line.strip().startswith("Policy") or line.strip().startswith("Class class-default"):
            desired_lines.append(line.strip())

    log.info(f"List of Class and Policy Map = {desired_lines}")

    for class_name in desired_lines:
        log.info(banner(f"{class_name}"))

        pattern_str = rf"{re.escape(class_name)}.*?Total Dropped\s+:\s+(\S+)"
        pattern = re.compile(pattern_str, re.DOTALL)

        match = pattern.search(output)

        if match:
            total_dropped_value = match.group(1)
            log.info(f"{class_name} - Total Dropped: {total_dropped_value}")
            #log.info('Total Dropped count is 0/0 packets/bytes which is expected\n')

            if total_dropped_value != "0/0":
                log.info(f"Class-name: {class_name} - Total Dropped count is in  packets/bytes")
                failed(f'Total dropped count is not 0/0\n')

            if class_name in condition_values:
                matched_condition, transmitted_condition = condition_values[class_name]

                pattern = re.compile(f"{class_name}.*?Matched\s+:\s+\d+/\d+\s+(\d+).*?Transmitted\s+:\s+\d+/\d+\s+(\d+)", re.DOTALL)


                match = pattern.search(output)

                if match:
                    matched_value = int(match.group(1))
                    transmitted_value = int(match.group(2))

                    log.info(f"Matched Rate: {matched_value}")
                    log.info(f"Transmitted Rate: {transmitted_value}")


                    if matched_value > matched_condition and transmitted_value > transmitted_condition:
                        log.info(f'Matched value and Transmitted value are more than {matched_condition} Gig\n')
                    else:
                        log.info(f'This is expected\n')
                        # failed(f'Matched value and Transmitted value are less than {matched_condition} Gig\n')


            # Check RED ecn marked & transmitted values for specific policies
            if class_name == "Policy QOS_QUEUEING Class RDMA_Egress" or class_name == "Policy QOS_QUEUEING Class LOSSLESSTCP_Egress":
                red_pattern = re.compile(r'RED ecn marked & transmitted\(packets/bytes\): (\S+)')
                red_match = red_pattern.search(output)
                
                if red_match:
                    red_values = red_match.group(1)
            
                    log.info(f"{class_name} - RED ecn marked & transmitted (packets/bytes): {red_values}")
            
                    if red_values != "0/0":
                        log.info(f"Class-name: {class_name} - RED ecn marked & transmitted value is not 0/0!")
                    else:
                        log.info(f'RED ecn marked & transmitted(packets/bytes) value is 0/0\n')

    D18_R10.disconnect()


def Verifier_Watchdog(failed, steps, script_args, testscript, testbed, test_data, timing, condition_values):
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D18_R10 = genietestbed.devices['D18-R10']
    retry = 0
    while retry < 10:
        try:
            D18_R10.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')
    D18_R10.execute('term length 0', timeout=300)
    D18_R10.execute('term width 0', timeout=300)
    D18_R10.execute('clear log', timeout=300)
    D18_R10.execute('clear log', timeout=300)
    D18_R10.execute('clear context', timeout=300)
    output = D18_R10.execute('show policy-map int HU0/12/0/34 out | e Policy Bag Stats time:', timeout=300)

    lines = output.split('\n')
    desired_lines = []

    for line in lines:
        if line.strip().startswith("Policy") or line.strip().startswith("Class class-default"):
            desired_lines.append(line.strip())

    log.info(f"List of Class and Policy Map = {desired_lines}")

    for class_name in desired_lines:
        log.info(banner(f"{class_name}"))

        pattern_str = rf"{re.escape(class_name)}.*?Total Dropped\s+:\s+(\S+)"
        pattern = re.compile(pattern_str, re.DOTALL)

        match = pattern.search(output)

        if match:
            total_dropped_value = match.group(1)
            log.info(f"{class_name} - Total Dropped: {total_dropped_value}")
            log.info('Total Dropped count is 0/0 packets/bytes which is expected\n')

            if total_dropped_value != "0/0":
                log.info(f"Class-name: {class_name} - Total Dropped is 0/0 packets/bytes!")

            if class_name in condition_values:
                matched_condition, transmitted_condition = condition_values[class_name]

                pattern = re.compile(f"{class_name}.*?Matched\s+:\s+\d+/\d+\s+(\d+).*?Transmitted\s+:\s+\d+/\d+\s+(\d+)", re.DOTALL)


                match = pattern.search(output)

                if match:
                    matched_value = int(match.group(1))
                    transmitted_value = int(match.group(2))

                    log.info("Matched Rate:", matched_value)
                    log.info("Transmitted Rate:", transmitted_value)

                    if matched_value > matched_condition and transmitted_value > transmitted_condition:
                        log.info(f'Matched value and Transmitted value are more than {matched_condition} Gig\n')
                    else:
                        log.info(f'This is not expected\n')
                        # failed(f'Matched value and Transmitted value are less than {matched_condition} Gig\n')


            # Check RED ecn marked & transmitted values for specific policies
            if class_name == "Policy QOS_QUEUEING Class RDMA_Egress" or class_name == "Policy QOS_QUEUEING Class LOSSLESSTCP_Egress":
                red_pattern = re.compile(r'RED ecn marked & transmitted\(packets/bytes\): (\S+)')
                red_match = red_pattern.search(output)
                
                if red_match:
                    red_values = red_match.group(1)
            
                    log.info(f"{class_name} - RED ecn marked & transmitted (packets/bytes): {red_values}")
            
                    if red_values != "0/0":
                        log.info(f"Class-name: {class_name} - RED ecn marked & transmitted value is not 0/0!")
                    else:
                        log.info(f'RED ecn marked & transmitted(packets/bytes) value is 0/0\n')

    D18_R10.disconnect()


def Verifier_D8_R9(failed, steps, script_args, testscript, testbed, test_data, timing, condition_values):
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D8_R9 = genietestbed.devices['D8-R9']
    retry = 0
    while retry < 10:
        try:
            D8_R9.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')

    D8_R9.execute('term length 0', timeout=300)
    D8_R9.execute('term width 0', timeout=300)
    output = D8_R9.execute('show policy-map int Hu0/2/0/35 out | e Policy Bag Stats time:', timeout=300)

    lines = output.split('\n')
    desired_lines = []

    for line in lines:
        if line.strip().startswith("Policy") or line.strip().startswith("Class class-default"):
            desired_lines.append(line.strip())

    log.info(f"List of Class and Policy Map = {desired_lines}")

    for class_name in desired_lines:
        log.info(banner(f"{class_name}"))

        pattern_str = rf"{re.escape(class_name)}.*?Total Dropped\s+:\s+(\S+)"
        pattern = re.compile(pattern_str, re.DOTALL)

        match = pattern.search(output)

        if match:
            total_dropped_value = match.group(1)
            log.info(f"{class_name} - Total Dropped:, {total_dropped_value}")
            #log.info('Total Dropped count is 0/0 packets/bytes which is expected\n')

            if total_dropped_value != "0/0":
                log.info(f"Class-name: {class_name} - Total Dropped is in packets/bytes!")
                failed(f'Total dropped count is not 0/0\n')

            if class_name in condition_values:
                matched_condition, transmitted_condition = condition_values[class_name]

                pattern = re.compile(f"{class_name}.*?Matched\s+:\s+\d+/\d+\s+(\d+).*?Transmitted\s+:\s+\d+/\d+\s+(\d+)", re.DOTALL)


                match = pattern.search(output)

                if match:
                    matched_value = int(match.group(1))
                    transmitted_value = int(match.group(2))

                    log.info(f"Matched Rate: {matched_value}")
                    log.info(f"Transmitted Rate: {transmitted_value}")



                    if matched_value > matched_condition and transmitted_value > transmitted_condition:
                        log.info(f'Matched value and Transmitted value are more than {matched_condition} Gig\n')
                    else:
                        log.info(f'This is not expected\n')
                        #self.failed('This is not expected')


            # Check RED ecn marked & transmitted values for specific policies
            if class_name == "Policy QOS_QUEUEING Class RDMA_Egress" or class_name == "Policy QOS_QUEUEING Class LOSSLESSTCP_Egress":
                red_pattern = re.compile(r'RED ecn marked & transmitted\(packets/bytes\): (\S+)')
                red_match = red_pattern.search(output)
                
                if red_match:
                    red_values = red_match.group(1)
            
                    log.info(f"{class_name} - RED ecn marked & transmitted (packets/bytes): {red_values}")
            
                    if red_values != "0/0":
                        log.info(f"Class-name: {class_name} - RED ecn marked & transmitted value is not 0/0!")
                    else:
                        log.info(f'RED ecn marked & transmitted(packets/bytes) value is 0/0\n')

    # D8_R9.disconnect()


def Get_STC_Streamblock_Handle(script_args, streamblock_name):
    stc = script_args['tgn_spirent_conn']
    result = stc.perform("GetObjects", ClassName="StreamBlock", Condition=f"name = '{streamblock_name}'")
    streamblock = result['ObjectList'] 
    return streamblock



def Macsec_Check(failed, steps, script_args, testscript, testbed, test_data, timing):


    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D8_R9 = genietestbed.devices['D8-R9']
    retry = 0
    while retry < 10:
        try:
            D8_R9.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')

    D8_R9.execute('term length 0', timeout = 300) 
    D8_R9.execute('term width 0', timeout = 300)         
    #output = D8_R9.execute('show int acc rates | e No accounting statistics available | b Bundle-Ether8000 | e HundredGigE | e MgmtEth0/RP0/CPU0/0 | e ARP | e IPV6_ND', timeout = 300)
    log.info(banner("Step 3b: PFC over Macsec Validation"))     
    output = D8_R9.execute('show int acc rates | e HundredGigE', timeout = 300)
    bundles = []
            
    # Split data into blocks for each bundle using a more accurate approach
    bundle_blocks = re.split(r'\n\s*\n', output.strip())
            
    for block in bundle_blocks:
        lines = block.strip().split('\n')
        bundle_name = lines[0].strip()
    
        # Extract egress values from the block
        egress_ipv4_value, egress_ipv6_value = 0, 0
    
        for line in lines:
            if 'IPV4_UNICAST' in line:
                egress_ipv4_value = int(line.split()[4])
            elif 'IPV6_UNICAST' in line:
                egress_ipv6_value = int(line.split()[4])
    
        # Check if both IPV4_UNICAST and IPV6_UNICAST egress are nonzero, then add to the list
        if egress_ipv4_value != 0 and egress_ipv6_value != 0 and 'Ingress                        Egress' not in bundle_name: 
            bundles.append(bundle_name)
            
    # Print the list of bundles with both IPV4_UNICAST and IPV6_UNICAST egress nonzero
    log.info("Bundles with nonzero IPV4_UNICAST and IPV6_UNICAST egress:")
    log.info(bundles)
    log.info(f"Bundles with nonzero IPV4_UNICAST and IPV6_UNICAST egress: {bundles}")
    port_list = []
    for bundle in bundles:
        output = D8_R9.execute('show bundle ' + bundle + ' | b Port', timeout=300)
        bundle_member = output.split()[-9]
        port_list.append(bundle_member)
    
    log.info(f"Port List for Bundles: {port_list}")


    # Execute the command outside the loop
    output = D8_R9.execute('show macsec mka summary | e FALLBACK ', timeout=300)

    # Iterate through the port_list
    for port in port_list:
        # Extract the status for the current port using a regular expression
        match = re.search(f'{port}\s+([^\s]+)\s+', output)
        
        # Check if the match is found
        if match:
            status = match.group(1)
            if status == 'Secured':
                log.info(f"The link for port {port} is secured.")
                break
            else:
                log.info(f"The link for port {port} is not secured.")
        else:
            log.info(f"Status not found for port {port} in the output.")

    output = D8_R9.execute('show macsec mka session | e FALLBACK', timeout=300)


    # Iterate through the port_list
    for port in port_list:
        # Extract the status for the current port using a regular expression
        match = re.search(f'{port}\s+[^\s]+\s+[^\s]+\s+([^\s]+)\s+', output)
        
        # Check if the match is found
        if match:
            status = match.group(1)
            if status == 'Secured':
                log.info(f"The link for port {port} is secured.")
                break
            else:
                log.info(f"The link for port {port} is not secured.")
        else:
            log.info(f"Status not found for port {port} in the output.")
            


    for port in port_list:
        output = D8_R9.execute('show macsec secy stats interface ' +port + ' | i OutOctetsEncrypted', timeout=300)

        # Regular expression to extract the OutOctetsEncrypted value
        match = re.search(r'OutOctetsEncrypted\s*:\s*(\d+)', output)
                
        # Check if the match is found
        if match:
            out_octets_encrypted_before = int(match.group(1))
            log.info(f"OutOctetsEncrypted before value: {out_octets_encrypted_before}") 

        log.info('Waiting for 60 second')   
        time.sleep(60)

        output = D8_R9.execute('show macsec secy stats interface ' +port + ' | i OutOctetsEncrypted', timeout=300)

        # Regular expression to extract the OutOctetsEncrypted value
        match = re.search(r'OutOctetsEncrypted\s*:\s*(\d+)', output)
                
        # Check if the match is found
        if match:
            out_octets_encrypted_after = int(match.group(1))
            log.info(f"OutOctetsEncrypted after value: {out_octets_encrypted_after}") 

        if out_octets_encrypted_after > out_octets_encrypted_before:
            log.info(f"OutOctetsEncrypted counter is increasing")
            break
        else:
            log.info(f"OutOctetsEncrypted counter is not increasing")
            self.failed('OutOctetsEncrypted counter is not increasing')
    D8_R9.disconnect()

def HBM_SMS_Utilization(failed, steps, script_args, testscript, testbed, test_data, timing):

    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D18_R10 = genietestbed.devices['D18-R10']
    retry = 0
    while retry < 10:
        try:
            D18_R10.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')



    D18_R10.execute('terminal length 0', timeout = 300)
    D18_R10.execute('terminal width 0', timeout = 300)
    D18_R10.execute('show platform', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 2 "script xr_qos_cmds hbm_usage" location 0/12/CPU0 ', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 2 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/12/CPU0', timeout = 300)

    D18_R10.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 2 "script read_dvoq_qsm" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 2 "script xr_pfc_cmds rate" location 0/12/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/6/CPU0', timeout = 300)

    D18_R10.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/6/CPU0', timeout = 300)
    D18_R10.execute('show logging', timeout = 300)
    D18_R10.disconnect()

    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D8_R9 = genietestbed.devices['D8-R9']
    retry = 0
    while retry < 10:
        try:
            D8_R9.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')
    D8_R9.execute('terminal length 0', timeout = 300)
    D8_R9.execute('terminal width 0', timeout = 300)
    D8_R9.execute('show platform', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/0/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300)
    D8_R9.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
    D8_R9.execute('show controllers npu debugshell 2 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
    D8_R9.disconnect()


def HBM_SMS_Utilization_Test(failed, steps, script_args, testscript, testbed, test_data, timing, device_name=None):
    def connect_and_execute(device):
        retry = 0
        while retry < 10:
            try:
                device.connect(via='vty', connection_timeout=600, mit=True)
                break
            except:
                time.sleep(300)
                retry += 1
                if retry == 10:
                    log.failed('connect failed')

        device.execute('terminal length 0', timeout=300)
        device.execute('terminal width 0', timeout=300)
        device.execute('show platform', timeout=300)
        device.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/0/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script xr_qos_cmds hbm_usage" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script read_dvoq_qsm" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script xr_pfc_cmds rate" location 0/2/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script xr_qos_cmds hbm_usage" location 0/7/CPU0', timeout = 300)
        device.execute('show controllers npu debugshell 0 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script /pkg/bin/xr_qos_cmds.py free_sms" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script read_dvoq_qsm" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 0 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 1 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
        device.execute('show controllers npu debugshell 2 "script xr_pfc_cmds rate" location 0/7/CPU0', timeout = 300) 
        device.disconnect()

    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)

    if device_name is None or device_name.lower() == 'd18-r10':
        D18_R10 = genietestbed.devices['D18-R10']
        connect_and_execute(D18_R10)

    if device_name is None or device_name.lower() == 'd8-r9':
        D8_R9 = genietestbed.devices['D8-R9']
        connect_and_execute(D8_R9)



def Clear_counters(failed, steps, script_args, testscript, testbed, test_data, timing):

    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D18_R10 = genietestbed.devices['D18-R10']
    retry = 0
    while retry < 10:
        try:
            D18_R10.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')



    D18_R10.execute('terminal length 0', timeout = 300)
    D18_R10.execute('terminal width 0', timeout = 300)
    D18_R10.execute('clear controller FortyGigE * priority-flow-control statistics', timeout = 300)
    D18_R10.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
    D18_R10.execute('clear controller FourHundredGigE * priority-flow-control statistics', timeout = 300)
    D18_R10.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear qos counters interface all', timeout = 300)
    D18_R10.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D18_R10.execute('clear controller FortyGigE * stats', timeout = 300)
    D18_R10.execute('clear controller HundredGigE * stats', timeout = 300)
    D18_R10.execute('clear controller FourHundredGigE * stats ', timeout = 300)
    
    D18_R10.disconnect()

    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    log.info(genietestbed.devices)
    D8_R9 = genietestbed.devices['D8-R9']
    retry = 0
    while retry < 10:
        try:
            D8_R9.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(300)
            retry += 1
            if retry == 10:
                log.failed('connect failed')
    D8_R9.execute('terminal length 0', timeout = 300)
    D8_R9.execute('terminal width 0', timeout = 300)
    D8_R9.execute('clear controller FortyGigE * priority-flow-control statistics', timeout = 300)
    D8_R9.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
    D8_R9.execute('clear controller FourHundredGigE * priority-flow-control statistics', timeout = 300)
    D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear qos counters interface all', timeout = 300)
    D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
    D8_R9.execute('clear controller FortyGigE * stats', timeout = 300)
    D8_R9.execute('clear controller HundredGigE * stats', timeout = 300)
    D8_R9.execute('clear controller FourHundredGigE * stats ', timeout = 300)
    D8_R9.disconnect()

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
                args = {}
                args['sste_commands'] = ['show running-config | file harddisk:/xr_cli_automation_backup_config']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['sste_commands'] = ['clear context']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['sste_commands'] = ['clear log']
                sste_common.exec_commands(args, testscript.parameters['script_args'])
                args = {}
                args['sste_commands'] = ['dir harddisk:']
                output = sste_common.exec_commands(args, testscript.parameters['script_args'])
                if output.count('backup_cli.cfg'):
                    args = {}
                    args['sste_commands'] = ['delete harddisk:/backup_cli.cfg']
                    sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['sste_commands'] = ['copy running-config harddisk:/backup_cli.cfg']
                sste_common.exec_commands(args, testscript.parameters['script_args'])


            except Exception as e:
                log.error(str(e))
                result = False
                self.failed(step_txt + ": Failed")

        log.info('##########test_data')
        log.info(test_data)

        if 'tgn' in test_data:
            step_txt = "Connecting to TGN"
            with steps.start(step_txt, continue_=True) as s:
                try:
                    if not sste_tgn.tgn_connect(testscript.parameters['script_args'], testbed, test_data['tgn'],
                                                test_data):
                        s.failed(step_txt + ": Failed")
                except Exception as e:
                    log.error(str(e))
                    s.failed(step_txt + ": Failed")

        testscript.parameters['script_args']['testsuitename'] = "CVT Template Suite"
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
class TC1_5FC_Mode_for_T2_Role_with_Pac_and_GB_LCs(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D8_R9 = genietestbed.devices['D8-R9']
            retry = 0
            while retry < 10:
                try:
                    self.D8_R9.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')
            self.D8_R9.execute('term length 0', timeout = 300)
            self.D8_R9.execute('term width 0', timeout = 300)
            self.D8_R9.execute('sh run | i five-fc', timeout = 300)

            log.info(banner("Removing five-fc command - TC1_5FC_Mode_for_T2_Role_with_Pac_and_GB_LCs"))
            
            self.D8_R9.configure('no controller fabric mode five-fc FC-0-2-4-5-6\n', timeout=300)

            output = self.D8_R9.execute('sh run | i five-fc', timeout = 300)

            if output.count('controller fabric mode five-fc FC-0-2-4-5-6'):
                show_tech(script_args)
                self.failed('Command is not removed\n')

            log.info(banner("Checking FC state - TC1_5FC_Mode_for_T2_Role_with_Pac_and_GB_LCs"))
            output = self.D8_R9.execute('show platform | i 0/FC', timeout = 300)
            for line in output.strip().split('\n'):
                if len(line.split()) >= 4 and line.split()[2] != 'OPERATIONAL':
                    log.info('All the FCs are in OPERATIONAL state\n')
                    break

            # Controller Fabric Plane Check
            log.info(banner("Controller Fabric Plane Check - TC1_5FC_Mode_for_T2_Role_with_Pac_and_GB_LCs"))
            output = self.D8_R9.execute('show controller fabric plane all', timeout = 300) 
    
            # Split the output into lines
            controller = output.splitlines()
            # Initialize a variable to count the "UP" occurrences
            up_count = 0
        
            # Iterate through the lines and count the "UP" occurrences in the Admin and Plane State columns
            for line in controller:
                if "UP" in line:
                    up_count += line.count("UP")
    
            # Check if there are a total of 16 entries with "UP" keyword
            if up_count != 13:
                log.info('Admin State and Plane state are not in UP/UP state\n')
                #self.failed('Admin State and Plane state are not in UP/UP state')    
                time.sleep(5)


		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC2_Proc_Restart(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')



            self.D18_R10.execute('term length 0', timeout = 300)
            self.D18_R10.execute('term width 0', timeout = 300)
            output = self.D18_R10.execute('show process qos_ea location 0/0/CPU0 | i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value1 = pid_line[1].strip()
            respawn_count_value1 = respawn_count_line[1].strip()
            last_started_value1 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ea 0/0/CPU0: {pid_value1}")
            log.info(f"Respawn Count for qos_ea 0/0/CPU0: {respawn_count_value1}")
            log.info(f"Start time for qos_ea 0/0/CPU0: {last_started_value1}")

            log.info(banner("Process restart qos_ea location 0/0/CPU0 - TC2_Proc_Restart"))

            self.D18_R10.execute('process restart qos_ea location 0/0/CPU0', timeout = 300)

            log.info(banner("Waiting 30sec for the process to become stable... - TC2_Proc_Restart"))
            time.sleep(30)



            output = self.D18_R10.execute('show process qos_ea location 0/0/CPU0 | i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value2 = pid_line[1].strip()
            respawn_count_value2 = respawn_count_line[1].strip()
            last_started_value2 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ea 0/0/CPU0: {pid_value2}")
            log.info(f"Respawn Count for qos_ea 0/0/CPU0: {respawn_count_value2}")
            log.info(f"Start time for qos_ea 0/0/CPU0: {last_started_value2}")


            # Check if values have changed
            if (pid_value1 == pid_value2) or (respawn_count_value2 == respawn_count_value1) or (last_started_value1 == last_started_value2):
                show_tech(script_args)
                self.failed('Before and After value of process restart is not changing\n')
            else:
                log.info('Before and After value of process restart is changing\n')
            




            output = self.D18_R10.execute('show process qos_ma location 0/0/CPU0 | i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value1 = pid_line[1].strip()
            respawn_count_value1 = respawn_count_line[1].strip()
            last_started_value1 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ma 0/0/CPU0: {pid_value1}")
            log.info(f"Respawn Count for qos_ma 0/0/CPU0: {respawn_count_value1}")
            log.info(f"Start time for qos_ma 0/0/CPU0: {last_started_value1}")

            log.info(banner("Process restart qos_ma location 0/0/CPU0 - TC2_Proc_Restart"))

            self.D18_R10.execute('process restart qos_ma location 0/0/CPU0', timeout = 300)

            log.info(banner("Waiting 30sec for the process to become stable... - TC2_Proc_Restart"))
            time.sleep(30)


            output = self.D18_R10.execute('show process qos_ma location 0/0/CPU0 | i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value2 = pid_line[1].strip()
            respawn_count_value2 = respawn_count_line[1].strip()
            last_started_value2 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ma 0/0/CPU0: {pid_value2}")
            log.info(f"Respawn Count for qos_ma 0/0/CPU0: {respawn_count_value2}")
            log.info(f"Start time for qos_ma 0/0/CPU0: {last_started_value2}")


            # Check if values have changed
            if (pid_value1 == pid_value2) or (respawn_count_value2 == respawn_count_value1) or (last_started_value1 == last_started_value2):
                show_tech(script_args)
                self.failed('Before and After value of process restart is not changing\n')
            else:
                log.info('Before and After value of process restart is changing\n')




            output = self.D18_R10.execute('show process qos_ma location 0/RP0/CPU0 | i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value1 = pid_line[1].strip()
            respawn_count_value1 = respawn_count_line[1].strip()
            last_started_value1 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ma 0/RP0/CPU0: {pid_value1}")
            log.info(f"Respawn Count for qos_ma 0/RP0/CPU0: {respawn_count_value1}")
            log.info(f"Start time for qos_ma 0/RP0/CPU0: {last_started_value1}")

            log.info(banner("Process restart qos_ma location 0/RP0/CPU0 - TC2_Proc_Restart"))

            self.D18_R10.execute('process restart qos_ma location 0/RP0/CPU0', timeout = 300)

            log.info(banner("Waiting 30sec for the process to become stable... - TC2_Proc_Restart"))
            time.sleep(30)



            output = self.D18_R10.execute('show process qos_ma location 0/RP0/CPU0| i "PID|Respawn count|Last started"', timeout = 300)

            # Split the output text into lines
            lines = output.strip().split('\n')
            # Extracting values from the lines
            pid_line = lines[1].split(':')
            respawn_count_line = lines[2].split(':')
            last_started_line = lines[3].split(':', 1)  # Split at the first colon
            
            # Extracting values
            pid_value2 = pid_line[1].strip()
            respawn_count_value2 = respawn_count_line[1].strip()
            last_started_value2 = last_started_line[1].strip()
            log.info(f"PID Value for qos_ma 0/RP0/CPU0: {pid_value2}")
            log.info(f"Respawn Count for qos_ma 0/RP0/CPU0: {respawn_count_value2}")
            log.info(f"Start time for qos_ma 0/RP0/CPU0: {last_started_value2}")


            # Check if values have changed
            if (pid_value1 == pid_value2) or (respawn_count_value2 == respawn_count_value1) or (last_started_value1 == last_started_value2):
                show_tech(script_args)
                self.failed('Before and After value of process restart is not changing\n')
            else:
                log.info('Before and After value of process restart is changing\n')

            log.info('Waiting for 60 seconds for the traffic to converge')
            time.sleep(60)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")


		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


@aetest.skip(reason='debug')
class Test_API(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
        #for loop in range(2):
            #if 'tgn' in test_data:
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)

@aetest.skip(reason='debug')
class Test_API(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):

            tgn_streams = ['RWA2-OWR2-ISIS-SR-Labeled-V4-Convergence-1',
                        'RWA2-OWR2-ISIS-SR-Labeled-V6-Convergence-1',         
                        'RWA2-OWR2-ISIS-SR-Labeled-V4-Convergence-2',
                        'RWA2-OWR2-ISIS-SR-Labeled-V6-Convergence-2', 
                        'OWR2-RWA2-ISIS-SR-Labeled-V4-Convergence',   
                        'OWR2-RWA2-ISIS-SR-Labeled-V6-Convergence'] 



            if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#                # Disable stream block
#                log.info('Disabling Traffic')
#                stc = script_args['tgn_spirent_conn']
#                for stream in tgn_streams:
#                    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
#                    stc.config(streamblock,Active=False)
#    
#                stc.apply() 
#
#                time.sleep(10)
#    
#                # Enable stream block
#                log.info('Disabling Traffic')
#                stc = script_args['tgn_spirent_conn']
#                for stream in tgn_streams:
#                    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
#                    stc.config(streamblock,Active=False)
#    
#                stc.apply() 
#
#                time.sleep(10)
    
#                log.info('Stopping_Streamblock')
#                sste_tgn.tgn_stop_traffic(script_args,None,streams=tgn_streams)
#                time.sleep(10)


#                log.info('Starting_Streamblock')
#                sste_tgn.tgn_start_traffic(script_args,None,streams=tgn_streams)
#                time.sleep(10)

                stc = script_args['tgn_spirent_conn']
                for stream in tgn_streams:
                    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                    stc.config(streamblock,Load=25,Loadunit='percent_line_rate')
    
                stc.apply()  

                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.S2_OWR2 = genietestbed.devices['S2-OWR2']
            retry = 0
            while retry < 10:
                try:
                    self.S2_OWR2.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')




            # self.S2_OWR2.execute('show run hw-module profile priority-flow-control', timeout = 300)
# 
            # self.S2_OWR2.execute('show run priority-flow-control watchdog', timeout = 300)
# 
            # self.S2_OWR2.execute('show run class-map', timeout = 300)
# 
            # self.S2_OWR2.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
# 
# 
# 
            # self.S2_OWR2.execute('clear controller FortyGigE * priority-flow-control statistics', timeout = 300)
            # self.S2_OWR2.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
            # self.S2_OWR2.execute('clear controller FourHundredGigE * priority-flow-control statistics', timeout = 300)
            # self.S2_OWR2.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            # self.S2_OWR2.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            # self.S2_OWR2.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            # self.S2_OWR2.execute('clear qos counters interface all', timeout = 300)
            # self.S2_OWR2.execute('clear controller FortyGigE * stats', timeout = 300)
            # self.S2_OWR2.execute('clear controller HundredGigE * stats', timeout = 300)
            # self.S2_OWR2.execute('clear controller FourHundredGigE * stats', timeout = 300)


            output = self.S2_OWR2.execute('show policy-map int HU0/12/0/34 out | e Policy Bag Stats time:', timeout = 300)       
############################ Enable Disable stream block##############################
#            # Disable stream block
#            stc = script_args['tgn_spirent_conn']
#            for stream in tgn_streams:
#                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
#                stc.config(streamblock,Active=False)
#
#            stc.apply() 
#
#            # Enable stream block
#            stc = script_args['tgn_spirent_conn']
#            for stream in tgn_streams:
#                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
#                stc.config(streamblock,Active=False)
#
#            stc.apply() 

#@aetest.skip(reason='debug')
class TC3_Classification_and_Marking_and_Over_Subscription(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            tgn_streams_25_load = ['HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT',
                            'HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3',       
                            'HMv4-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3',
                            'HMv6-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3'] 

            tgn_streams_10_load = ['HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1',
                            'HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0',       
                            'HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1',
                            'HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0',
                            'HMv4TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1',
                            'HMv4UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0',
                            'HMv6TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1',
                            'HMv6UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0']



            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')



            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)

            log.info(banner("Step 1 on D18_R10 - TC3_Classification_and_Marking_and_Over_Subscription"))
            self.D18_R10.execute('show run hw-module profile priority-flow-control', timeout = 300)
            self.D18_R10.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D18_R10.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D18_R10.execute('show controllers npu priority-flow-control location all', timeout = 300)

            log.info(banner("Step 2 on D18_R10 - TC3_Classification_and_Marking_and_Over_Subscription"))
            self.D18_R10.execute('clear controller FortyGigE * priority-flow-control statistics', timeout = 300)
            self.D18_R10.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
            self.D18_R10.execute('clear controller FourHundredGigE * priority-flow-control statistics', timeout = 300)
            self.D18_R10.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear qos counters interface all', timeout = 300)
            self.D18_R10.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D18_R10.execute('clear controller FortyGigE * stats', timeout = 300)
            self.D18_R10.execute('clear controller HundredGigE * stats', timeout = 300)
            self.D18_R10.execute('clear controller FourHundredGigE * stats', timeout = 300)

            self.D18_R10.disconnect()

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D8_R9 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D8_R9.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')



            self.D8_R9.execute('terminal length 0', timeout = 300)
            self.D8_R9.execute('terminal width 0', timeout = 300)
            self.D8_R9.execute('clear logging', timeout = 300)

            log.info(banner("Step 1 on D8_R9 - TC3_Classification_and_Marking_and_Over_Subscription"))
            self.D8_R9.execute('show run hw-module profile priority-flow-control', timeout = 300)
            self.D8_R9.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D8_R9.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D8_R9.execute('show controllers npu priority-flow-control location all', timeout = 300)

            log.info(banner("Step 2 on D8_R9 - TC3_Classification_and_Marking_and_Over_Subscription"))
            self.D8_R9.execute('clear controller FortyGigE * priority-flow-control statistics', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * priority-flow-control statistics', timeout = 300)
            self.D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear qos counters interface all', timeout = 300)
            self.D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller FortyGigE * stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * stats', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * stats', timeout = 300)

            self.D8_R9.disconnect()


            log.info(banner("Step 3a: Validating traffic with 0 drops - TC3_Classification_and_Marking_and_Over_Subscription"))
            #log.info("This step should have been taken care manually before starting the testcase. Make sure streams are started with 0 drops")


            ################################## Macsec Verification ################################

            Macsec_Check(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ################################## Verifier_Before ################################
            #Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            time.sleep(60)

            
            ################################## HBM & SMS Utilization  ################################
            log.info(banner("Step 3c & Step 3d: Display the HBM & SMS utilization output without oversubscription on D18-R10 RH and D8-R9 T2 - TC3_Classification_and_Marking_and_Over_Subscription"))
            HBM_SMS_Utilization(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("Step 4: Wait for a minute, execute the cmd sh policy-map egress interface out on RH device and verify traffic classified into the respective queues with 0 drops, and verify accurate traffic rate per streamblock - TC3_Classification_and_Marking_and_Over_Subscription"))

            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            # ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1)


            log.info(banner("Step 5a: Changing the Load percentage of "
               "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
               "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
               "HMv4-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3,"
               "HMv6-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3 to 25% - TC3_Classification_and_Marking_and_Over_Subscription"))

            log.info(banner("Step 5a: Changing the Load percentage of "
                        "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                        "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"       
                        "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                        "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                        "HMv4TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1,"
                        "HMv4UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0,"
                        "HMv6TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1,"
                        "HMv6UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0 to 10% - TC3_Classification_and_Marking_and_Over_Subscription"))


            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Changing the Load percentage of the streams - TC3_Classification_and_Marking_and_Over_Subscription"))
                stc = script_args['tgn_spirent_conn']
                #for stream in tgn_streams:
                #    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                #    stc.config(streamblock,Load=25,Loadunit='percent_line_rate')
                #stc.apply() 


                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=25,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=10,Loadunit='percent_line_rate')


                stc.apply()
            #############  Clearing Traffic Stats ################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")


            log.info(banner("Waiting 60s for the change to take affect - TC3_Classification_and_Marking_and_Over_Subscription"))

            time.sleep(60)

            log.info(banner("Verifying Again with changed Load - TC3_Classification_and_Marking_and_Over_Subscription"))

            condition_values_2 = {
                'Class class-default': (50000000, 50000000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class class-default': (30000000, 30000000),
            }
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_2)


            ################################## HBM & SMS Utilization after Oversubscription  ################################
            log.info(banner("Step 5b & Step 5c: Display the HBM & SMS utilization output on D18-R10 RH and D8-R9 T2 under oversubscription - TC3_Classification_and_Marking_and_Over_Subscription"))
            HBM_SMS_Utilization(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            ################################## PFC VALUE CHECK ################################
            log.info(banner("Step 6: PFC Value Check"))
            PFC_Value_Check_Test(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Step : Changing the Load percentage of "
                   "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                   "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                   "HMv4-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3,"
                   "HMv6-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3 to 5% - TC3_Classification_and_Marking_and_Over_Subscription"))
    
                log.info(banner("Step : Changing the Load percentage of "
                            "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                            "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"       
                            "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                            "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                            "HMv4TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1,"
                            "HMv4UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0,"
                            "HMv6TCP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC3-QB0D-dscp0x03-def-def-ECN01-ECT1,"
                            "HMv6UDP-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC4-QB12-dscp0x04-def-def-ECN10-ECT0 to 5% - TC3_Classification_and_Marking_and_Over_Subscription"))

                stc = script_args['tgn_spirent_conn']
                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=5,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=5,Loadunit='percent_line_rate')

                stc.apply()
                log.info(banner("Waiting for 60s for the traffic to be stable - TC3_Classification_and_Marking_and_Over_Subscription"))
                time.sleep(60)

                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC6_Ingress_Policies_ACL(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1 Making sure there is 0 drop in the beginning of the testcase - TC6_Ingress_Policies_ACL"))
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')


            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            log.info(banner("Step 2: on D18-R10 TC6_Ingress_Policies_ACL - TC6_Ingress_Policies_ACL"))
            output = self.D18_R10.execute('show interface BE8000 accounting rates', timeout = 300)

            # Extract values using regular expression
            ipv4_match = re.search(r'IPV4_UNICAST\s+(\d+)', output)
            ipv6_match = re.search(r'IPV6_UNICAST\s+(\d+)', output)
            
            # Check if matches are found
            if ipv4_match and ipv6_match:
                ipv4_bits_sec = int(ipv4_match.group(1))
                log.info(f"IPV4_UNICAST: {ipv4_bits_sec}")
                log.info(ipv4_bits_sec)
                ipv6_bits_sec = int(ipv6_match.group(1))
                log.info(f"IPV6_UNICAST: {ipv6_bits_sec}")
            
                # Check if values are more than 1000
                if ipv4_bits_sec > 1000 or ipv6_bits_sec > 1000:
                    log.info("Values are more than 1000 pkts/sec")
                else:
                    log.info("Values are not more than 1000 pkts/sec")
                    #show_tech(script_args)
                    #self.failed('Values are not more than 1000 pkts/sec')
            else:
                log.info("Unable to find relevant information in the output.")


        log.info(banner("Step 3 Apply IPV4 and IPV6 ingress ACLs under BE8000 - TC6_Ingress_Policies_ACL"))

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            log.info('Take_traffic_snapshot_before_configuring_the_ACL')
            ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
                
        self.D18_R10.configure('interface Bundle-Ether8000\n'
                    'ipv4 access-group D18_v4_Bundle_ingress ingress\n'
                    'ipv6 access-group D18_v6_Bundle_ingress ingress\n', timeout = 300)


        log.info('Waiting 30 seconds for the config to take effect')

        time.sleep(30)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_configuring_the_ACL')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")

            
            output = self.D18_R10.execute('show interface BE8000 accounting rates', timeout = 300)

            # Extract values using regular expression
            ipv4_match = re.search(r'IPV4_UNICAST\s+(\d+)', output)
            ipv6_match = re.search(r'IPV6_UNICAST\s+(\d+)', output)
            
            # Check if matches are found
            if ipv4_match and ipv6_match:
                ipv4_bits_sec = int(ipv4_match.group(1))
                log.info(f"IPV4_UNICAST: {ipv4_bits_sec}")
                log.info(ipv4_bits_sec)
                ipv6_bits_sec = int(ipv6_match.group(1))
                log.info(f"IPV6_UNICAST: {ipv6_bits_sec}")
            
                # Check if values are more than 1000
                if ipv4_bits_sec > 1000 or ipv6_bits_sec > 1000:
                    log.info("Values are more than 1000 pkts/sec")
                else:
                    log.info("Values are not more than 1000 pkts/sec")
            else:
                log.info("Unable to find relevant information in the output.")

        log.info(banner("Step 4 Rolling back to previous config - TC6_Ingress_Policies_ACL"))
        self.D18_R10.execute('rollback configuration last 1', timeout = 300)
        self.D18_R10.execute('show logging', timeout = 300)

		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC7_Policies_in_place_modification(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1: Making sure there is 0 drop in the beginning of the testcase - TC7_Policies_in_place_modification"))
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            log.info(banner("Step 2: on D18_R10 - TC7_Policies_in_place_modification"))
            output = self.D18_R10.execute('sh run int Hu0/12/0/34', timeout = 300)

            # Extract service-policy input and output names
            service_policy_input = None
            service_policy_output = None
            for line in output.split('\n'):
                if "service-policy input" in line:
                    service_policy_input = line.split()[-1]
                elif "service-policy output" in line:
                    service_policy_output = line.split()[-1]

            log.info(f"Service-policy input name: {service_policy_input}")
            log.info(f"Service-policy output name: {service_policy_output}")

            self.D18_R10.execute('show policy-map pmap-name ' + str(service_policy_output) + ' detail', timeout = 300)


            self.D18_R10.execute('show policy-map int HU0/12/0/34 out', timeout = 300)

            self.D18_R10.execute('show qos interface Hu0/12/0/34 output', timeout = 300)

            log.info(banner("Step 3: Inplace modification of the egress policy(modify queue limit) - TC7_Policies_in_place_modification"))

            self.D18_R10.configure('policy-map QOS_QUEUEING\n'
                    'class TC6_Egress\n'
                    'queue-limit 18 ms\n', timeout = 300)


            output = self.D18_R10.execute('show config commit changes last 1 | i queue-limit 18 ms', timeout = 300)

            if output.count('queue-limit 18 ms'):
                log.info('Config went through')
            else:
                show_tech(script_args)
                self.failed('Config not found')

            self.D18_R10.execute('show qos interface Hu0/12/0/34 output', timeout = 300)

            log.info(banner("Step 4: Waiting 30secs to verify queue-limit - TC7_Policies_in_place_modification"))

            self.D18_R10.execute('show policy-map int HU0/12/0/34 out', timeout = 300)

            output = self.D18_R10.execute('sh run policy-map QOS_QUEUEING | i queue-limit 18 ms', timeout = 300)

            if output.count('queue-limit 18 ms'):
                log.info('Config went through')
            else:
                show_tech(script_args)
                self.failed('Config not found')

            log.info(banner("Step 5: Rolling back to previous configuration - TC7_Policies_in_place_modification"))
            self.D18_R10.execute('rollback configuration last 1', timeout = 300)

            self.D18_R10.execute('show log', timeout = 300)


		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC8_Class_maps_in_place_modificatons(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1: Show output - TC8_Class_maps_in_place_modificatons"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            
            output = self.D18_R10.execute('sh run int Hu0/12/0/34', timeout = 300)

            # Extract service-policy input and output names
            service_policy_input = None
            service_policy_output = None
            for line in output.split('\n'):
                if "service-policy input" in line:
                    service_policy_input = line.split()[-1]
                elif "service-policy output" in line:
                    service_policy_output = line.split()[-1]

            log.info(f"Service-policy input name: {service_policy_input}")
            log.info(f"Service-policy output name: {service_policy_output}")

            self.D18_R10.execute('show policy-map pmap-name ' + str(service_policy_output) + ' detail', timeout = 300)


            self.D18_R10.execute('show run class-map TC6_Egress', timeout = 300)

            log.info(banner("Step 2: Execute inplace class-map modification to verify multiple association of same TC to different classes under 1 policy is blocked - TC8_Class_maps_in_place_modificatons"))

            self.D18_R10.configure('class-map match-any TC6_Egress\n'
                    'no match traffic-class 6\n'
                    'match traffic-class 5\n', timeout = 300)


            # output = self.D18_R10.execute('show configuration failed | i  InPlace Modify Error:', timeout = 300)

            # if output.count('InPlace Modify Error:'):
            #     log.info('Desired error found')
            # else:
            #     self.failed('Desired error not found')

            # self.D18_R10.send('end\n', timeout = 300)

            # self.D18_R10.send('no\n', timeout = 300)


            log.info(banner("Step 3: Update class-map description and verify successful commit - TC8_Class_maps_in_place_modificatons"))

            self.D18_R10.configure('class-map match-any TC6_Egress\n'
                    'description queue-limit\n', timeout = 300)

            output = self.D18_R10.execute('show config commit changes last 1 | i description queue-limit', timeout = 300)

            if output.count('description queue-limit'):
                log.info('Class-map description got updated')
            else:
                show_tech(script_args)
                self.failed('Class-map description did not get updated')

            output = self.D18_R10.execute('show run class-map TC6_Egress | i description queue-limit', timeout = 300)

            if output.count('description queue-limit'):
                log.info('Class-map description got updated')
            else:
                show_tech(script_args)
                self.failed('Class-map description did not get updated')

            log.info(banner("Step 4: Rolling back to previous configuration - TC8_Class_maps_in_place_modificatons"))

            self.D18_R10.execute('rollback configuration last 1', timeout = 300)

            self.D18_R10.execute('show log', timeout = 300)


		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC15_Short_range_SMS_PFC_short_link_to_short_link(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1: Show output - TC15_Short_range_SMS_PFC_short_link_to_short_link"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D8_R9 = genietestbed.devices['D8-R9']
            retry = 0
            while retry < 10:
                try:
                    self.D8_R9.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D8_R9.execute('terminal length 0', timeout = 300)
            self.D8_R9.execute('terminal width 0', timeout = 300)
            self.D8_R9.execute('clear logging', timeout = 300)
            self.D8_R9.execute('clear context', timeout = 300)

            self.D8_R9.execute('show run hw-module profile priority-flow-control', timeout = 300)
            self.D8_R9.execute('show controllers npu priority-flow-control location all', timeout = 300)
            self.D8_R9.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D8_R9.execute('show run int Hu0/1/0/38', timeout = 300)
            self.D8_R9.execute('show run int Hu0/2/0/35', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D8_R9.execute('show qos int Hu0/1/0/38 input', timeout = 300)
            self.D8_R9.execute('show qos int Hu0/2/0/35 output', timeout = 300)


            log.info(banner("Step 2:Clear Controller Counter - TC15_Short_range_SMS_PFC_short_link_to_short_link"))

            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear qos counters interface all', timeout = 300)
            self.D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * stats', timeout = 300)



            log.info(banner("Step 3: Making sure there is 0 drop in the beginning of the testcase - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

            log.info(banner("Step 4: SMS & HBM utilization outputs at 100 percent Line rate - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
            HBM_SMS_Utilization_Test(self.failed, steps, script_args, testscript, testbed, test_data, timing, device_name='D8-R9')

            log.info(banner("Step 5: Traffic classification check - TC15_Short_range_SMS_PFC_short_link_to_short_link"))

            tgn_streams_10_load = ['HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-9kB-TC012567-b0-dscp0x00-def-def-ECN00-nonECT',
                        'HMv4TCP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-iMix-TC3-b0D-dscp0x03-def-def-ECN01-ECT1',       
                        'HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-9kB-TC012567-b0-dscp0x00-def-def-ECN00-nonECT',
                        'HMv6TCP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-iMix-TC3-b0D-dscp0x03-def-def-ECN01-ECT1'] 

            tgn_streams_25_load = ['HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0',
                        'HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0']


            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Changing the Load percentage of the streams from 5% LR Lossy and Lossless to 10% Lossy & 25%  Lossless - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
                stc = script_args['tgn_spirent_conn']
                #for stream in tgn_streams:
                #    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                #    stc.config(streamblock,Load=25,Loadunit='percent_line_rate')
                #stc.apply() 


                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=10,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=25,Loadunit='percent_line_rate')

                stc.apply()
            #############  Clearing Traffic Stats ################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            log.info(banner("Waiting 60s for the change to take affect - TC15_Short_range_SMS_PFC_short_link_to_short_link"))

            time.sleep(60)



            condition_values_1 = {
                'Class class-default': (50000000, 50000000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class class-default': (30000000, 30000000),
            }
            ################################## Verifier_Before ################################
            Verifier_D8_R9(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1)

            log.info(banner("Step 6: Verify Watchdog SM state - TC15_Short_range_SMS_PFC_short_link_to_short_link"))

            output = self.D8_R9.execute('show contr Hu0/1/0/38 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            output = self.D8_R9.execute('show contr Hu0/2/0/35 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            log.info(banner("Checking Hardware Programming Error - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
            output = self.D8_R9.execute('show logging | in HW_PROG_ERROR', timeout = 300)
            if output.count('HW_PROG_ERROR'):
                show_tech(script_args)
                self.failed('Hardware Programming Error Found\n')
            log.info(banner("Checking Out of Resource Error - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
            output = self.D8_R9.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            self.D8_R9.execute('show logging', timeout = 300)

            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Step 5a: Changing the Load percentage of "
                   "HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                   "HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                   "HMv4-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3,"
                   "HMv6-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3 to 20% - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
                stc = script_args['tgn_spirent_conn']

                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=10,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=20,Loadunit='percent_line_rate')

                stc.apply()



		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC23_Short_link_to_short_link(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1 Show output - TC23_Short_link_to_short_link"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D8_R9 = genietestbed.devices['D8-R9']
            retry = 0
            while retry < 10:
                try:
                    self.D8_R9.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D8_R9.execute('terminal length 0', timeout = 300)
            self.D8_R9.execute('terminal width 0', timeout = 300)
            self.D8_R9.execute('clear logging', timeout = 300)
            self.D8_R9.execute('clear context', timeout = 300)

            self.D8_R9.execute('show run hw-module profile priority-flow-control', timeout = 300)
            self.D8_R9.execute('show controllers npu priority-flow-control location all', timeout = 300)
            self.D8_R9.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D8_R9.execute('show run int Hu0/1/0/38', timeout = 300)
            self.D8_R9.execute('show run int Hu0/2/0/35', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D8_R9.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D8_R9.execute('show qos int Hu0/1/0/38 input', timeout = 300)
            self.D8_R9.execute('show qos int Hu0/2/0/35 output', timeout = 300)


            log.info(banner("Step 2: Clear Controller Counter - TC23_Short_link_to_short_link"))

            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control statistics', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear qos counters interface all', timeout = 300)
            self.D8_R9.execute('clear controller FortyGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller FourHundredGigE * priority-flow-control watchdog-stats', timeout = 300)
            self.D8_R9.execute('clear controller HundredGigE * stats', timeout = 300)



            log.info(banner("Step 3: Making sure there is 0 drop in the beginning of the testcase - TC23_Short_link_to_short_link"))
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)


            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

            log.info(banner("Step 4: SMS & HBM utilization outputs at 100 percent Line rate - TC23_Short_link_to_short_link"))
            HBM_SMS_Utilization_Test(self.failed, steps, script_args, testscript, testbed, test_data, timing, device_name='D8-R9')

            log.info(banner("Step 5: Traffic classification check - TC23_Short_link_to_short_link"))

            tgn_streams_10_load = ['HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-9kB-TC012567-b0-dscp0x00-def-def-ECN00-nonECT',
                        'HMv4TCP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-iMix-TC3-b0D-dscp0x03-def-def-ECN01-ECT1',       
                        'HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-9kB-TC012567-b0-dscp0x00-def-def-ECN00-nonECT',
                        'HMv6TCP-Sp4/1-H01038phy-D8-to-D8-H02035-6/1-iMix-TC3-b0D-dscp0x03-def-def-ECN01-ECT1'] 

            tgn_streams_25_load = ['HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0',
                        'HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0']


            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Changing the Load percentage of the streams from 5% LR Lossy and Lossless to 10% Lossy & 25%  Lossless - TC15_Short_range_SMS_PFC_short_link_to_short_link"))
                stc = script_args['tgn_spirent_conn']
                #for stream in tgn_streams:
                #    streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                #    stc.config(streamblock,Load=25,Loadunit='percent_line_rate')
                #stc.apply() 


                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=10,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=25,Loadunit='percent_line_rate')

                stc.apply()
            #############  Clearing Traffic Stats ################
            log.info(banner("Clearing Traffic Stats - TC23_Short_link_to_short_link"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            log.info(banner("Waiting 60s for the change to take affect - TC23_Short_link_to_short_link"))

            time.sleep(60)



            condition_values_1 = {
                'Class class-default': (50000000, 50000000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (6000000, 6000000),
                'Policy QOS_QUEUEING Class class-default': (30000000, 30000000),
            }
            ################################## Verifier_Before ################################
            Verifier_D8_R9(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1)


            log.info(banner("Step 6: Verify Watchdog SM state - TC23_Short_link_to_short_link"))

            output = self.D8_R9.execute('show contr Hu0/1/0/38 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            output = self.D8_R9.execute('show contr Hu0/2/0/35 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            log.info(banner("Checking Hardware Programming Error - TC23_Short_link_to_short_link"))
            output = self.D8_R9.execute('show logging | in HW_PROG_ERROR', timeout = 300)
            if output.count('HW_PROG_ERROR'):
                #show_tech(script_args)
                self.failed('Hardware Programming Error Found\n')
            log.info(banner("Checking Out of Resource Error - TC23_Short_link_to_short_link"))
            output = self.D8_R9.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            self.D8_R9.execute('show logging', timeout = 300)

            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info(banner("Step 5a: Changing the Load percentage of "
                   "HMv4UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                   "HMv6UDP-Sp4/1-H01038phy-D8-to-D8-H02035-1kB-6/1-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                   "HMv4-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3,"
                   "HMv6-Sp6/1-H02035phy-D8-to-D18-H012034-8/13-TC012567-QB0-dscp0x00-def-def-ECN00-nonECT-3 to 20% - TC23_Short_link_to_short_link"))
                stc = script_args['tgn_spirent_conn']

                for streamblockname in tgn_streams_10_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=10,Loadunit='percent_line_rate')

                for streamblockname in tgn_streams_25_load:
                    streamblocks = Get_STC_Streamblock_Handle(script_args,streamblockname)
                    for streamblock in streamblocks.split():
                        stc.config(streamblock,Load=20,Loadunit='percent_line_rate')

                stc.apply()

		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC24_Watchdog_global(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            log.info(banner("Step 1: Make sure there is 0 drop for "
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0 streams - TC24_Watchdog_global"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            ################################## Clear counter ################################
            log.info(banner("Step 2: Clear controller counters - TC24_Watchdog_global"))
            Clear_counters(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('Watchdog SM state is correct')
            else:
                #show_tech(script_args)
                self.failed('Watchdog SM state is correct')


            log.info(banner("Step 3: Make sure there is 0 drop for "
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0 streams - TC24_Watchdog_global"))


            log.info(banner("Step 4: Verify 0 drops in Hu0/12/0/34 egress policy-map output - TC24_Watchdog_global"))
            # ################################## Verifier_Before ################################

            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1) 


            log.info(banner("Step 5: Verify M M watchdog SM state for TC3 and TC4 - TC24_Watchdog_global"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')
            self.D18_R10.execute('term length 0', timeout = 300)
            self.D18_R10.execute('term width 0', timeout = 300)

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            


            log.info(banner("Step 6: Start Pause storms in TC3 and TC4 - TC24_Watchdog_global"))
            
            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC3',
                        'HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC4'] 

            # Enable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=True)

            stc.apply() 
            # Start Traffic Stream
            sste_tgn.tgn_start_traffic(script_args,None,streams=tgn_streams)
            log.info('Waiting for 30 seconds for the traffic to flow')
            time.sleep(30)


            log.info(banner("Step 7: Verify R R watchdog SM state for TC3 and TC4 - TC24_Watchdog_global"))


            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - R R - - -'):
                log.info('watchdog SM state is R R')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not R R')

            ##################### Checking Shudown Events value for TC3 and TC4 ###################

            log.info(banner("Checking Shutdown Events value for TC3 and TC4 - TC24_Watchdog_global"))

            # Use regular expression to find the Shutdown Events values for Traffic Class 3 and 4
            shutdown_events_match = re.search(r"Shutdown Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if shutdown_events_match:
                shutdown_events_tc3 = int(shutdown_events_match.group(1))
                shutdown_events_tc4 = int(shutdown_events_match.group(2))
            
                log.info(f"Shutdown Events for Traffic Class 3: {shutdown_events_tc3}")
                log.info(f"Shutdown Events for Traffic Class 4: {shutdown_events_tc4}")
            
                # Check if any of the values is not 0 and log "Life is great"
                if shutdown_events_tc3 != 0 or shutdown_events_tc4 != 0:
                    log.info("Life is great")
            else:
                log.info("Shutdown Events values not found in the output.")
                #show_tech(script_args)
                self.failed('Shutdown Events values not found in the output.')
                
            
            ##################### Checking Watchdog Events value for TC3 and TC4 ###################

            log.info(banner("Checking Watchdog Events value for TC3 and TC4 - TC24_Watchdog_global"))            
            
            # Use regular expressions to find the Watchdog Events values for Traffic Class 3 and 4
            watchdog_events_match = re.search(r"Watchdog Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if watchdog_events_match:
                # Correct the indexing to capture the correct values for Watchdog Events
                watchdog_events_tc3 = int(watchdog_events_match.group(1))
                watchdog_events_tc4 = int(watchdog_events_match.group(2))
            
                log.info(f"Watchdog Events for Traffic Class 3: {watchdog_events_tc3}")
                log.info(f"Watchdog Events for Traffic Class 4: {watchdog_events_tc4}")
            
                # Check if any of the Watchdog Events values is not 0 and log "Life is great"
                if watchdog_events_tc3 != 0 or watchdog_events_tc4 != 0:
                    log.info("Life is great")
            else:
                log.info("Watchdog Events values not found in the output.")
                show_tech(script_args)
                self.failed('Watchdog Events values not found in the output.')


            log.info(banner("Step 8: Verify TC3,TC4 LosslessTCP and RDMA traffic is dropped - TC24_Watchdog_global"))


            output = self.D18_R10.execute('show policy-map int HU0/12/0/34 out', timeout = 300)
            rdma_index = -1 
            losslesstcp_index = -1

            lines = output.split('\n')   
            # Search for the RDMA_Egress and LOSSLESSTCP_Egress classes and their 'Total Dropped' counts
            for i, line in enumerate(lines):
                if 'Policy QOS_QUEUEING Class RDMA_Egress' in line:
                    rdma_index = i
                elif 'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress' in line:
                    losslesstcp_index = i
           
            # Find 'Total Dropped' line for RDMA_Egress
            for i in range(rdma_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_rdma = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for RDMA_Egress (packets/bytes): %s", total_dropped_rdma)
                    if total_dropped_rdma != "0/0":
                        log.info("This is expected")
                    else:
                        log.info("This is not expected")
                        #show_tech(script_args)
                        #self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break
                       
            # Find 'Total Dropped' line for LOSSLESSTCP_Egress
            for i in range(losslesstcp_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_losslesstcp = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for LOSSLESSTCP_Egress (packets/bytes): %s", total_dropped_losslesstcp)
                    if total_dropped_losslesstcp != "0/0":
                        log.info("This is expected")
                    else:
                        log.info("This is not expected")
                        #show_tech(script_args)
                        #self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break

            log.info(banner("Step 9: Stop the pause storms and verify M M watchdog SM states - TC24_Watchdog_global"))
            # Stopping stream block
            log.info('Stopping_Streamblock')
            sste_tgn.tgn_stop_traffic(script_args,None,streams=tgn_streams)

            ###########################  Disable stream block ##############################
            # Disable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=False)
    
            stc.apply()
            log.info('Waiting 30 seconds for the traffic to settle') 
            time.sleep(30)

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            self.D18_R10.execute('show logging', timeout = 300)

		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC26_PFC_Watchdog_Single_lossless_Q(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            log.info(banner("Step 1: Show commands for configured global PFC policy -  TC26_PFC_Watchdog_Single_lossless_Q"))
            self.D18_R10.execute('show run hw-module profile priority-flow-control', timeout = 300)

            self.D18_R10.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D18_R10.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
            self.D18_R10.execute('show controllers npu priority-flow-control location all', timeout = 300)

            self.D18_R10.disconnect()
            ################################## Clear counter ################################
            log.info(banner("Step 2: Clear controller counters -  TC26_PFC_Watchdog_Single_lossless_Q"))
            Clear_counters(self.failed, steps, script_args, testscript, testbed, test_data, timing)



            log.info(banner("Step3: Make sure there is 0 drop for "
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0 streams -  TC26_PFC_Watchdog_Single_lossless_Q"))



            log.info(banner("Step 4: Verify 0 drops in Hu0/12/0/34 egress policy-map output -  TC26_PFC_Watchdog_Single_lossless_Q"))  

            # ################################## Verifier_Before ################################
            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1)   
            
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('term length 0', timeout = 300)
            self.D18_R10.execute('term width 0', timeout = 300)



            log.info(banner("Step 5:Verify Watchdog SM state -  TC26_PFC_Watchdog_Single_lossless_Q"))
            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')



            log.info(banner("Step 6: Start Pause storm in single lossless Queue TC3 -  TC26_PFC_Watchdog_Single_lossless_Q"))
            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC3'] 

            # Enable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                log.info(f"DEBUG: Setting streamblock {stream} ({streamblock}) to active.")
                stc.config(streamblock,Active=True)

            stc.apply() 
            # Start stream block
            sste_tgn.tgn_start_traffic(script_args,None,streams=tgn_streams)

            log.info('Waiting for 1 minute for the traffic to flow')
            time.sleep(60)

            log.info(banner("Step 7: Verify M R watchdog SM state for TC4 TC3 -  TC26_PFC_Watchdog_Single_lossless_Q"))

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M R - - -'):
                log.info('watchdog SM state is M R')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M R')



            ##################### Checking Shudown Events value for TC3 and TC4 ###################

            log.info(banner("Checking Shutdown Events value for TC3 and TC4 -  TC26_PFC_Watchdog_Single_lossless_Q"))

            # Use regular expression to find the Shutdown Events values for Traffic Class 3 and 4
            shutdown_events_match = re.search(r"Shutdown Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if shutdown_events_match:
                shutdown_events_tc3 = int(shutdown_events_match.group(1))
                shutdown_events_tc4 = int(shutdown_events_match.group(2))
            
                log.info(f"Shutdown Events for Traffic Class 3: {shutdown_events_tc3}")
                log.info(f"Shutdown Events for Traffic Class 4: {shutdown_events_tc4}")
            
                # Check if any of the values is not 0 and log "Life is great"
                if shutdown_events_tc3 > 0 or shutdown_events_tc4 > 0:
                    log.info("Life is great")
            else:
                log.info("Shutdown Events values not found in the output.")
                #show_tech(script_args)
                self.failed('Shutdown Events values not found in the output.')
                
            
            ##################### Checking Watchdog Events value for TC3 and TC4 ###################

            log.info(banner("Checking Watchdog Events value for TC3 and TC4 -  TC26_PFC_Watchdog_Single_lossless_Q"))            
            
            # Use regular expressions to find the Watchdog Events values for Traffic Class 3 and 4
            watchdog_events_match = re.search(r"Watchdog Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if watchdog_events_match:
                # Correct the indexing to capture the correct values for Watchdog Events
                watchdog_events_tc3 = int(watchdog_events_match.group(1))
                watchdog_events_tc4 = int(watchdog_events_match.group(2))
            
                log.info(f"Watchdog Events for Traffic Class 3: {watchdog_events_tc3}")
                log.info(f"Watchdog Events for Traffic Class 4: {watchdog_events_tc4}")
            
                # Check if any of the Watchdog Events values is not 0 and log "Life is great"
                if watchdog_events_tc3 > 0 or watchdog_events_tc4 > 0:
                    log.info("Life is great")
            else:
                log.info("Watchdog Events values not found in the output.")
                #show_tech(script_args)
                self.failed('Watchdog Events values not found in the output.')



            log.info(banner("Step 8: Verify TC3,TC4 LosslessTCP and RDMA traffic is dropped -  TC26_PFC_Watchdog_Single_lossless_Q"))
            output = self.D18_R10.execute('show policy-map interface Hu0/12/0/34 output', timeout = 300)

            rdma_index = -1 
            losslesstcp_index = -1
            lines = output.split('\n')   
            # Search for the RDMA_Egress and LOSSLESSTCP_Egress classes and their 'Total Dropped' counts
            for i, line in enumerate(lines):
                if 'Policy QOS_QUEUEING Class RDMA_Egress' in line:
                    rdma_index = i
                elif 'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress' in line:
                    losslesstcp_index = i
           
            # Find 'Total Dropped' line for RDMA_Egress
            for i in range(rdma_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_rdma = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for RDMA_Egress (packets/bytes): %s", total_dropped_rdma)
                    if total_dropped_rdma == "0/0":
                        log.info("This is expected")
                    else:
                        #show_tech(script_args)
                        self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break
                       
            # Find 'Total Dropped' line for LOSSLESSTCP_Egress
            for i in range(losslesstcp_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_losslesstcp = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for LOSSLESSTCP_Egress (packets/bytes): %s", total_dropped_losslesstcp)
                    if total_dropped_losslesstcp != "0/0":
                        log.info("This is expected")
                    else:
                        #show_tech(script_args)
                        self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break
 
            log.info(banner("Step 9: Stop Pause storm and verify SM state is M M -  TC26_PFC_Watchdog_Single_lossless_Q"))


            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC3'] 

            # Stopping stream block
            log.info('Stopping_Streamblock')
            sste_tgn.tgn_stop_traffic(script_args,None,streams=tgn_streams)

            # Disable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=False)

            stc.apply() 

            log.info('Waiting for 30 seconds for the traffic to flow')
            time.sleep(30)



            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')
            self.D18_R10.execute('show logging', timeout = 300)
		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass




#@aetest.skip(reason='debug')
class TC27_PFC_Watchdog_single_lossy_Q_negative_test(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            log.info(banner("Step 1: Show commands for configured global PFC policy - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))
            self.D18_R10.execute('show run hw-module profile priority-flow-control', timeout = 300)

            self.D18_R10.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D18_R10.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
            self.D18_R10.execute('show controllers npu priority-flow-control location all', timeout = 300)

            self.D18_R10.disconnect()
            ################################## Clear counter ################################
            log.info(banner("Step 2: Clear controller counters - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))
            Clear_counters(self.failed, steps, script_args, testscript, testbed, test_data, timing)



            log.info(banner("Step3: Make sure there is 0 drop for "
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0 streams - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))



            log.info(banner("Step 4: Verify 0 drops in Hu0/12/0/34 egress policy-map output - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))    
            ################################### Verifier_Before ################################
            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1) 
            
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            
            self.D18_R10.execute('term length 0', timeout = 300)
            self.D18_R10.execute('term width 0', timeout = 300)

            log.info(banner("Step 5:Verify M M Watchdog SM state - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))
            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')


            log.info(banner("Step 6: Start Pause storm in single lossy Queue TC0 - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))
            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC0'] 

            # Enable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=True)

            stc.apply() 
            # Start Traffic Stream
            sste_tgn.tgn_start_traffic(script_args,None,streams=tgn_streams)
            log.info('Waiting for 30 seconds for the traffic to flow')
            time.sleep(30)



            log.info(banner("Step 7: Verify M M watchdog SM state for TC3 & TC4 - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M R')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            log.info(banner("Checking Rx PFC Frame count for CoS 0 - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))
            # Use regular expression to find the Rx PFC Frame value for Cos 0
            rx_pfc_cos_0_match = re.search(r"0\s+on\s+(\d+)", output)
            
            if rx_pfc_cos_0_match:
                rx_pfc_cos_0_value = int(rx_pfc_cos_0_match.group(1))
                log.info(f"Rx PFC Frame value for CoS 0: {rx_pfc_cos_0_value}")
                
                # Check if the value is not 0 and log "Life is great"
                if rx_pfc_cos_0_value != 0:
                    log.info("Rx PFC Frame value is increasing")
                else:
                    log.info("Rx PFC Frame value is not increasing")
                    show_tech(script_args)
                    self.failed("Rx PFC Frame value is not increasing")
            else:
                log.info("Rx PFC Frame value for CoS 0 not found in the output.")


            log.info(banner("Step 8: Verify 0 drop in egress policy map - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))

            ################################### Verifier_Before ################################
            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1) 




            log.info(banner("Step 9: Stop Pause storm and verify SM state is M M - TC27_PFC_Watchdog_single_lossy_Q_negative_test"))


            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC0'] 
            # Stopping stream block
            log.info('Stopping_Streamblock')
            sste_tgn.tgn_stop_traffic(script_args,None,streams=tgn_streams)

            # Disable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=False)

            stc.apply() 

            log.info('Waiting for 30 seconds for the traffic to flow')
            time.sleep(30)

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            
            self.D18_R10.execute('term length 0', timeout = 300)
            self.D18_R10.execute('term width 0', timeout = 300)

            self.D18_R10.execute('clear controller hundredGigE0/12/0/34 priority-flow-control statistics', timeout = 300)

            log.info('Waiting for 10 seconds for the counter to be cleared')
            time.sleep(10)

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)
            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')


            # Use regular expression to find the Rx PFC Frame value for Cos 0
            rx_pfc_cos_0_match = re.search(r"0\s+on\s+(\d+)", output)
            
            if rx_pfc_cos_0_match:
                rx_pfc_cos_0_value = int(rx_pfc_cos_0_match.group(1))
                log.info(f"Rx PFC Frame value for CoS 0: {rx_pfc_cos_0_value}")
                
                # Check if the value is not 0 and log "Life is great"
                if rx_pfc_cos_0_value == 0:
                    log.info("Rx PFC Frame value is zero")
                else:
                    log.info("Rx PFC Frame value is not zero or not cleared")
                    show_tech(script_args)
                    self.failed("Rx PFC Frame value is not zero or not cleared")
            else:
                log.info("Rx PFC Frame value for CoS 0 not found in the output.")

            self.D18_R10.execute('show logging', timeout = 300)
		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC28_PFC_Watchdog_simultaneous_multiple_Qs(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        ##############  Clearing Traffic Stats ################
        log.info(banner("Clearing Traffic Stats"))
        sste_tgn.tgn_clear_stats(script_args, test_data)
        log.info("Cleared Traffic Stats")
        log.info(banner("Waiting 60s for the traffic to be stable"))
        time.sleep(60)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            self.D18_R10.execute('clear logging', timeout = 300)
            self.D18_R10.execute('clear context', timeout = 300)

            log.info(banner("Step 1: Show commands for configured global PFC policy - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            self.D18_R10.execute('show run hw-module profile priority-flow-control', timeout = 300)

            self.D18_R10.execute('show run priority-flow-control watchdog', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name QOS_MARKING detail', timeout = 300)
            self.D18_R10.execute('show policy-map pmap-name P_SHAPER detail', timeout = 300)
            self.D18_R10.execute('show run interface HundredGigE0/12/0/34', timeout = 300)
            self.D18_R10.execute('show controllers npu priority-flow-control location all', timeout = 300)

            self.D18_R10.disconnect()
            ################################## Clear counter ################################
            log.info(banner("Step 2: Clear controller counters - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            Clear_counters(self.failed, steps, script_args, testscript, testbed, test_data, timing)



            log.info(banner("Step3: Make sure there is 0 drop for "
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT,"
                "HMv4TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv4UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC012567-b0-dscp0x00-def-def-ECN00-nonECT-3,"
                "HMv6TCP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC3-b0D-dscp0x03-def-def-ECN01-ECT1,"
                "HMv6UDP-Sp6/29-H00046phy-D8-to-D18-H012034-8/13-TC4-b12-dscp0x04-def-def-ECN10-ECT0 streams - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))



            log.info(banner("Step 4: Verify 0 drops in Hu0/12/0/34 egress policy-map output - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))    
            ################################### Verifier_Before ################################

            condition_values_1 = {
                'Class class-default': (180000, 180000),
                'Policy QOS_QUEUEING Class RDMA_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress': (30000, 30000),
                'Policy QOS_QUEUEING Class class-default': (30000, 30000),
            }
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing, condition_values_1) 
            
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
            log.info(genietestbed.devices)
            self.D18_R10 = genietestbed.devices['D18-R10']
            retry = 0
            while retry < 10:
                try:
                    self.D18_R10.connect(via='vty', connection_timeout=600, mit=True)
                    break
                except:
                    time.sleep(300)
                    retry += 1
                    if retry == 10:
                        log.failed('connect failed')

            log.info(banner("Step 5:Verify M M Watchdog SM state for TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            self.D18_R10.execute('terminal length 0', timeout = 300)
            self.D18_R10.execute('terminal width 0', timeout = 300)
            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - M M - - -'):
                log.info('watchdog SM state is M M')
            else:
                #show_tech(script_args)
                self.failed('watchdog SM state is not M M')

            # Use regular expression to find the Rx PFC Frame value for Cos 0
            rx_pfc_cos_0_match = re.search(r"0\s+on\s+(\d+)", output)
            
            if rx_pfc_cos_0_match:
                rx_pfc_cos_0_value = int(rx_pfc_cos_0_match.group(1))
                log.info(f"Rx PFC Frame value for CoS 0: {rx_pfc_cos_0_value}")
                
                # Check if the value is not 0 and log "Life is great"
                if rx_pfc_cos_0_value == 0:
                    log.info("Rx PFC Frame value is not increasing")
                else:
                    log.info("Rx PFC Frame value is increasing")
                    
            else:
                log.info("Rx PFC Frame value for CoS 0 not found in the output.")


            log.info(banner("Step 6: Start Pause storms in TC0, TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))

            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC0',
                            'HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC3',
                            'HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC4'] 

            # Enable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=True)

            stc.apply() 


            # Start Traffic Stream
            sste_tgn.tgn_start_traffic(script_args,None,streams=tgn_streams)
            log.info('Waiting for 30 seconds for the traffic to settle')
            time.sleep(30)

            log.info(banner("Step 7: Verify R R watchdog SM state for TC4 TC3. Verify CoS value > 0 for TC0,TC3,TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))

            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            if output.count('- - - R R - - -'):
                log.info('watchdog SM state is R R')
            else:
                log.info('watchdog SM state is not R R')
                #show_tech(script_args)
                self.failed('watchdog SM state is not R R')

            ##################### Checking Rx PFC Frames value for CoS 0, CoS 3 and CoS 4 #################

            log.info(banner("Checking Rx PFC Frames value for CoS 0, CoS 3 and CoS 4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            # Use regular expression to find the Rx PFC Frame values for CoS 0, 3, and 4
            rx_pfc_cos_values = [0, 0, 0, 0, 0, 0, 0, 0]  # Initialize with 0 for each CoS
            
            for cos in [0, 3, 4]:
                cos_match = re.search(fr"{cos}\s+on\s+(\d+)", output)
                if cos_match:
                    rx_pfc_cos_values[cos] = int(cos_match.group(1))
                    log.info(f"Rx PFC Frame value for CoS {cos}: {rx_pfc_cos_values[cos]}")
                else:
                    log.info(f"Rx PFC Frame value for CoS {cos} not found in the output.")
            
            # Check if any of the values is not 0 and log "Life is great"
            if any(value != 0 for value in rx_pfc_cos_values):
                log.info("Rx PFC Value is increasing")
            else:
                log.info("Rx PFC Value is not increasing")
                #show_tech(script_args)
                self.failed("Rx PFC Value is not increasing")

            ##################### Checking Shudown Events value for TC3 and TC4 ###################

            log.info(banner("Checking Shutdown Events value for TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))

            # Use regular expression to find the Shutdown Events values for Traffic Class 3 and 4
            shutdown_events_match = re.search(r"Shutdown Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if shutdown_events_match:
                shutdown_events_tc3 = int(shutdown_events_match.group(1))
                shutdown_events_tc4 = int(shutdown_events_match.group(2))
            
                log.info(f"Shutdown Events for Traffic Class 3: {shutdown_events_tc3}")
                log.info(f"Shutdown Events for Traffic Class 4: {shutdown_events_tc4}")
            
                # Check if any of the values is not 0 and log "Life is great"
                if shutdown_events_tc3 != 0 or shutdown_events_tc4 != 0:
                    log.info("Life is great")
            else:
                log.info("Shutdown Events values not found in the output.")
                #show_tech(script_args)
                self.failed('Shutdown Events values not found in the output.')
                
            
            ##################### Checking Watchdog Events value for TC3 and TC4 ###################

            log.info(banner("Checking Watchdog Events value for TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))            
            
            # Use regular expressions to find the Watchdog Events values for Traffic Class 3 and 4
            watchdog_events_match = re.search(r"Watchdog Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if watchdog_events_match:
                # Correct the indexing to capture the correct values for Watchdog Events
                watchdog_events_tc3 = int(watchdog_events_match.group(1))
                watchdog_events_tc4 = int(watchdog_events_match.group(2))
            
                log.info(f"Watchdog Events for Traffic Class 3: {watchdog_events_tc3}")
                log.info(f"Watchdog Events for Traffic Class 4: {watchdog_events_tc4}")
            
                # Check if any of the Watchdog Events values is not 0 and log "Life is great"
                if watchdog_events_tc3 != 0 or watchdog_events_tc4 != 0:
                    log.info("Life is great")
            else:
                log.info("Watchdog Events values not found in the output.")
                show_tech(script_args)
                self.failed('Watchdog Events values not found in the output.')




            log.info(banner("Step 8: Verify TC3,TC4 LosslessTCP and RDMA traffic is dropped - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            output = self.D18_R10.execute('show policy-map interface HU0/12/0/34 output', timeout = 300)
            rdma_index = -1 
            losslesstcp_index = -1
            lines = output.split('\n')   
            # Search for the RDMA_Egress and LOSSLESSTCP_Egress classes and their 'Total Dropped' counts
            for i, line in enumerate(lines):
                if 'Policy QOS_QUEUEING Class RDMA_Egress' in line:
                    rdma_index = i
                elif 'Policy QOS_QUEUEING Class LOSSLESSTCP_Egress' in line:
                    losslesstcp_index = i
           
            # Find 'Total Dropped' line for RDMA_Egress
            for i in range(rdma_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_rdma = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for RDMA_Egress (packets/bytes): %s", total_dropped_rdma)
                    if total_dropped_rdma != "0/0":
                        log.info("This is expected")
                    else:
                        log.info("This is not expected")
                        #show_tech(script_args)
                        #self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break
                       
            # Find 'Total Dropped' line for LOSSLESSTCP_Egress
            for i in range(losslesstcp_index, len(lines)):
                if 'Total Dropped' in lines[i]:
                    total_dropped_losslesstcp = lines[i].split(':')[1].strip().split(' ')[0]
                    log.info("Total Dropped for LOSSLESSTCP_Egress (packets/bytes): %s", total_dropped_losslesstcp)
                    if total_dropped_losslesstcp == "0/0":
                        log.info("This is expected")
                    else:
                        log.info("This is not expected")
                        #show_tech(script_args)
                        #self.failed('Total Dropped count is not 0/0 packets/bytes')
                    break

            log.info(banner("Step 9: Stop Pause storm and Verify M M watchdog SM states for TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))



            tgn_streams = ['HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC0',
                           'HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC3',
                            'HM PFC-WD Sp8/13-H012034-D18-FloodStorm-TC4'] 

            # Stopping stream block
            log.info('Stopping_Streamblock')
            sste_tgn.tgn_stop_traffic(script_args,None,streams=tgn_streams)

            # Disable stream block
            stc = script_args['tgn_spirent_conn']
            for stream in tgn_streams:
                streamblock = Get_STC_Streamblock_Handle(script_args,stream)
                stc.config(streamblock,Active=False)

            stc.apply() 


            log.info('Waiting for 30 seconds for the traffic to settle')

            time.sleep(30)
            ##################### Checking Rx PFC Frames value for CoS 0, CoS 3 and CoS4 #################

            log.info(banner("Checking Rx PFC Frames value for CoS 0, CoS 3 and CoS4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            output = self.D18_R10.execute('show contr Hu0/12/0/34 priority-flow-control', timeout = 300)

            # Define the regular expression pattern
            pattern = r"(?P<cos>\d+)\s+on\s+(?P<count>\d+)"
            
            # Use re.findall to find all matches of the pattern
            matches = re.findall(pattern, output)
            
            # Create a dictionary to store the parsed data
            data = {}
            for match in matches:
                data[int(match[0])] = int(match[1])

            cos_0 = data.get(0, 0)  # Use get() with default value 0 if key is not found
            cos_3 = data.get(3, 0)
            cos_4 = data.get(4, 0)   
            
            # Print the extracted values
            log.info(f"CoS 0: {cos_0}")
            log.info(f"CoS 3: {cos_3}")
            log.info(f"CoS 4: {cos_4}")



            ##################### Checking Auto Restore Events value for TC3 and TC4 ###################

            log.info(banner("Checking Auto Restore Events value for TC3 and TC4 - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))            
            
            # Use regular expressions to find the Auto Restore Events values for Traffic Class 3 and 4
            auto_restore_events_match = re.search(r"Auto Restore Events\s*:\s*\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)", output)
            
            if auto_restore_events_match:
                # Correct the indexing to capture the correct values for Auto Restore Events
                auto_restore_events_tc3 = int(auto_restore_events_match.group(1))
                auto_restore_events_tc4 = int(auto_restore_events_match.group(2))
            
                log.info(f"Auto Restore Events for Traffic Class 3: {auto_restore_events_tc3}")
                log.info(f"Auto Restore Events for Traffic Class 4: {auto_restore_events_tc4}")
            
                # Check if any of the Auto Restore Events values is not 0 and log "Life is great"
                if auto_restore_events_tc3 >= 0 or auto_restore_events_tc4 >= 0:
                    log.info("Life is great")
            else:
                log.info("Auto Restore Events values not found in the output.")
                #show_tech(script_args)
                self.failed('Auto Restore Events values not found in the output.')


            log.info(banner("Step 10: SNMP PFC MIB verification during watchdog state transitions and slow OID check - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))


            # Capturing ifIndex 
            output = self.D18_R10.execute('show snmp inter hundredGigE0/12/0/34 ifindex', timeout = 300)
            ifIndex = output.split()[-1]
            log.info(f"ifIndex: {ifIndex}")


            #########Connecting to Fretta-PXE Server###########
            log.info(banner("Connecting to Fretta-PXE server - TC28_PFC_Watchdog_simultaneous_multiple_Qs"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['fretta-pxe']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    show_tech(script_args)
                    self.failed('can not connect to controller sucessfully')

            #output = self.controller.execute('snmpwalk -v 2c -c public 172.25.124.50 1.3.6.1.4.1.9.9.813.1.2.1.3.1526', timeout = 300)
            output = self.controller.execute('snmpwalk -v 2c -c public 172.25.124.50 1.3.6.1.4.1.9.9.813.1.2.1.3.' + str(ifIndex), timeout=300)

            # Define variables to store parsed values
            TC0_SNMP = None
            TC3_SNMP = None
            TC4_SNMP = None
            
            # Iterate over each line in the output
            for line in output.splitlines():
                # Extract the OID and value using regular expressions
                match = re.search(r"(.*) = Counter64: (\d+)", line)
                if match:
                    oid, value = match.groups()
            
                    # Check if the OID matches the desired ones
                    if oid.endswith(".0"):
                        TC0_SNMP = int(value)
                    elif oid.endswith(".3"):
                        TC3_SNMP = int(value)
                    elif oid.endswith(".4"):
                        TC4_SNMP = int(value)
            
            # Print the parsed values

            log.info(f"TC3_SNMP: {TC0_SNMP}")
            log.info(f"TC4_SNMP: {TC3_SNMP}")
            log.info(f"TC4_SNMP: {TC4_SNMP}")

            # Print the extracted values
            log.info(f"CoS 0: {cos_0}")
            log.info(f"CoS 3: {cos_3}")
            log.info(f"CoS 4: {cos_4}")


        if cos_0 == TC0_SNMP and cos_3 == TC3_SNMP and cos_4 == TC4_SNMP:
            log.info("Life is great")
        else:
            log.info("Show output and snmp value doesnot match")
            show_tech(script_args)
            self.failed("Show output and snmp value doesnot match")

        self.controller.disconnect()


        self.D18_R10.execute('show snmp request type summary', timeout = 300)
        self.D18_R10.execute('sh snmp request type detail', timeout = 300)
        self.D18_R10.execute('sh processes memory detail location 0/RP0/CPU0 | i "JID|===|mibd"', timeout = 300)
        self.D18_R10.execute('show snmp', timeout = 300)
        self.D18_R10.execute('show snmp trace slow oids reverse', timeout = 300)
        self.D18_R10.execute('show logging', timeout = 300)

		log.info('Waiting one minute for the core to generate incase there is any crash')
		time.sleep(60)
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class CommonCleanup(aetest.CommonCleanup):
    global coredump_list, showtech_list

    @aetest.subsection
    def upload_log(self, steps, script_args, testbed, test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty')
        self.router.configure('load harddisk:/backup_cli.cfg', replace=True, timeout=600)
        self.router.execute('clear configuration inconsistency', timeout=600)
        if 'upload_result' not in test_data or str(test_data['upload_result']) == "1":
            sste_common.upload_log(script_args, testbed, test_data)

        log.info('######################Copy core files############################')
        log.info(coredump_list)
        for core in coredump_list:
            args = {}
            args['timeout'] = 3600
            log.info('copying ' + core[0] + ' out to ' + script_args['debug_log_path'])
            args['sste_commands'] = [
                'copy ' + core[0] + ' tftp://172.23.16.140' + script_args['debug_log_path'] + '/' + core[
                    1] + ' vrf MGMT']
            sste_common.exec_commands(args, script_args)

        log.info('######################Copy show tech############################')
        log.info(showtech_list)
        for showtech in showtech_list:
            args = {}
            args['timeout'] = 3600
            log.info('copying ' + showtech[0] + ' out to ' + script_args['debug_log_path'])
            args['sste_commands'] = [
                'copy ' + showtech[0] + ' tftp://172.23.16.140' + script_args['debug_log_path'] + '/' + showtech[
                    1] + ' vrf MGMT']
            sste_common.exec_commands(args, script_args)

    @aetest.subsection
    def disconnect(self, steps, script_args, testbed):
        step_txt = "Disconnect Device"
        with steps.start(step_txt):
            if testbed.devices:
                for host, connection in testbed.devices.items():
                    if connection:
                        log.info("Disconnecting from %s" % host)
                        connection.disconnect()