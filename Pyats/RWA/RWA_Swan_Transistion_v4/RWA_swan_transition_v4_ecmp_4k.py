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

def V4_Controller(failed, steps, script_args, testscript, testbed, test_data, timing):
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
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4_empty_fib.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    
    '''controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/v4-ecmp-2nh-per-class-no-noncbf-250.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: #gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(120)'''

    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
    time.sleep(30)
    controller.disconnect()


def V6_Controller(failed, steps, script_args, testscript, testbed, test_data, timing):
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
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4_empty_fib.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    
    '''controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/v4-ecmp-2nh-per-class-no-noncbf-250.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: #gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(120)'''

    controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(2)
    controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
    time.sleep(60)
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




    D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
    log.info(banner("Checking 4k Labels"))
    counter = 0
    while 1:
        output= D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
        if output.count('4000'):
            break
        counter += 1
        if counter >= 15:
            break
        time.sleep(5)
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
    while 1:
        output= D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
        if output.count('4000'):
            break
        counter += 1
        if counter >= 15:
            break
        time.sleep(5)

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

#@aetest.skip(reason='debug')
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
                args['timeout'] = 300
                args['sste_commands'] = ["logging container fetch-timestamp"]
                sste_common.config_commands(module_args, script_args)

                args = {}
                args['timeout'] = 300
                args['sste_commands'] = ["logging container all"]
                sste_common.config_commands(module_args, script_args)

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
class TC1_LSP_UP_DOWN_BETWN_LOCAL_AND_REMOTE_PEER(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC1.0-LSP up down between local nad remote peer"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: shut no shut  bundles from Physical Interfaces for  both DEFAULT & SCAVENGER "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                self.D18WAN.execute('clear log', timeout = 300)
                self.D18WAN.execute('clear context', timeout = 300)
                self.D18WAN.configure('interface HundredGigE0/6/0/0/0 shutdown\n'
                                    'interface FourHundredGigE0/6/0/1 shutdown\n'
                                    'interface FourHundredGigE0/0/0/20 shutdown\n'
                                    'interface HundredGigE0/6/0/0/3 shutdown', timeout=300)


            
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                self.D18WAN.configure('no interface HundredGigE0/6/0/0/0 shutdown\n'
                                    'no interface FourHundredGigE0/6/0/1 shutdown\n'
                                    'no interface FourHundredGigE0/0/0/20 shutdown\n'
                                    'no interface HundredGigE0/6/0/0/3 shutdown', timeout=300)

            
                time.sleep(150)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Trigger ENDS"))

            
                self.D18WAN.disconnect()
            
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



#@aetest.skip(reason='debug')
class TC2_CONTINUOUS_SWAN_PROGRAMMING(aetest.Testcase):
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
            
        log.info(banner("TC2.0_Continuous_Swan_Programming")) 

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
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4_empty_fib.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
    
            '''self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/v4-ecmp-2nh-per-class-no-noncbf-250.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: #gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)'''

            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4WAN-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
            time.sleep(1)
            self.controller.disconnect()


            

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8WAN = genietestbed.devices['D8WAN']
        self.D8WAN.connect(via='vty',connection_timeout=300)
        log.info(banner("Checking 4k Labels"))
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



        ####################### Connecting to D12W #######################
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D12W = genietestbed.devices['D12W']

        retry = 0
        while retry < 10:
            try:
                self.D12W.connect(via='vty', connection_timeout=600, mit=True)
                break
            except:
                time.sleep(300)
                retry += 1
                if retry == 10:
                    log.failed('connect failed')
        self.D12W.connect(via='vty',connection_timeout=300)

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

        ####################### Connecting to D8W #######################

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D8W = genietestbed.devices['D8W']
        retry = 0
        while retry < 10:
            try:
                self.D8W.connect(via='vty', connection_timeout=600, mit=True)
                break
            except:
                time.sleep(300)
                retry += 1
                if retry == 10:
                    log.failed('connect failed')
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
        
        ####################### Connecting to D18WAN #######################

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
    
        log.info(genietestbed.devices)
    
        self.D18WAN = genietestbed.devices['D18WAN']
        retry = 0
        while retry < 10:
            try:
                self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                break
            except:
                time.sleep(300)
                retry += 1
                if retry == 10:
                    log.failed('connect failed')
        log.info(banner("Checking Hardware Programming Error"))
        output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)
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
class TC5_DMAC_CHANGE(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC5.0-Dmac Change"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Changing the mac address on Bundle-Ethernet"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                self.D8WAN.configure('interface Bundle-Ether 12800\n'
                                   'mac-address 10.10.10', timeout=60)

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                self.D18WAN.execute('show arp | i 12800', timeout = 300)

                output = self.D18WAN.execute('ping 108.112.0.0', timeout = 300)
                if output.count('!'):
                    log.info('Ping test working fine')

                time.sleep(30)
                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')


                output = self.D18WAN.execute('show cef ipv6 3000::1 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+ [\w]+}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')



                output = self.D18WAN.execute('show mpls forwarding prefix 100.100.110.1/32 location 0/6/CPU0', timeout=300)

                if output.count('SR Pfx'):
                    self.failed('Traffic is using SR Path')
                else:
                    log.info('Traffic is using SWAN Path')


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

                self.D8WAN.configure('interface Bundle-Ether 12800\n'
                                   'no mac-address 10.10.10', timeout=60)
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
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



#@aetest.skip(reason='debug')
class TC6_INGRESS_LOCAL_BUNDLE_CONFIG_UNCONFIG(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC6.0-Ingress Local Bundle Config Unconfig"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Removing & Configuring bundles from Physical Interfaces for  both DEFAULT & SCAVENGER "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                self.D18WAN.execute('clear log', timeout = 300)
                self.D18WAN.execute('clear context', timeout = 300)
                self.D18WAN.configure('interface HundredGigE0/6/0/0/0\n'
                                    'no bundle id 12800 mode active\n'
                                    'interface FourHundredGigE0/6/0/1\n'
                                    'no bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/0/0/20\n'
                                    'no bundle id 12802 mode active\n'
                                    'interface HundredGigE0/6/0/0/3\n'
                                    'no bundle id 12803 mode active', timeout=60)

            
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                self.D18WAN.configure('interface HundredGigE0/6/0/0/0\n'
                                    'bundle id 12800 mode active\n'
                                    'interface FourHundredGigE0/6/0/1\n'
                                    'bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/0/0/20\n'
                                    'bundle id 12802 mode active\n'
                                    'interface HundredGigE0/6/0/0/3\n'
                                    'bundle id 12803 mode active', timeout=60)

            
                time.sleep(150)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Trigger ENDS"))

            
                self.D18WAN.disconnect()
            
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


#@aetest.skip(reason='debug')
class TC7_INGRESS_LOCAL_LC_RELOAD(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC7.0-Ingress Local LC Reload"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_LC_RELOAD######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Ingress Local LC Reload "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                try:
                    self.D18WAN.execute('reload location 0/6/CPU0 noprompt', timeout = 7200)
                except:
                    log.info("Lincard still reloading")
                    time.sleep(300)

            
                time.sleep(60)

                while True:
                    output = self.D18WAN.execute('sh platform | i 0/6/CPU0',timeout = 300)

                    if output.count('IOS XR RUN'):
                        log.info("Linecard is stable now")
                        break
                    else:
                        # If the list is empty, break out of the loop
                        log.info("Linecard is not stable yet")
                    time.sleep(30)




                log.info(banner("Checking Hardware Programming Error "))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
                time.sleep(10)
                self.controller.disconnect()

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Trigger ENDS"))

            
                self.D18WAN.disconnect()
            
            time.sleep(90)


            
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



#@aetest.skip(reason='debug')
class TC8_INGRESS_LOCAL_LC_SHUT_NOSHUT(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC8.0-Ingress Local LC Shut NoShut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_LC_RELOAD######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Ingress Local LC Shut NoShut"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                try:
                    self.D18WAN.configure('hw-module shutdown location 0/6/CPU0', timeout = 7200)
                except:
                    log.info("Lincard is shutting down")
                    time.sleep(300)

            
                time.sleep(60)

                try:
                    self.D18WAN.configure('no hw-module shutdown location 0/6/CPU0', timeout = 7200)
                except:
                    log.info("Lincard is booting")
                    time.sleep(300)

            
                time.sleep(60)

                while True:
                    output = self.D18WAN.execute('sh platform | i 0/6/CPU0',timeout = 300)

                    if output.count('IOS XR RUN'):
                        log.info("Linecard is stable now")
                        break
                    else:
                        # If the list is empty, break out of the loop
                        log.info("Linecard is not stable yet")
                    time.sleep(30)




                log.info(banner("Checking Hardware Programming Error "))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
                time.sleep(10)
                self.controller.disconnect()

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Trigger ENDS"))

            
                self.D18WAN.disconnect()
            
            time.sleep(90)


            
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

#@aetest.skip(reason='debug')
class TC9_INGRESS_REMOTE_BUNDLE_CONFIG_UNCONFIG(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC9.0-Ingress Remote Bundle Config Unconfig"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_BE_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Removing & Configuring bundles from Physical Interfaces for  both DEFAULT & SCAVENGER "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                self.D8WAN.execute('clear log', timeout = 300)
                self.D8WAN.execute('clear context', timeout = 300)
                self.D8WAN.configure('interface HundredGigE0/6/0/0/0\n'
                                    'no bundle id 12800 mode active\n'
                                    'interface FourHundredGigE0/5/0/32\n'
                                    'no bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/5/0/33\n'
                                    'no bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/6/0/1\n'
                                    'no bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/0/0/20\n'
                                    'no bundle id 12802 mode active\n'
                                    'interface FourHundredGigE0/5/0/35\n'
                                    'no bundle id 12803 mode active\n'
                                    'interface HundredGigE0/6/0/0/3\n'
                                    'no bundle id 12803 mode active\n', timeout=300)

            
                time.sleep(30)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                self.D8WAN.configure('interface HundredGigE0/6/0/0/0\n'
                                    'bundle id 12800 mode active\n'
                                    'interface FourHundredGigE0/5/0/32\n'
                                    'bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/5/0/33\n'
                                    'bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/6/0/1\n'
                                    'bundle id 12801 mode active\n'
                                    'interface FourHundredGigE0/0/0/20\n'
                                    'bundle id 12802 mode active\n'
                                    'interface FourHundredGigE0/5/0/35\n'
                                    'bundle id 12803 mode active\n'
                                    'interface HundredGigE0/6/0/0/3\n'
                                    'bundle id 12803 mode active\n', timeout=300)

            
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

            
                self.D8WAN.disconnect()
            
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



#@aetest.skip(reason='debug')
class TC10_INGRESS_REMOTE_LC_RELOAD(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC10.0-Ingress Remote LC Reload"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_LC_RELOAD######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Ingress Local LC Reload "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                try:
                    self.D8WAN.execute('reload location 0/5/CPU0 noprompt', timeout = 7200)
                except:
                    log.info("Lincard still reloading")
                    time.sleep(300)

            
                time.sleep(60)

                while True:
                    output = self.D8WAN.execute('sh platform | i 0/5/CPU0',timeout = 300)

                    if output.count('IOS XR RUN'):
                        log.info("Linecard is stable now")
                        break
                    else:
                        # If the list is empty, break out of the loop
                        log.info("Linecard is not stable yet")
                    time.sleep(30)




                log.info(banner("Checking Hardware Programming Error "))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
                time.sleep(10)
                self.controller.disconnect()

                log.info('Waiting 5 more mintures for the traffic to recover')
                time.sleep(300)

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

            
                self.D8WAN.disconnect()
            
            time.sleep(90)


            
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



#@aetest.skip(reason='debug')
class TC11_INGRESS_REMOTE_LC_SHUT_NOSHUT(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC11.0-Ingress Remote LC Shut NoShut"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D8WAN_LC_SHUT_NOSHUT######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Ingress Remote LC Shut NoShut"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                try:
                    self.D8WAN.configure('hw-module shutdown location 0/6/CPU0', timeout = 7200)
                except:
                    log.info("Lincard is shutting down")
                    time.sleep(300)

            
                time.sleep(60)

                try:
                    self.D8WAN.configure('no hw-module shutdown location 0/6/CPU0', timeout = 7200)
                except:
                    log.info("Lincard is booting")
                    time.sleep(300)

            
                time.sleep(60)

                while True:
                    output = self.D8WAN.execute('sh platform | i 0/6/CPU0',timeout = 300)

                    if output.count('IOS XR RUN'):
                        log.info("Linecard is stable now")
                        break
                    else:
                        # If the list is empty, break out of the loop
                        log.info("Linecard is not stable yet")
                    time.sleep(30)




                log.info(banner("Checking Hardware Programming Error "))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')



                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
                time.sleep(10)
                self.controller.disconnect()

                log.info('Waiting 5 more mintures for the traffic to recover')
                time.sleep(300)

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

            
                self.D8WAN.disconnect()
            
            time.sleep(90)


            
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



#@aetest.skip(reason='debug')
class TC12_INGRESS_REMOTE_ROUTER_RELOAD(aetest.Testcase):
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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC12.0-Ingress Remote Router Reload"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            ###################### D18WAN_LC_RELOAD######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Ingress Remote Router Reload "))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                try:
                    self.D8WAN.execute('reload location all noprompt', timeout = 7200)
                except:
                    log.info("Router still reloading")
                    time.sleep(300)

            
                time.sleep(600)

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')


                while True:
                    output = self.D8WAN.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN | ex UP',timeout = 300)
                    # Split the text after the "--------------------------------------------------------------------------------"
                    output_lines = output.split("--------------------------------------------------------------------------------")[1:]
                    # Clean up and remove leading/trailing whitespace
                    output_lines = [line.strip() for line in output_lines if line.strip()]
                    # Check if the list is empty and fail the test case if it's not
                    if output_lines:
                        log.info("Not all unit came up yet")
                    else:
                        # If the list is empty, break out of the loop
                        break
                    time.sleep(30)

                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_500X16_PB_ECMP_V4V6NH_8K.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
                time.sleep(10)
                self.controller.disconnect()

                log.info('Waiting 5 more mintures for the traffic to recover')
                time.sleep(300)

                log.info(banner("Checking Hardware Programming Error "))

                output = self.D8WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D8WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')


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

            
                self.D8WAN.disconnect()
            
            time.sleep(90)


            
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


#@aetest.skip(reason='debug')
class TC13_INVALID_NEXT_HOP_ADDRESS(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC13.0-Invalid next hop address"))



            ###################### Checing Swan agent communication with server ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Fib Programming include negative"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                output = self.controller.execute('gzip -c /root/MBB_MASTER/Incorrect_D18WAN_hostname.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')

                if output.count('DeviceName: D8WAN does not match Host: D18WAN'):
                    log.info('DeviceName: D8WAN does not match Host: D18WAN is seen')
                else:
                    self.failed('Command went through. It is not expected\n')


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()
                self.controller.disconnect()
            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC26_COMMUNICATION_WITH_SWAN_CONTROLLER(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC23.0-Communication with Swan Controller"))



            ###################### Checing Swan agent communication with server ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Checking Communication with Swan Controller"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                output = self.controller.execute('curl -v http://172.25.124.54:10000/version', timeout = 300)

                if output.count('HTTP/1.1 200 OK'):
                    log.info('HTTP/1.1 200 OK is seen')
                else:
                    self.failed('HTTP/1.1 200 OK is not seen\n')

                output = self.controller.execute('curl -v http://172.25.124.54:10000/flowtable', timeout = 300)

                if output.count('HTTP/1.1 200 OK'):
                    log.info('HTTP/1.1 200 OK is seen')
                else:
                    self.failed('HTTP/1.1 200 OK is not seen\n')

                output = self.controller.execute('curl -v http://172.25.124.54:10000/flowtable/summary', timeout = 300)

                if output.count('HTTP/1.1 200 OK'):
                    log.info('HTTP/1.1 200 OK is seen')
                else:
                    self.failed('HTTP/1.1 200 OK is not seen\n')

                output = self.controller.execute('curl -v http://172.25.124.54:10000/tunnels | wc -l', timeout = 300)

                if output.count('4001'):
                    log.info('Total 4005 tunnels')
                else:
                    self.failed('4001 tunnels are not seen\n')

                output = self.controller.execute('curl -v http://172.25.124.54:10000/instance/1/version', timeout = 300)

                if output.count('HTTP/1.1 200 OK'):
                    log.info('HTTP/1.1 200 OK is seen')
                else:
                    self.failed('HTTP/1.1 200 OK is not seen\n')




                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()
                self.controller.disconnect()
            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass



#@aetest.skip(reason='debug')
class TC27_DDoS_ATTACK_SURVIVAL_ON_PORT_10001_42000(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC27.0-DDOS attack survival on port 10001 42000"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Denying certain network under linux networking"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                self.D18WAN.execute('show run linux networking', timeout = 300)
                self.D18WAN.execute('sh run linux networking | file harddisk:/linux_networking_permit.cfg', timeout = 300)
                self.D18WAN.execute('sh run linux networking | e permit | file harddisk:linux_networking_deny.cfg', timeout = 300)


                log.info(banner("Denying Linux Networking"))

                self.D18WAN.configure('no linux networking', timeout=600)

                self.D18WAN.execute('show run linux networking', timeout = 300)

                self.D18WAN.configure('load harddisk:/linux_networking_deny.cfg', timeout=600)


                self.D18WAN.execute('show run linux networking | e permit', timeout = 300)



                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500CBF-V4+V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
                self.controller.disconnect()
                time.sleep(120)
                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')

                log.info(banner("Permitting Linux Networking"))

                self.D18WAN.configure('load harddisk:/linux_networking_permit.cfg', timeout=600)


                self.D18WAN.execute('show run linux networking', timeout = 300)


                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                self.controller.execute('gzip -c /root/MBB_MASTER/EXPLICIT_NULLV6_D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;', timeout = 300)
                self.controller.disconnect()
                time.sleep(30)
                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

                
#@aetest.skip(reason='debug')
class TC28_FIB_PROGRAMMING_INCLUDE_NEGATIVE(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC28.0-Fib Programming include negative"))



            ###################### Checing Swan agent communication with server ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Fib Programming include negative"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                output = self.controller.execute('gzip -c /root/MBB_MASTER/Incorrect_D18WAN_hostname.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')

                if output.count('DeviceName: D8WAN does not match Host: D18WAN'):
                    log.info('DeviceName: D8WAN does not match Host: D18WAN is seen')
                else:
                    self.failed('Command went through. It is not expected\n')


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()
                self.controller.disconnect()
            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC32_SWAN_AGENT_CRASH(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


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
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC32.0-SWAN Agent Crash"))

            ################################## Verifier_Before ################################
            Verifier_Before(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Kill Swanagent Process"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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
                self.D8WAN.disconnect()

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                self.D18WAN.execute('sh appmgr application-table', timeout = 300)
                output= self.D18WAN.execute('sh process cpu | i agentxr', timeout = 300)
                # Define a regular expression pattern to extract the first number after a newline
                pattern = r'\n(\d+)\s+'
                
                # Use re.search to find the first occurrence of the pattern in the output
                match = re.search(pattern, output)
                
                # Check if a match was found
                if match:
                    # Extract the first number from the match
                    swanagent_process = int(match.group(1))
                    log.info("Swan Agent Process Number: %s", swanagent_process)

                ######################### Crash the SwanAgent Process #########################

                self.D18WAN.execute('bash kill -9 ' + str(swanagent_process), timeout = 300)

                time.sleep(30)

                output = self.D18WAN.execute('sh appmgr application-table', timeout = 300)


                # Check if both "Activated" and "Up" keywords are found
                if output.count("Activated") > 0 and output.count("Up") > 0:
                    log.info('SwanAgent Recovered from Crash')


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                ################################## Connecting to Linux Box ###########################
                V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
                ##################################### Verifier_After ###################################
                Verifier_After(self.failed, steps, script_args, testscript, testbed, test_data, timing)

                log.info('Waiting 5 more minutes for all the traffic stream to converge')
                time.sleep(300)

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
class TC33_LSP_PROGRAMMING_TIME(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC33.0-LSP Programming Time"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: LSP Programming Time"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                output = self.D18WAN.execute('show appmgr application name SwanAgent logs | i Time in ms', timeout = 300)

                # Find all numbers (including decimal numbers) followed by "ms" in the output
                numbers = re.findall(r'(\d+(\.\d+)?)ms', output)

                # Get the last captured number (convert to float if found)
                lsp_programming_time = float(numbers[-1][0]) if numbers else None

                log.info("LSP Programming Time in ms: %s", lsp_programming_time)

                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC34_LABEL_STAT_VERIFICATION(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC34.0-Label Stat Verification"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Label Stat Verification"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                
                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')


                time.sleep(30)
                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')


                output = self.D18WAN.execute('show cef ipv6 3000::1 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+ [\w]+}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')



                output = self.D18WAN.execute('show mpls forwarding prefix 100.100.110.1/32 location 0/6/CPU0', timeout=300)

                if output.count('SR Pfx'):
                    self.failed('Traffic is using SR Path')
                else:
                    log.info('Traffic is using SWAN Path')


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass




#@aetest.skip(reason='debug')
class TC35_VERIFY_APPMGR_INFRA(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC35.0-Verify Appmgr Infra"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Verifying Appmgr Infra"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                self.D18WAN.execute('show appmgr application-table', timeout = 300)
                self.D18WAN.execute('show appmgr source-table', timeout = 300)
                self.D18WAN.execute('show appmgr packages installed', timeout = 300)
                self.D18WAN.execute('show appmgr process-script-table', timeout = 300)
                self.D18WAN.execute('show appmgr source name swanagent', timeout = 300)
                self.D18WAN.execute('show appmgr application name SwanAgent info detail', timeout = 300)
                self.D18WAN.execute('show appmgr application name SwanAgent info summary', timeout = 300)
                self.D18WAN.execute('show appmgr application name SwanAgent logs', timeout = 300)
                self.D18WAN.execute('show appmgr application name SwanAgent logs ', timeout = 300)
                self.D18WAN.execute('show appmgr application name SwanAgent stats', timeout = 300)
                




                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass




@aetest.skip(reason='debug')
class TC36_MULTI_INSTANCE_SWAN_PROGRAMMING(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC36.0-Multi Instance Swan Programming"))



            ###################### Checing Swan agent communication with server ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: push xml file for instance 0 & instance 1"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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


                ################ Connecting to D18WAN ################
                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                time.sleep(30)
                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')


                output = self.D18WAN.execute('show cef ipv6 3000::1 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+ [\w]+}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')



                output = self.D18WAN.execute('show mpls forwarding prefix 100.100.110.1/32 location 0/6/CPU0', timeout=300)

                if output.count('SR Pfx'):
                    log.info('Traffic is using SR Path')
                else:
                    log.info('Traffic is using SWAN Path')

                #self.D18WAN.disconnect()

                #########Connecting to SwanAgent###########
                log.info(banner("Connecting to Linux Box"))
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
                        failed('can not connect to controller sucessfully')
                self.controller.execute('unset http_proxy')
                self.controller.execute('unset https_proxy')
                output = self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-NONCBF-POP-10K.xml | curl -s -X POST http://172.25.124.54:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')



                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')


                output = self.D18WAN.execute('show mpls forwarding labels 54000 69999', timeout = 300)
                #
                #
                #
                # Need to put the check once xml is avaialble from Dhiren
                #
                #
                #
                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()
                self.controller.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass

#@aetest.skip(reason='debug')
class TC37_VRF_FWDING_ISSUE_CSCwb18777(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC37.0-VRF fwding issue CSCwb18777"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Verifying VRF fwding issue"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                self.D18WAN.execute('bash ifconfig | awk \'/^vethac100005/,/^$/\'', timeout=300)
                self.D18WAN.execute('bash ifconfig | awk \'/^vethac100001/,/^$/\'', timeout=300)
                self.D18WAN.execute('show ipv4 int brief | i Mgmt', timeout=300)
                self.D18WAN.execute('show run | i virtu', timeout=300)

                output = self.D18WAN.execute('bash docker ps -a', timeout=300)

                # Split the output into lines
                lines = output.strip().split('\n')

                # Initialize variables to store the container IDs
                container_id1 = None
                container_id2 = None

                # Iterate through the lines to find the container IDs for vrf-relay:latest
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "vrf-relay:latest":
                        container_id = parts[0]
                        if container_id1 is None:
                            container_id1 = container_id
                        else:
                            container_id2 = container_id
                log.info("Container ID 1: %s", container_id1)
                log.info("Container ID 2: %s", container_id2)

                output = self.D18WAN.execute('bash docker logs ' + str(container_id1), timeout = 300)

                # Use regular expression to find and capture the last IP address in the output
                ip_pattern = r"Reserving IP address pair: '[\d.]+/[\d]+' - '([\d.]+/[\d]+)'"
                matches = re.findall(ip_pattern, output)

                if matches:
                    # Get the last captured IP address
                    last_ip_address1 = matches[-1]

                log.info("Ip Address of Instance 1: %s", last_ip_address1)
                


                output = self.D18WAN.execute('bash docker logs ' + str(container_id2), timeout = 300)

                # Use regular expression to find and capture the last IP address in the output
                ip_pattern = r"Reserving IP address pair: '[\d.]+/[\d]+' - '([\d.]+/[\d]+)'"
                matches = re.findall(ip_pattern, output)

                if matches:
                    # Get the last captured IP address
                    last_ip_address2 = matches[-1]
                log.info("Ip Address of Instance 2: %s", last_ip_address2)

                if last_ip_address1 == last_ip_address2:
                    self.failed('Both instance using same ip')
                else:
                    log.info('Both Instances using different ip')


                output = self.D18WAN.execute('show cef ipv4 100.100.110.1/32 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+\}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')


                output = self.D18WAN.execute('show cef ipv6 3000::1 detail loca 0/0/cpu0 | i "Bundle-Ether|labels imposed" | e Y', timeout=300)
                # Define the regular expression pattern to capture "labels imposed"
                pattern = r'labels imposed \{[0-9]+ [0-9]+ [\w]+}'

                # Use re.findall to find all occurrences of the pattern in the output
                matches = re.findall(pattern, output)

                # Check if "labels imposed" appears four times
                if len(matches) == 4:
                    log.info('Traffic is using SWAN Path')
                    # Print the labels imposed values
                    for match in matches:
                        log.info("Total Number of label imposed: %s", match)
                else:
                    log.info('Traffic is using SR Path')



                output = self.D18WAN.execute('show mpls forwarding prefix 100.100.110.1/32 location 0/6/CPU0', timeout=300)

                if output.count('SR Pfx'):
                    log.info('Traffic is using SR Path')
                else:
                    log.info('Traffic is using SWAN Path')


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class TC38_SWAN_AGENT_Reload(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):


            ################################## Connecting to Linux Box ###########################
            V4_Controller(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            
            log.info(banner("TC32.0-SWAN Agent Reload"))


            ###################### Crashing SwanAgent Process ######################

            if 'beloop' in test_data:
                self.beloop = test_data['beloop']
            else:
                self.beloop = 1
            for beloop in range(int(self.beloop)):
                log.info(banner(f"Loop number: {beloop}"))

                log.info(banner("Trigger: Reload Swanagent Process"))


                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D8WAN = genietestbed.devices['D8WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D8WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')

                

                self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
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

                testbed_file = testbed.testbed_file
                genietestbed = load(testbed_file)
                log.info(genietestbed.devices)
                self.D18WAN = genietestbed.devices['D18WAN']
                retry = 0
                while retry < 10:
                    try:
                        self.D18WAN.connect(via='vty', connection_timeout=600, mit=True)
                        break
                    except:
                        time.sleep(300)
                        retry += 1
                        if retry == 10:
                            log.failed('connect failed')



                self.D18WAN.execute('sh appmgr application-table', timeout = 300)
                output= self.D18WAN.execute('sh process cpu | i agentxr', timeout = 300)
                # Define a regular expression pattern to extract the first number after a newline
                pattern = r'\n(\d+)\s+'
                
                # Use re.search to find the first occurrence of the pattern in the output
                match = re.search(pattern, output)
                
                # Check if a match was found
                if match:
                    # Extract the first number from the match
                    swanagent_process = int(match.group(1))
                    log.info("Swan Agent Process Number: %s", swanagent_process)

                ######################### Reload the SwanAgent Process #########################

                self.D18WAN.execute('appmgr application stop name SwanAgent', timeout = 300)


                output = self.D18WAN.execute('sh appmgr application-table', timeout = 300)
                # Check if both "Activated" and "Up" keywords are found
                if output.count("Exited") > 0 and output.count("seconds") > 0:
                    log.info('SwanAgent Rloaded')

                time.sleep(10)

                self.D18WAN.execute('appmgr application start name SwanAgent', timeout = 300)

                time.sleep(10)
                output = self.D18WAN.execute('sh appmgr application-table', timeout = 300)


                # Check if both "Activated" and "Up" keywords are found
                if output.count("Activated") > 0 and output.count("seconds") > 0:
                    log.info('SwanAgent Rloaded')


                log.info(banner("Checking Hardware Programming Error"))

                output = self.D18WAN.execute('show logging | in HW_PROG_ERROR', timeout = 300)

                if output.count('HW_PROG_ERROR'):
                    self.failed('Hardware Programming Error Found\n')

                log.info(banner("Checking Out of Resource Error"))
                output = self.D18WAN.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)

                if output.count('OOR_RED'):
                    self.failed('Out of Resource Error Found\n')
                

                time.sleep(10)

                log.info(banner("Testcase ENDS"))

            
                self.D8WAN.disconnect()
                self.D18WAN.disconnect()

            
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

        args = {}
        args['timeout'] = 300
        args['sste_commands'] = ["no logging container fetch-timestamp"]
        sste_common.config_commands(module_args, script_args)

        args = {}
        args['timeout'] = 300
        args['sste_commands'] = ["no logging container all"]
        sste_common.config_commands(module_args, script_args)

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

            