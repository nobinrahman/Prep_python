#!/bin/env python

import sys

sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
import re
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

def Controller(failed, steps, script_args, testscript, testbed, test_data, timing):
    #########Connecting to SwanAgent###########
    log.info(banner("Connecting to Linux Box"))
    index = 0
    while 1:

        try:
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)

            controller = genietestbed.devices['dhirshah-26']
            controller.connect(via='linux', connection_timeout=300)
            break
        except:
            index += 1
            time.sleep(60)
        if index == 10:
            failed('can not connect to controller sucessfully')
    controller.execute('unset http_proxy')
    controller.execute('unset https_proxy')
    controller.execute('cd /root/MBB_MASTER/MIXED && ./mixed-clis_transition.sh', timeout = 300)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4_empty_fib.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    
    # '''controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/v4-ecmp-2nh-per-class-no-noncbf-250.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: #gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(120)'''

    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml| curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(2)
    # controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    # time.sleep(10)
    controller.disconnect()


def Verifier_Before(failed, steps, script_args, testscript, testbed, test_data, timing):
    
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    
    log.info(genietestbed.devices)
    
    D8WAN = genietestbed.devices['D8WAN']
    D8WAN.connect(via='vty',connection_timeout=300)
    D8WAN.execute('clear log', timeout = 300)
    D8WAN.execute('clear context', timeout = 300)

    output = D8WAN.execute('show cef mpls local-label 24000 EOS det location 0/0/CPU0  | i Y | u wc -l', timeout = 300)
    # Split the output by whitespace
    parts = output.split()

    # Get the last element, which is the number you want
    number = parts[-1]

    # Convert the number to an integer (optional)
    global count_value1
    count_value1 = int(number)
    log.info("Hash count value before trigger: %s", count_value1)
            
    ########################Interface Accounting########################
    int_accounting = D8WAN.execute('show interfaces Bundle-Ether 28000 accounting rates', timeout = 300)

    lines = int_accounting.strip().split("\n")
    pkts_sec_line = None

    for line in lines:
        if "MPLS" in line:
            pkts_sec_line = line
            break

    # Extract the MPLS Egress Pkts/sec value
    if pkts_sec_line is not None:
        cols = pkts_sec_line.split()
        global pkts_sec_value1
        pkts_sec_value1 = int(cols[4])
    log.info("Interface Accounting value before trigger: %s", pkts_sec_value1)


    ########################Interface Accounting########################
    int_accounting = D8WAN.execute('show interfaces Bundle-Ether 28002 accounting rates', timeout = 300)

    lines = int_accounting.strip().split("\n")
    pkts_sec_line = None

    for line in lines:
        if "MPLS" in line:
            pkts_sec_line = line
            break

    # Extract the MPLS Egress Pkts/sec value
    if pkts_sec_line is not None:
        cols = pkts_sec_line.split()
        global pkts_sec_value3
        pkts_sec_value3 = int(cols[4])
    log.info("Interface Accounting value before trigger: %s", pkts_sec_value3)


    log.info(banner("Checking 4k Labels"))
    counter = 0
    index = 0
    while 1:
        output= D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
        # if output.count('4000'):
        #     break
        # counter += 1
        # if counter >= 15:
        #     break
        # time.sleep(5)
        outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
        outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
        if outputDefault.count('path up') == 4 and outputScavenger.count('path up') == 6:
            time.sleep(60)
            break
        time.sleep(5)
        index += 1
        if index == 120:
            log.error('###################\nlabels not recovered\n###################')
            break
    D8WAN.disconnect()


