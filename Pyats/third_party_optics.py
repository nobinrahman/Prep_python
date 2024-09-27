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

        testscript.parameters['script_args']['testsuitename'] = "Third Party Optics SOFT OIR Test"
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
class Third_Party_OPT_SWOIR_400G(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):    
            log.info(banner("Third Party 400G OPTICS SOFT OIR TEST"))

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

            output = self.router.execute('show inventory | i Non-Cisco | i 400G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 400G interfaces
            count_non_cisco_400G_before = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "400G" in line:
                    count_non_cisco_400G_before += 1
            # Print the total number of non-Cisco 400G interfaces
            #print("Total Non-Cisco 400G Interfaces Before:", count_non_cisco_400G_before)
            log.info("Total Non-Cisco 400G Interfaces Before: %d", count_non_cisco_400G_before)

            lines = output.strip().split("\n")

            interface_list = []
            unique_interface_set = set()
            
            for line in lines:
                if "NAME:" in line:
                    parts = line.split(", ")
                    interface_name = parts[0].split(":")[1].strip(' "')
                    interface_desc = parts[1].split(":")[1].strip(' "')
                    
                    if interface_desc not in unique_interface_set:
                        #unique_interface_set.add(interface_desc)
                        # Removing the prefix "FourHundredGig"
                        interface_name = interface_name.replace("FourHundredGigE", "")
                        interface_list.append(interface_name)
            
            #print("Unique_400G_Interface =", interface_list)
            log.info("Unique_400G_Interface = %d", interface_list)

            # Check if the interface_list is empty
            if not interface_list:
                self.failed('400G Non-Cisco Optic is not present in this DUT')


            else:
                for interface in interface_list:
                    parts = interface.split('/')
                    lc_number = parts[1]
                    interface_number = parts[3]
                    
                    print("LC Number =", lc_number)

                    print("Interface Number =", interface_number)

    
                    output = self.router.execute('sh interface FourHundredGigE' + interface + ' brief', timeout = 300)

                    if output.count('down        down'):
                        self.failed('Interface need to be in up/up state to begin OIR')
    
                    #log.info(banner("Removing Interface"))
                    log.info(banner(f"Removing Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 0\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)
                    time.sleep(30)
                    log.info('Optic removal is completed' )
    
                    output = self.router.execute('sh interface FourHundredGigE' + interface + ' brief', timeout = 300)
    
    
                    #log.info(banner("Inserting Interface"))
                    log.info(banner(f"Inserting Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 1\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)

                    log.info('Optic insertion is completed\n') 


                    log.info('Waiting 120s for the Interface to come up') 

                    time.sleep(120)

                    log.info(banner("Interface status check after trigger"))
                    output = self.router.execute('sh interface FourHundredGigE' + interface + ' brief', timeout = 300)
                    
                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')
                    else:
                        log.info('OPTICS is not in UP/UP State')
                        self.failed('OPTICS is not in UP/UP State')

                    log.info(banner("Bundle status check after trigger"))

                    output = self.router.execute('show run interface FourHundredGigE' + interface , timeout = 300)

                    # Define a regular expression pattern to capture the bundle-id number
                    pattern = r'bundle id (\d+)'

                    # Search for the pattern in the output
                    match = re.search(pattern, output)
                    bundle_id = match.group(1)
                    print("Bundle ID:", bundle_id)

                    output = self.router.execute('sh interface bundle-Ether' + bundle_id + ' brief', timeout = 300)

                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')

                    else:
                        log.info('Bundle is not in UP/UP State')
                        self.failed('Bundle is not in UP/UP State')

                    log.info(banner("Checking Hardware Programming Error"))
                    output = self.router.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                    if output.count('HW_PROG_ERROR'):
                        self.failed('Hardware Programming Error Found\n')
                    log.info(banner("Checking Out of Resource Error"))
                    output = self.router.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)
                    if output.count('OOR_RED'):
                        self.failed('Out of Resource Error Found\n')
                    time.sleep(10)

            log.info(banner("Matching inventory before and after trigger"))
            output = self.router.execute('show inventory | i Non-Cisco | i 400G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 400G interfaces
            count_non_cisco_400G_after = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "400G" in line:
                    count_non_cisco_400G_after += 1
            # Print the total number of non-Cisco 400G interfaces
            log.info("Total Non-Cisco 400G Interfaces Before: %d", count_non_cisco_400G_before)
            #print("Total Non-Cisco 400G Interfaces Before :", count_non_cisco_400G_before)
            log.info("Total Non-Cisco 400G Interfaces After: %d", count_non_cisco_400G_after)
            #print("Total Non-Cisco 400G Interfaces After :", count_non_cisco_400G_after)

            if count_non_cisco_400G_before == count_non_cisco_400G_after:
                log.info('All Interfaces showing up in the inventory')
            else:
                self.failed('Inventory does not match after trigger\n')

            self.router.disconnect()

        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class Third_Party_OPT_SWOIR_100G(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):    
            log.info(banner("Third Party 100G OPTICS SOFT OIR TEST"))

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

            output = self.router.execute('show inventory | i Non-Cisco | i 100G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 100G interfaces
            count_non_cisco_100G_before = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "100G" in line:
                    count_non_cisco_100G_before += 1
            # Print the total number of non-Cisco 100G interfaces
            #print("Total Non-Cisco 100G Interfaces Before:", count_non_cisco_100G_before)
            log.info("Total Non-Cisco 100G Interfaces Before: %d", count_non_cisco_100G_before)

            lines = output.strip().split("\n")

            interface_list = []
            unique_interface_set = set()
            
            for line in lines:
                if "NAME:" in line:
                    parts = line.split(", ")
                    interface_name = parts[0].split(":")[1].strip(' "')
                    interface_desc = parts[1].split(":")[1].strip(' "')
                    
                    if interface_desc not in unique_interface_set:
                        #unique_interface_set.add(interface_desc)
                        # Removing the prefix "FourHundredGig"
                        interface_name = interface_name.replace("HundredGigE", "")
                        interface_list.append(interface_name)
            
            #print("Unique_100G_Interface =", interface_list)
            log.info("Unique_100G_Interface = %d", interface_list)

            # Check if the interface_list is empty
            if not interface_list:
                self.failed('100G Non-Cisco Optic is not present in this DUT')
            else:
                for interface in interface_list:
                    parts = interface.split('/')
                    lc_number = parts[1]
                    interface_number = parts[3]
                    
                    print("LC Number =", lc_number)
                    print("Interface Number =", interface_number)

    
                    output = self.router.execute('sh interface HundredGigE' + interface + ' brief', timeout = 300)

                    if output.count('down        down'):
                        self.failed('Interface need to be in up/up state to begin OIR')
    
                    #log.info(banner("Removing Interface"))
                    log.info(banner(f"Removing Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 0\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)
                    time.sleep(30)
                    log.info('Optic removal is completed' )
    
                    output = self.router.execute('sh interface HundredGigE' + interface + ' brief', timeout = 300)
    
    
                    #log.info(banner("Inserting Interface"))
                    log.info(banner(f"Inserting Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 1\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)

                    log.info('Optic insertion is completed\n') 


                    log.info('Waiting 120s for the Interface to come up') 

                    time.sleep(120)

                    log.info(banner("Interface status check after trigger"))
                    output = self.router.execute('sh interface HundredGigE' + interface + ' brief', timeout = 300)
                    
                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')
                    else:
                        log.info('OPTICS is not in UP/UP State')
                        self.failed('OPTICS is not in UP/UP State')

                    log.info(banner("Bundle status check after trigger"))

                    output = self.router.execute('show run interface HundredGigE' + interface , timeout = 300)

                    # Define a regular expression pattern to capture the bundle-id number
                    pattern = r'bundle id (\d+)'

                    # Search for the pattern in the output
                    match = re.search(pattern, output)
                    bundle_id = match.group(1)
                    print("Bundle ID:", bundle_id)

                    output = self.router.execute('sh interface bundle-Ether' + bundle_id + ' brief', timeout = 300)

                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')

                    else:
                        log.info('Bundle is not in UP/UP State')
                        self.failed('Bundle is not in UP/UP State')

                    log.info(banner("Checking Hardware Programming Error"))
                    output = self.router.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                    if output.count('HW_PROG_ERROR'):
                        self.failed('Hardware Programming Error Found\n')
                    log.info(banner("Checking Out of Resource Error"))
                    output = self.router.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)
                    if output.count('OOR_RED'):
                        self.failed('Out of Resource Error Found\n')
                    time.sleep(10)

            log.info(banner("Matching inventory before and after trigger"))
            output = self.router.execute('show inventory | i Non-Cisco | i 100G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 100G interfaces
            count_non_cisco_100G_after = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "100G" in line:
                    count_non_cisco_100G_after += 1
            # Print the total number of non-Cisco 100G interfaces
            log.info("Total Non-Cisco 100G Interfaces Before: %d", count_non_cisco_100G_before)
            #print("Total Non-Cisco 100G Interfaces Before :", count_non_cisco_100G_before)
            log.info("Total Non-Cisco 100G Interfaces After: %d", count_non_cisco_100G_after)
            #print("Total Non-Cisco 100G Interfaces After :", count_non_cisco_100G_after)

            if count_non_cisco_100G_before == count_non_cisco_100G_after:
                log.info('All Interfaces showing up in the inventory')
            else:
                self.failed('Inventory does not match after trigger\n')

            self.router.disconnect()

        if check_context(script_args):
            self.failed('crash happened\n')
        pass


#@aetest.skip(reason='debug')
class Third_Party_OPT_SWOIR_40G(aetest.Testcase):
    global coredump_list, showtech_list, interface_list

    @aetest.test
    def Node1_trigger(self, steps, script_args, testscript,testbed, test_data, timing):


        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):    
            log.info(banner("Third Party 40G OPTICS SOFT OIR TEST"))

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

            output = self.router.execute('show inventory | i Non-Cisco | i 40G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 40G interfaces
            count_non_cisco_40G_before = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "40G" in line:
                    count_non_cisco_40G_before += 1
            # Print the total number of non-Cisco 40G interfaces
            #print("Total Non-Cisco 40G Interfaces Before:", count_non_cisco_40G_before)
            log.info("Total Non-Cisco 40G Interfaces Before: %d", count_non_cisco_40G_before)

            lines = output.strip().split("\n")

            interface_list = []
            unique_interface_set = set()
            
            for line in lines:
                if "NAME:" in line:
                    parts = line.split(", ")
                    interface_name = parts[0].split(":")[1].strip(' "')
                    interface_desc = parts[1].split(":")[1].strip(' "')
                    
                    if interface_desc not in unique_interface_set:
                        #unique_interface_set.add(interface_desc)
                        # Removing the prefix "FourHundredGig"
                        interface_name = interface_name.replace("FortyGigE", "")
                        interface_list.append(interface_name)
            
            #print("Unique_40G_Interface =", interface_list)
            log.info("Unique_40G_Interface = %d", interface_list)

            # Check if the interface_list is empty
            if not interface_list:
                self.failed('40G Non-Cisco Optic is not present in this DUT')
            else:
                for interface in interface_list:
                    parts = interface.split('/')
                    lc_number = parts[1]
                    interface_number = parts[3]
                    
                    print("LC Number =", lc_number)

                    print("Interface Number =", interface_number)

    
                    output = self.router.execute('sh interface FortyGigE' + interface + ' brief', timeout = 300)

                    if output.count('down        down'):
                        self.failed('Interface need to be in up/up state to begin OIR')
    
                    #log.info(banner("Removing Interface"))
                    log.info(banner(f"Removing Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 0\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)
                    time.sleep(30)
                    log.info('Optic removal is completed' )
    
                    output = self.router.execute('sh interface FortyGigE' + interface + ' brief', timeout = 300)
    
    
                    #log.info(banner("Inserting Interface"))
                    log.info(banner(f"Inserting Interface - {interface}"))
                    self.router.send('attach location 0/' + lc_number + '/CPU0\n')
                    time.sleep(3)
                    self.router.send('optics_srv_client -C oir -c 0 -P ' + interface_number + ' -d 1\n')
                    time.sleep(3)
                    self.router.send('exit\n')
                    # time.sleep(120)

                    log.info('Optic insertion is completed\n') 


                    log.info('Waiting 120s for the Interface to come up') 

                    time.sleep(120)

                    log.info(banner("Interface status check after trigger"))
                    output = self.router.execute('sh interface FortyGigE' + interface + ' brief', timeout = 300)
                    
                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')
                    else:
                        log.info('OPTICS is not in UP/UP State')
                        self.failed('OPTICS is not in UP/UP State')

                    log.info(banner("Bundle status check after trigger"))

                    output = self.router.execute('show run interface FortyGigE' + interface , timeout = 300)

                    # Define a regular expression pattern to capture the bundle-id number
                    pattern = r'bundle id (\d+)'

                    # Search for the pattern in the output
                    match = re.search(pattern, output)
                    bundle_id = match.group(1)
                    print("Bundle ID:", bundle_id)

                    output = self.router.execute('sh interface bundle-Ether' + bundle_id + ' brief', timeout = 300)

                    if output.count('up          up'):
                        log.info('OPTICS is in UP/UP State')

                    else:
                        log.info('Bundle is not in UP/UP State')
                        self.failed('Bundle is not in UP/UP State')

                    log.info(banner("Checking Hardware Programming Error"))
                    output = self.router.execute('show logging | in HW_PROG_ERROR', timeout = 300)
                    if output.count('HW_PROG_ERROR'):
                        self.failed('Hardware Programming Error Found\n')
                    log.info(banner("Checking Out of Resource Error"))
                    output = self.router.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)
                    if output.count('OOR_RED'):
                        self.failed('Out of Resource Error Found\n')
                    time.sleep(10)

            log.info(banner("Matching inventory before and after trigger"))
            output = self.router.execute('show inventory | i Non-Cisco | i 40G', timeout = 300)

            # Checking the total number of interfaces in inventory

            output_lines = output.split('\n')

            # Initialize a counter for non-Cisco 40G interfaces
            count_non_cisco_40G_after = 0

            # Iterate through each line and count the relevant interfaces
            for line in output_lines:
                if "Non-Cisco" in line and "40G" in line:
                    count_non_cisco_40G_after += 1
            # Print the total number of non-Cisco 40G interfaces
            log.info("Total Non-Cisco 40G Interfaces Before: %d", count_non_cisco_40G_before)
            #print("Total Non-Cisco 40G Interfaces Before :", count_non_cisco_40G_before)
            log.info("Total Non-Cisco 40G Interfaces After: %d", count_non_cisco_40G_after)
            #print("Total Non-Cisco 40G Interfaces After :", count_non_cisco_40G_after)

            if count_non_cisco_40G_before == count_non_cisco_40G_after:
                log.info('All Interfaces showing up in the inventory')
            else:
                self.failed('Inventory does not match after trigger\n')

            self.router.disconnect()

        if check_context(script_args):
            self.failed('crash happened\n')
        pass

@aetest.skip(reason='debug')
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