def Verifier_After(failed, steps, script_args, testscript, testbed, test_data, timing):

    ##################################### Connecting to D8WAN #################################
    log.info(banner("Connecting D8WAN for verification"))
    #testbed_file = testbed.testbed_file
    #genietestbed = load(testbed_file)
    
    #log.info(genietestbed.devices)
    
    #D8WAN = genietestbed.devices['D8WAN']
    #D8WAN.connect(via='vty',connection_timeout=300)
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)

    log.info(genietestbed.devices)

    D8WAN = genietestbed.devices['D8WAN']
    retry = 0
    while retry < 10:
        try:
            D8WAN.connect(via='vty', connection_timeout=600, mit=True)
            break
        except:
            time.sleep(10)
            retry += 1
            if retry == 10:
                log.failed('connect failed')
    D8WAN.execute('clear log', timeout = 300)
    D8WAN.execute('clear context', timeout = 300)


    #######################Checking 4k Labels#########################
    
    log.info(banner("Checking 4k Labels"))
    counter = 0
    index = 0
    while 1:
        output= D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
        # if output.count('4000'):
        #     break
        # counter += 1
        # if counter >= 15:
        #     break
        # time.sleep(5)
        outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
        outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
        if outputDefault.count('path up') == 4 and outputScavenger.count('path up') == 6:
            time.sleep(60)
            break
        time.sleep(5)
        index += 1
        if index == 120:
            log.error('###################\nlabels not recovered\n###################')
            break

    ########################Interface Accounting########################
    int_accounting = D8WAN.execute('show interfaces Bundle-Ether 28000 accounting rates', timeout = 300)

    lines = int_accounting.strip().split("\n")
    pkts_sec_line = None

    for line in lines:
        if "MPLS" in line:
            pkts_sec_line = line
            break

    # Extract the MPLS Egress Pkts/sec value
    if pkts_sec_line is not None:
        cols = pkts_sec_line.split()
        pkts_sec_value2 = int(cols[4])
    global pkts_sec_value1
    log.info("Interface Accounting value Before trigger: %s", pkts_sec_value1)
    log.info("Interface Accounting value After trigger: %s", pkts_sec_value2)

    # Calculate the difference percentage
    diff_percentage = abs(pkts_sec_value1 - pkts_sec_value2) / max(pkts_sec_value1, pkts_sec_value2) * 100
    log.info("Interface Accounting value diff percentage: %s", diff_percentage)
    # Check if the difference is within 5% tolerance level
    tolerance = 80
    if diff_percentage <= tolerance:
        log.info("Values are within 5% tolerance.")
    else:
        failed('Testcase failed: Values are not within 5% tolerance.\n')


    ########################Interface Accounting########################
    int_accounting = D8WAN.execute('show interfaces Bundle-Ether 28002 accounting rates', timeout = 300)

    lines = int_accounting.strip().split("\n")
    pkts_sec_line = None

    for line in lines:
        if "MPLS" in line:
            pkts_sec_line = line
            break

    # Extract the MPLS Egress Pkts/sec value
    if pkts_sec_line is not None:
        cols = pkts_sec_line.split()
        pkts_sec_value4 = int(cols[4])
    global pkts_sec_value3
    log.info("Interface Accounting value Before trigger: %s", pkts_sec_value3)
    log.info("Interface Accounting value After trigger: %s", pkts_sec_value4)

    # Calculate the difference percentage
    diff_percentage = abs(pkts_sec_value3 - pkts_sec_value4) / max(pkts_sec_value3, pkts_sec_value4) * 100
    log.info("Interface Accounting value diff percentage: %s", diff_percentage)
    # Check if the difference is within 5% tolerance level
    tolerance = 80
    if diff_percentage <= tolerance:
        log.info("Values are within 5% tolerance.")
    else:
        failed('Testcase failed: Values are not within 5% tolerance.\n')


                

    ######################## Checking Hash Count ############################
    log.info(banner("Comparing hash count value before and after trigger"))
            
            
    output = D8WAN.execute('show cef mpls local-label 24000 EOS det location 0/0/CPU0  | i Y | u wc -l', timeout = 300)
    # Split the output by whitespace
    parts = output.split()

    # Get the last element, which is the number you want
    number = parts[-1]

    # Convert the number to an integer (optional)
    count_value2 = int(number)
    log.info("Hash Count Value after trigger: %s", count_value2)
    global count_value1
    if count_value1 != count_value2:
        failed('Hash Count value doesnot match\n')
        #log.info("Testcase failed: Values are not same.")
    else:
        log.info("Hash Count value before and after matches")

    

    ##########################Clearing MPLS Forwarding Counter######################

    log.info(banner("Clearing MPLS Forwarding Counters"))
    D8WAN.execute('clear mpls forwarding counters', timeout = 300)
    time.sleep(180)
    ###########################Checking Byte Switched Value #########################
    log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
    output = D8WAN.execute('show mpls forwarding labels 24000 24999', timeout = 300)
    time.sleep(30)
    # Parse byte switched values using regular expressions
    byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

    # Convert string values to integers
    byte_switched_values = [int(value) for value in byte_switched_values]

    # Check if the list contains any non-zero values
    if all(value == 0 for value in byte_switched_values):
        log.info ('Non Zero Value notFound')
        failed('MPLS Byte switch is not happening\n')
    else:
        log.info ('Non Zero Value Found')

    #################################CPU Utilization Check ######################

    '''# Check if the interface accounting rates increasing
    log.info(banner("Checking CPU Utilization"))
    output = D8WAN.execute('show proc cpu  | ex "0%      0%       0%"', timeout = 300)
    time.sleep(5)

    # Split the output by lines
    lines = output.strip().split("\n")

    # Find the index of the line with column headers
    header_index = None
    for index, line in enumerate(lines):
        if line.startswith("PID"):
            header_index = index
            break

    # Extract the CPU utilization lines starting from the line after the headers
    if header_index is not None:
        cpu_lines = lines[header_index + 1:]
    else:
        cpu_lines = []

    # Extract the CPU utilization values
    cpu_data = []
    for line in cpu_lines:
        columns = line.split()
        if len(columns) >= 5:
            pid, min1, min5, min15, process = columns
            cpu_data.append((int(min1.rstrip("%")), int(min5.rstrip("%")), int(min15.rstrip("%"))))

    # Check if any value exceeds 15%
    for min1, min5, min15 in cpu_data:
        if min1 > 15 or min5 > 15 or min15 > 15:
            failed('CPU utilization is not in limits\n')
            break
    else:
        log.info ('CPU utilization is in limits')'''

    
    ######################## Pending Delete Object ##############################
    log.info(banner("Checking Pending delete object"))
    D8WAN.send('attach location 0/4/CPU0\n', timeout = 300)
    time.sleep(5)
    output = str(D8WAN.send('python /pkg/bin/debug-pending-delete.py\n', timeout = 300))
    time.sleep(90)
    
    D8WAN.send('exit\n', timeout = 300)
    time.sleep(5)
    D8WAN.execute('show version', timeout = 300)

    D8WAN.disconnect()

    ##############  Clearing Traffic Stats ################
    log.info(banner("Clearing Traffic Stats"))
    sste_tgn.tgn_clear_stats(script_args, test_data)
    log.info("Cleared Traffic Stats")


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


@aetest.skip(reason='debug')
class TC1_TEST(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)



#@aetest.skip(reason='debug')
class TC1_LOCAL_BE_SHUT_NOSHUT(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        log.info(banner("TC1.1_Ingress_All_Path_shut_both_FC"))
        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing) 
            time.sleep(10) 

            ###################  Clearing Traffic Stats ######################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D8WAN_BE_SHUT_NOSHUT ######################

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Shut All DEFAULT & SCAVENGER Ingress Path"))
            
                self.D8WAN.config('interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007 shutdown', timeout = 300)
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error "))
    
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                self.D8WAN.config('no interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007 shutdown', timeout = 300)
                time.sleep(150)
                log.info(banner("Checking Hardware Programming Error "))
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
    
            
                log.info(banner("Trigger ENDS"))
                time.sleep(5)


            self.D8WAN.disconnect()
            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC2_WITH_SINGLE_FC_ALL_PATH_SHUT_UNSHUT(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        log.info(banner("TC2.1_WITH_SINGLE_FC_ALL_PATH_SHUT"))
        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)

            #######################Test environment getting ready #####################
            log.info(banner("Making the test scenario ready"))
            self.D8WAN.config('interface Bundle-Ether 28000,28001,28002,28003 shutdown', timeout = 300)
            time.sleep(30)
            

            ###################  Clearing Traffic Stats ######################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            ###################### D8WAN_BE_SHUT_NOSHUT ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Shut All DEFAULT & SCAVENGER Ingress Path"))
            
                self.D8WAN.config('interface Bundle-Ether 28004,28005 shutdown', timeout = 300)
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error "))
    
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("TC2.2_WITH_SINGLE_FC_ALL_PATH_NOSHUT"))

                self.D8WAN.config('no interface Bundle-Ether 28004,28005 shutdown', timeout = 300)
                time.sleep(30)
                log.info(banner("Checking Hardware Programming Error "))
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
    
            
                log.info(banner("Trigger ENDS"))
                time.sleep(10)
            #######################Bringing back to previous state #####################
            log.info(banner("Going Back to Previous State"))
            self.D8WAN.config('no interface Bundle-Ether 28000,28001,28002,28003 shutdown', timeout = 300)
            time.sleep(150)

            self.D8WAN.disconnect()
            
            ##################################### Verifier_After ###################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


@aetest.skip(reason='debug')
class TC3_LOCAL_BE_CONFIG_UNCONFIG(aetest.Testcase):
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

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC3.1-Ingress_Remote_BE_UnConfig"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Removing & Configuring bundles from Physical Interfaces for both DEFAULT & SCAVENGER "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
        
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface FourHundredGigE0/6/0/26\n'
                                    'no bundle id 28000 mode active\n'
                                    'interface FourHundredGigE0/6/0/27\n'
                                    'no bundle id 28000 mode active\n'
                                    'interface FourHundredGigE0/6/0/28\n'
                                    'no bundle id 28002 mode active\n'
                                    'interface FourHundredGigE0/6/0/29\n'
                                    'no bundle id 28002 mode active\n'
                                    'interface FourHundredGigE0/2/0/20\n'
                                    'no bundle id 28001 mode active\n'
                                    'interface FourHundredGigE0/2/0/21\n'
                                    'no bundle id 28003 mode active', timeout = 300)


            
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error "))

                output = self.D12W.execute('', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')



                self.D12W.configure('interface FourHundredGigE0/6/0/26\n'
                                    'bundle id 28000 mode active\n'
                                    'interface FourHundredGigE0/6/0/27\n'
                                    'bundle id 28000 mode active\n'
                                    'interface FourHundredGigE0/6/0/28\n'
                                    'bundle id 28002 mode active\n'
                                    'interface FourHundredGigE0/6/0/29\n'
                                    'bundle id 28002 mode active\n'
                                    'interface FourHundredGigE0/2/0/20\n'
                                    'bundle id 28001 mode active\n'
                                    'interface FourHundredGigE0/2/0/21\n'
                                    'bundle id 28003 mode active', timeout = 300)

            
                time.sleep(150)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Trigger ENDS"))

            
                self.D12W.disconnect()
            
            time.sleep(30)


            
            ##################################### Verifier_After ###################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

@aetest.skip(reason='debug')
class TC4_BE_MEMBER_LINK_MVMT_ACROSS_NH_BE(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            log.info(banner("Connecting to Linux Box"))
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC4.0_BE_Member_Links_Mvmt_Across_NH_BE"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)           

            ############### Trigger in D12W ###################
            
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Interchanging Bundle Members"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface FH0/6/0/26\n'
                                    'bundle id 28001 mode active\n'
                                    'interface FourHundredGigE0/6/0/27\n'
                                    'bundle id 28000 mode active', timeout=300)
                time.sleep(30)


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D8WAN = genietestbed.devices['D8WAN']
                self.D8WAN.connect(via='vty', connection_timeout=300)
                self.D8WAN.config('interface FH0/4/0/26\n bundle id 28001 mode active\n interface FH0/4/0/27\n bundle id 28000 mode active ', timeout = 300)
                time.sleep(30)
            
                log.info(banner("Checking Hardware Programming Error"))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Bundle status"))

                self.D8WAN.execute('show interfaces brief | i BE28000', timeout = 300)
                self.D8WAN.execute('show interfaces brief | i BE28001', timeout = 300)
            

                self.D12W.execute('show interfaces brief | i BE28001', timeout = 300)
                self.D12W.execute('show interfaces brief | i BE28000', timeout = 300)
            


                #########################Rolling back to previous consfig #####################
                log.info(banner("Moving the Interfaces to their Previous Bundles"))


                self.D12W.execute('rollback configuration last 1', timeout = 300)
                time.sleep(30)

            

                log.info(banner("Checking Hardware Programming Error"))
            

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)

                log.info(banner("Moving the Interfaces to their Previous Bundles"))
    
                self.D8WAN.execute('rollback configuration last 1', timeout = 300)
                time.sleep(150)
            
                log.info(banner("Checking Hardware Programming Error"))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)


                log.info(banner("Trigger ENDS")) 
                time.sleep(30)   
            
                self.D12W.disconnect()
                self.D8WAN.disconnect()
            

            ##################################### Verifier_After ###################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

@aetest.skip(reason='debug')
class TC5_REMOTE_BE_CONFIG_UNCONFIG(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC5.0_Ingress_Local_Bundle_Unconfig_Config"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            

            ###################### D8W_BE_SHUT_NOSHUT######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
            
                log.info(banner("Trigger: Removing All DEFAULT & SCAVENGER Bundles"))  
            
                self.D8WAN.config('no interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007', timeout = 300)
                time.sleep(30)
                
                log.info(banner("Checking Hardware Programming Error")) 
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
    
                time.sleep(10)
        
                


                log.info(banner("Trigger: Configuring All DEFAULT & SCAVENGER Bundles"))  
            
                self.D8WAN.config('interface Bundle-Ether28000\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.0\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'service-policy input CORE-QOS-IN\n'
                                    'ipv4 address 20.1.0.1 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::1:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'flow mpls monitor IPFIX_MAP_MPLS sampler IPFIX_SM ingress\n'
                                    'logging events link-status ', timeout=300)
                time.sleep(30)

                self.D8WAN.config('interface Bundle-Ether28001\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.2\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'service-policy input CORE-QOS-IN\n'
                                    'ipv4 address 20.1.0.3 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::2:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'flow mpls monitor IPFIX_MAP_MPLS sampler IPFIX_SM ingress\n'
                                    'logging events link-status ', timeout=300)
                time.sleep(30)

                self.D8WAN.config('interface Bundle-Ether28002\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.4\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'service-policy input CORE-QOS-IN\n'
                                    'ipv4 address 20.1.0.5 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::3:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'flow mpls monitor IPFIX_MAP_MPLS sampler IPFIX_SM ingress\n'
                                    'logging events link-status ', timeout=300)
                time.sleep(30)

                self.D8WAN.config('interface Bundle-Ether28003\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.6\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'service-policy input CORE-QOS-IN\n'
                                    'ipv4 address 20.1.0.7 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::4:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'flow mpls monitor IPFIX_MAP_MPLS sampler IPFIX_SM ingress\n'
                                    'logging events link-status ', timeout=300)


                self.D8WAN.config('interface Bundle-Ether28004\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.8\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'service-policy input CORE-QOS-IN\n'
                                    'service-policy output CORE-QOS-OUT-400G\n'
                                    'ipv4 address 20.1.0.9 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::5:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'flow mpls monitor IPFIX_MAP_MPLS sampler IPFIX_SM ingress\n'
                                    'logging events link-status ', timeout=300)


                self.D8WAN.config('interface Bundle-Ether28005\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.10\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'ipv4 address 20.1.0.11 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::6:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'logging events link-status ', timeout=300)


                self.D8WAN.config('interface Bundle-Ether28006\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.12\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'ipv4 address 20.1.0.13 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::7:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'logging events link-status ', timeout=300)

                self.D8WAN.config('interface Bundle-Ether28007\n'
                                    'description ###CONN_D12W_D8WAN####\n'
                                    'bfd mode ietf\n'
                                    'bfd address-family ipv4 multiplier 5\n'
                                    'bfd address-family ipv4 destination 20.1.0.14\n'
                                    'bfd address-family ipv4 fast-detect\n'
                                    'bfd address-family ipv4 minimum-interval 100\n'
                                    'mtu 9192\n'
                                    'ipv4 address 20.1.0.15 255.255.255.254\n'
                                    'ipv6 nd suppress-ra\n'
                                    'ipv6 address 4001:1::8:1/127\n'
                                    'lacp cisco enable\n'
                                    'lldp\n'
                                    'bundle maximum-active links 64\n'
                                    'load-interval 30\n'
                                    'logging events link-status ', timeout=300)
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                log.info(banner("Checking Out of Resource Error"))
                
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)

                self.D8WAN.disconnect()

            time.sleep(150)
            
            
            
            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC6_INGRESS_BOTH_DEFAULT_PATH_SHUT_UNSHUT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC6.1_Ingress_Remote_Class_Default_FC0_All_Path_Shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut Both Default Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28000,28001,28002,28003 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                self.D12W.configure('no interface Bundle-Ether 28000,28001,28002,28003 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(30)
            
                self.D12W.disconnect()
        
            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC7_REMOTE_BE_SHUT_NOSHUT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC7.1_Ingress_Remote_All_Path_Shut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger:Shut All DEFAULT & SCAVENGER Path"))



                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                self.D12W.configure('no interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007 shutdown', timeout=60)
                time.sleep(30) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)

                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
                
                self.D12W.disconnect()
            
            time.sleep(150)


            

            ##################################### Verifier_After ###################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#############################################################Transit NODE###########################################################


#@aetest.skip(reason='debug')
class TC13_Transit_Node_DEFAULT_PATH_SHUT_ONE(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC13.1-TC13.2_Transit_Node_Local_Single_Path_FC0_Shut"))

            

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### SHUT_NOSHUT_INTERFACE ######################
        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))    

            log.info(banner("Trigger: Shut Transit Node FC0 single Bundle"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28100,28101 shutdown', timeout=60)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: NoShut Transit Node FC0 single Bundle"))

            self.D8W.configure('no interface Bundle-Ether 28100,28101 shutdown', timeout=60)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)

            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(30)

            self.D8W.disconnect()
        

        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()
        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)
        



        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC14_Transit_Node_DEFAULT_PATH_SHUT_NOSHUT_BOTH(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC14.1-TC14.2_Transit_Node_Local_Single_Shut_FC0_FC1"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)
            


            ###################### SHUT_NOSHUT_INTERFACE ######################
            
        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)): 
            log.info(banner(f"Loop number: {beloop}"))   

            log.info(banner("Trigger: Transit Node both DEFAULT Bundle Shut"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28100,28101,28102,28013 shutdown', timeout=60)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: Transit Node both DEFAULT Bundle NoShut"))

            self.D8W.configure('no interface Bundle-Ether 28100,28101,28102,28103 shutdown', timeout=60)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)
            
            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)

            log.info(banner("Trigger ENDS"))

            time.sleep(30)

            self.D8W.disconnect()
        


        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC15_Transit_Node_SCAVENGER_PATH_SHUT_ONE(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC15.1-15.2_Transit_Node_Local_Single_Path_SCAVENGER_Shut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        ###################### SHUT_INTERFACE ######################
            
        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))    

            log.info(banner("Trigger: Shut_Transit Node_Scavenger_Bundle"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28104,28105 shutdown', timeout=60)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: NoShut_Transit Node_Scavenger_Bundle"))

            self.D8W.configure('no interface Bundle-Ether 28104,28105 shutdown', timeout=60)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)


            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(30)

            
            self.D8W.disconnect()



        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC16_Transit_Node_SCAVANGER_PATH_SHUT_NOSHUT_BOTH(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC16.1-TC16.2_Transit_Node_Local_Single_Path_FC1_Both_shut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### SHUT_NOSHUT_INTERFACE ######################
            
        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)): 
            log.info(banner(f"Loop number: {beloop}"))   

            log.info(banner("Trigger: Shut Both FC1 Bundle"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28104,28105,28106,28107 shutdown', timeout=300)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: NoShut Both FC1 Bundle"))

            self.D8W.configure('no interface Bundle-Ether 28104,28105,28106,28107 shutdown', timeout=300)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)

            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(30)

            self.D8W.disconnect()
        


        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC17_Transit_Node_DEFAULT_SCAVANGER_PATH_SHUT_NOSHUT(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC17.1-TC17.2_Transit_Node_Local_Path_FC0_FC1_All_Path_shut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)
            



            ###################### SHUT_NOSHUT_INTERFACE ######################


        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))    

            log.info(banner("Trigger: Shut Both Default & SCAVENGER Bundles"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28100,28101,28102,28103,28004,28005,28006,28007 shutdown', timeout=60)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: NoShut Both Default & SCAVENGER Bundles"))

            self.D8W.configure('no interface Bundle-Ether 28100,28101,28102,28103,28004,28005,28006,28007 shutdown', timeout=60)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)

            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(30)
            self.D8W.disconnect()

        
        


        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC18_Deagg_Agg(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
        log.info(banner("TC19.0_Deagg_Agg_Deagg_Transition_Every_2s")) 

        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))

            #########Connecting to SwanAgent###########
            log.info(banner("Connecting to Linuxbox"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['dhirshah-26']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    self.failed('can not connect to controller sucessfully')
            
            self.controller.execute('unset http_proxy')
            self.controller.execute('unset https_proxy')
            self.controller.execute('cd /root/MBB_MASTER/MIXED && ./mixed-clis_transition.sh', timeout = 300)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml| curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(10)


            

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8WAN = genietestbed.devices['D8WAN']
        self.D8WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking 4k Labels"))
        counter = 0 
        index = 0
        while 1:
            output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
            # if output.count('4000'):
            #     break
            # counter += 1
            # if counter >= 15:
            #     break
            outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
            outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
            if outputDefault.count('path up') == 4 and outputScavenger.count('path up') == 6:
                time.sleep(60)
                break
            time.sleep(5)
            index += 1
            if index == 120:
                log.error('###################\nlabels not recovered\n###################')
                break
                time.sleep(5)
            log.info(banner("Checking Hardware Programming Error"))
        output= self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)

        log.info(banner("Checking Hardware Programming Error"))
        self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')
        time.sleep(10)

        log.info(banner("Checking Out of Resource Error"))
        output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

        if output.count('OOR_RED'):
            self.failed('Out of Resource Error Found\n')
        time.sleep(10)



        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8W = genietestbed.devices['D8W']
        self.D8W.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')
        time.sleep(10)

        log.info(banner("Checking Out of Resource Error"))
        output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

        if output.count('OOR_RED'):
            self.failed('Out of Resource Error Found\n')
        time.sleep(10)

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D18WAN = genietestbed.devices['D18WAN']
        self.D18WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')
        time.sleep(10)
        log.info(banner("Checking Out of Resource Error"))
        output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

        if output.count('OOR_RED'):
            self.failed('Out of Resource Error Found\n')
        time.sleep(10)

        ################DISCONNECT FROM DEVICES#####################
        self.D8WAN.disconnect()
        self.D8W.disconnect()
        self.D12W.disconnect()
        self.D18WAN.disconnect()
        self.controller.disconnect()

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC19_Deagg_Agg_Agg(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
        log.info(banner("TC19.0_Deagg_Agg_Agg_Transition_Every_2s")) 

        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))

            #########Connecting to SwanAgent###########
            log.info(banner("Connecting to Linuxbox"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['dhirshah-26']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    self.failed('can not connect to controller sucessfully')
            
                
            self.controller.execute('unset http_proxy')
            self.controller.execute('unset https_proxy')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            
            #SWAN V4 Programming-ECMP
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-UCMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-NONCBF-POP-10K.xml | curl -s -X POST http://172.25.124.79:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-1000CBF-6K-Impose-24x-UCMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-NONCBF-POP-10K.xml | curl -s -X POST http://172.25.124.54:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('ip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            #SWAN V4 Programming-UCMP
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-UCMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-NONCBF-POP-10K.xml | curl -s -X POST http://172.25.124.79:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-1000CBF-6K-Impose-24x-UCMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-NONCBF-POP-10K.xml | curl -s -X POST http://172.25.124.54:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(2)
            self.controller.execute('ip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(30)


            

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8WAN = genietestbed.devices['D8WAN']
        self.D8WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking 4k Labels"))
        counter = 0 
        index = 0 
        while 1:
            output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
            # if output.count('4000'):
            #     break
            # counter += 1
            # if counter >= 15:
            #     break
            # time.sleep(5)
            outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
            outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
            if outputDefault.count('path up') == 4 and outputScavenger.count('path up') == 6:
                time.sleep(60)
                break
            time.sleep(5)
            index += 1
            if index == 120:
                log.error('###################\nlabels not recovered\n###################')
                break
                time.sleep(5)
        log.info(banner("Checking Hardware Programming Error"))
        output= self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
            
        log.info(banner("Checking Hardware Programming Error"))
        self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')



        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8W = genietestbed.devices['D8W']
        self.D8W.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D18WAN = genietestbed.devices['D18WAN']
        self.D18WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        ################DISCONNECT FROM DEVICES#######################
        self.D8WAN.disconnect()
        self.D8W.disconnect()
        self.D12W.disconnect()
        self.D18WAN.disconnect()
        self.controller.disconnect()

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


@aetest.skip(reason='debug')
class TC20_Deagg_Swap_Deagg_Swap(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
        log.info(banner("TC20.0_Deagg_Agg_SWAN_Slicing_Scenario")) 

        if 'beloop' in test_data:
                self.beloop = test_data['beloop']
        else:
                self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))

            #########Connecting to SwanAgent###########
            log.info(banner("Connecting to Linuxbox"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['dhirshah-26']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    self.failed('can not connect to controller sucessfully')
            
            self.controller.execute('unset http_proxy')
            self.controller.execute('unset https_proxy')
            self.controller.execute('cd /root/MBB_MASTER/MIXED && ./mixed-clis_transition.sh', timeout = 300)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/EWA/SouthToNorth/D8WAN_swap_V4_4K_ECMP_2LabelsStack.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-1000CBF-V4+V6-V4-UCMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            # time.sleep(2)
            # self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(30)


            

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8WAN = genietestbed.devices['D8WAN']
        self.D8WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking 4k Labels"))
        counter = 0
        index = 0 
        while 1:
            output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
            # if output.count('4000'):
            #     break
            # counter += 1
            # if counter >= 15:
            #     break
            # time.sleep(5)
            outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
            outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
            if outputDefault.count('path up') == 4 and outputScavenger.count('path up') == 6:
                time.sleep(60)
                break
            time.sleep(5)
            index += 1
            if index == 120:
                log.error('###################\nlabels not recovered\n###################')
                break
                time.sleep(5)
        log.info(banner("Checking Hardware Programming Error"))
        output= self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
            
        log.info(banner("Checking Hardware Programming Error"))
        self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')



        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8W = genietestbed.devices['D8W']
        self.D8W.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D18WAN = genietestbed.devices['D18WAN']
        self.D18WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        ################DISCONNECT FROM DEVICES#######################
        self.D8WAN.disconnect()
        self.D8W.disconnect()
        self.D12W.disconnect()
        self.D18WAN.disconnect()
        self.controller.disconnect()

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC21_DEFAULT_PATH_PRESENT_SCAVENGER_PATH_ADDED(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC21_Class default FC0 present and scavenger class FC1 paths are added"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut Both scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28004,28005,28006,28007 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: NO Shut Both scavenger Path"))

                self.D12W.configure('no interface Bundle-Ether 28004,28005,28006,28007 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()
            log.info(banner("Trigger ENDS"))
        
            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC22_DEFAULT_SCAVENGER_ALL_PATH_SHUT_SINGLE_PATH_DEFAULT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC22_Class default FC0 and Scavenger class FC1 with 2 paths each. Shut single path in FC0, unshut path"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut Single Default Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28001 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: No Shut Single Default Path"))

                self.D12W.configure('no interface Bundle-Ether 28001 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()

                log.info(banner("Trigger ENDS"))
        

            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC23_DEFAULT_SCAVENGER_ALL_PATH_SHUT_SINGLE_PATH_SCAVENGER(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC23_Class default FC0 and Scavenger class FC1 with 2 paths each. Shut single path in FC1, unshut path"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut Single Default Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28004 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: No Shut Single Default Path"))

                self.D12W.configure('no interface Bundle-Ether 28004 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()
        
            

            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass




#@aetest.skip(reason='debug')
class TC24_TC25_DEFAULT_SCAVENGER_ALL_PATH_SHUT_SINGLE_PATH_DEFAULT_SCAVENGER(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC24_Class default FC0 and Scavenger class FC1 with 2 paths each. Shut single path in FC1, unshut path"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut Single Default & Scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28001,28004 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: Shut Single Default & Scavenger Path"))

                self.D12W.configure('no interface Bundle-Ether 28001,28004 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()
            
            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC26_CLASS_SCAVENGER_ALL_PATH_SHUT_NOSHUT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC26_Class scavenger all paths shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut both Scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28004,28005,28006,28007 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: NoShut both Scavenger Path"))

                self.D12W.configure('no interface Bundle-Ether 28004,28005,28006,28007 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()

                log.info(banner("Trigger ENDS"))
        
            

            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC27_CLASS_DEFAULT_ALL_PATH_SHUT_SCAVENGER_SINGLE(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC27_Class default FC0 all paths shut, class scavenger FC1 single path shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut both Default & Single Scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: Shut both Default & Single Scavenger Path"))

                self.D12W.configure('no interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()
                log.info(banner("Trigger ENDS"))
            
            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC28_CLASS_SCAVENGER_ALL_PATH_SHUT_DEFAULT_SINGLE(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC27_Class default FC0 all paths shut, class scavenger FC1 single path shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut both Scavenger & Single Default Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.execute('clear log', timeout = 300)
                self.D12W.execute('clear context', timeout = 300)
                self.D12W.configure('interface Bundle-Ether 28001,28002,28003,28004,28005,28006,28007 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: Shut both Scavenger & Single Default Path"))

                self.D12W.configure('no interface Bundle-Ether 28001,28002,28003,28004,28005,28006,28007 shutdown', timeout=60)
                time.sleep(150) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()
                log.info(banner("Trigger ENDS"))
        
            

            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC29_Transit_Node_SCAVANGER_PATH_SHUT_TWO(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC29.0_Transit_Node_Local_Single_Path_FC1_Shut_NoShut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)


        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)): 
            log.info(banner(f"Loop number: {beloop}"))

            ###################### SHUT_NOSHUT_INTERFACE ######################
            log.info(banner("Trigger: Transit Node Both Default and single scavenger BE shut"))

            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28100,28101,28102,28103,28104 shutdown', timeout=300)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: Transit Node Both Default and single scavenger BE noshut"))

            self.D8W.configure('no interface Bundle-Ether 28100,28101,28102,28103,28104 shutdown', timeout=300)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)

            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(60)

            self.D8W.disconnect()



        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)
           


        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass






#@aetest.skip(reason='debug')
class TC30_Transit_Node_DEFAULT_PATH_SHUT_TWO(aetest.Testcase):
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
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            

            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            log.info(banner("TC30.1_Transit_node_FC1_paths_shut_single_path_shut_FC0"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### SHUT_NOSHUT_INTERFACE ######################
            
        if 'beloop' in test_data:
            self.beloop = test_data['beloop']
        else:
            self.beloop = 1
        for beloop in range(int(self.beloop)): 
            log.info(banner(f"Loop number: {beloop}"))   

            log.info(banner("Trigger: Transit Node Local both SCAVENGER BE path shut"))



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D8W = genietestbed.devices['D8W']
            self.D8W.connect(via='vty', connection_timeout=300)
            self.D8W.execute('clear log', timeout = 300)
            self.D8W.execute('clear context', timeout = 300)
            self.D8W.configure('interface Bundle-Ether 28104,28105,28006,28007 shutdown', timeout=300)
        
            time.sleep(30)

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n') 

            log.info(banner("Trigger: NoShut Both FC1 Bundle"))

            self.D8W.configure('no interface Bundle-Ether 28104,28105,28006,28007 shutdown', timeout=300)
            time.sleep(150) 

            log.info(banner("Checking Hardware Programming Error"))

            output = self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

            if output.count('HW_PROG_ERROR'):
                self.failed('Hardware Programming Error Found\n')
            time.sleep(10)

            log.info(banner("Checking Out of Resource Error"))
            output = self.D8W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

            if output.count('OOR_RED'):
                self.failed('Out of Resource Error Found\n')
            time.sleep(10)
            
            log.info(banner("Trigger ENDS"))
            time.sleep(30)

            self.D8W.disconnect()
        


        ##########################Clearing MPLS Forwarding Counter######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
        log.info(banner("Clearing MPLS Forwarding Counters"))
        self.D12W.execute('clear mpls forwarding counters', timeout = 300)
        time.sleep(180)
        ########################## Checking Byte Switched Value #########################
        log.info(banner("Checking MPLS Non Zero Byte Switched Value "))
        output = self.D12W.execute('show mpls forwarding labels 34000 34999', timeout = 300)
        time.sleep(30)

        # Parse byte switched values using regular expressions
        byte_switched_values = re.findall(r"\d+\s*$", output, re.MULTILINE)

        # Convert string values to integers
        byte_switched_values = [int(value) for value in byte_switched_values]

        # Check if the list contains any non-zero values
        if all(value == 0 for value in byte_switched_values):
            log.info ('Non Zero Value notFound')
            self.failed('MPLS Byte switch is not happening\n')

        self.D12W.disconnect()

        
        ################################## Verifier_After ################################
        Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC31_SHUT_ALL_LINK_5s_SPAN(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC31_WITH_SINGLE_FC_ALL_PATH_SHUT"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D8WAN_BE_SHUT_NOSHUT ######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)
            self.D8WAN.execute('clear log', timeout = 300)
            self.D8WAN.execute('clear context', timeout = 300)

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Shut All DEFAULT & SCAVENGER Ingress Path span of 5second"))
            
                self.D8WAN.config('interface Bundle-Ether 28000 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28001 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28002 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28003 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28004 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28005 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28006 shutdown', timeout = 300)
                time.sleep(5)
                self.D8WAN.config('interface Bundle-Ether 28007 shutdown', timeout = 300)
                time.sleep(5)

                log.info(banner("Checking Hardware Programming Error "))
    
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Trigger: NOShut All DEFAULT & SCAVENGER Ingress Path span of 5second"))

                self.D8WAN.config('no interface Bundle-Ether 28000 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28001 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28002 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28003 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28004 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28005 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28006 shutdown', timeout = 300)
                time.sleep(30)
                self.D8WAN.config('no interface Bundle-Ether 28007 shutdown', timeout = 300)
                time.sleep(150)
                
                log.info(banner("Checking Hardware Programming Error "))
                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
    
            
                log.info(banner("Trigger ENDS"))
                time.sleep(10)

            
            self.D8WAN.disconnect()
            
            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)
            

            #self.check_mpls_forwarding(script_args)
            

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC32_CLASS_SCAVENGER_FC1_PATH_SHUT_NOSHUT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC32_Class scavenger all paths shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)
            
            ###################################Making the test enviornment ready#######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D12W = genietestbed.devices['D12W']
            self.D12W.connect(via='vty', connection_timeout=300)
            self.D12W.execute('clear log', timeout = 300)
            self.D12W.execute('clear context', timeout = 300)
            self.D12W.configure('interface Bundle-Ether 28006,28007 shutdown', timeout=60)
        
            time.sleep(30)
            self.D12W.disconnect()

            ##############  Clearing Traffic Stats ################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut both Scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.configure('no interface Bundle-Ether 28006,28007 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: NoShut both Scavenger Path"))

                self.D12W.configure('interface Bundle-Ether 28006,28007 shutdown', timeout=60)
                time.sleep(30) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()

            ###################################Going back to previous state#######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
        
            log.info(genietestbed.devices)


            self.D12W = genietestbed.devices['D12W']
            self.D12W.connect(via='vty', connection_timeout=300)
            self.D12W.configure('no interface Bundle-Ether 28000,28001,28002,28003,28004,28005,28006,28007 shutdown', timeout=60)
            
            time.sleep(150)
            self.D12W.disconnect()
            
            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

        

#@aetest.skip(reason='debug')
class TC33_CLASS_DEFAULT_FC0_PATH_SHUT_NOSHUT(aetest.Testcase):
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
            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
            ################################## Connecting to Linux Box ###########################
            Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            log.info(banner("TC33_Class scavenger all paths shut"))
            
            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)
            
            ###################################Making the test enviornment ready#######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)


            self.D12W = genietestbed.devices['D12W']
            self.D12W.connect(via='vty', connection_timeout=300)
            self.D12W.execute('clear log', timeout = 300)
            self.D12W.execute('clear context', timeout = 300)
            self.D12W.configure('interface Bundle-Ether 28000,28001 shutdown', timeout=60)
        
            time.sleep(30)
            self.D12W.disconnect()

            ##############  Clearing Traffic Stats ################
            log.info(banner("Clearing Traffic Stats"))
            sste_tgn.tgn_clear_stats(script_args, test_data)
            log.info("Cleared Traffic Stats")

            ###################### D12W_BE_SHUT_NOSHUT######################
            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))
                log.info(banner("Trigger: Shut both Scavenger Path"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
    
                log.info(genietestbed.devices)


                self.D12W = genietestbed.devices['D12W']
                self.D12W.connect(via='vty', connection_timeout=300)
                self.D12W.configure('no interface Bundle-Ether 28000,28001 shutdown', timeout=60)
        
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n') 

                log.info(banner("Trigger: NoShut both Scavenger Path"))

                self.D12W.configure('interface Bundle-Ether 28000,28001 shutdown', timeout=60)
                time.sleep(30) 

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')
                time.sleep(10)


                log.info(banner("Checking Out of Resource Error"))
                output = self.D12W.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                time.sleep(10)
            
                self.D12W.disconnect()

            ###################################Going back to previous state#######################
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
        
            log.info(genietestbed.devices)


            self.D12W = genietestbed.devices['D12W']
            self.D12W.connect(via='vty', connection_timeout=300)
            self.D12W.configure('no interface Bundle-Ether 28000,28001,28002,28003 shutdown', timeout=60)
            
            time.sleep(150)
            self.D12W.disconnect()
            
            

            ################################## Verifier_After ################################
            Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC34_MBB(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
            
        log.info(banner("TC20.0_Deagg_Agg_SWAN_Slicing_Scenario")) 

        if 'beloop' in test_data:
                self.beloop = test_data['beloop']
        else:
                self.beloop = 1
        for beloop in range(int(self.beloop)):
            log.info(banner(f"Loop number: {beloop}"))

            #########Connecting to SwanAgent###########
            log.info(banner("Connecting to Linuxbox"))
            index = 0
            while 1:

                try:
                    testbed_file = testbed.testbed_file
                    genietestbed = load(testbed_file)

                    self.controller = genietestbed.devices['dhirshah-26']
                    self.controller.connect(via='linux', connection_timeout=300)
                    break
                except:
                    index += 1
                    time.sleep(60)
                if index == 10:
                    self.failed('can not connect to controller sucessfully')
            
            self.controller.execute('unset http_proxy')
            self.controller.execute('unset https_proxy')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MBB_TRANSITIONS_WAN_TO_INTERSLICE/D18-4NH-500V4-500V6-to-125-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_ECMP.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(10)


            

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8WAN = genietestbed.devices['D8WAN']
        self.D8WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking 4k Labels"))
        counter = 0
        while 1:
            output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
            if output.count('4000'):
                break
            counter += 1
            if counter >= 15:
                break
            time.sleep(5)
        log.info(banner("Checking Hardware Programming Error"))
        output= self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']
        self.D12W.connect(via='vty',connection_timeout=300)
            
        log.info(banner("Checking Hardware Programming Error"))
        self.D12W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')



        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8W = genietestbed.devices['D8W']
        self.D8W.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D8W.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D18WAN = genietestbed.devices['D18WAN']
        self.D18WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking Hardware Programming Error"))
        self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
        if output.count('HW_PROG_ERROR'):
            self.failed('Hardware Programming Error Found\n')

        ################DISCONNECT FROM DEVICES#######################
        self.D8WAN.disconnect()
        self.D8W.disconnect()
        self.D12W.disconnect()
        self.D18WAN.disconnect()
        self.controller.disconnect()

        if 'tgn' in test_data:
            log.info('Take_traffic_snapshot_after_trigger')
            ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            log.info(ret_val)
            if ret_val:
                log.info("traffic converged equals to : {}".format(ret_val))
            else:
                show_tech(script_args)
                self.failed("traffic not converged")
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

            