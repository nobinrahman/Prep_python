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
from genie.testbed import load
from stcrestclient import stchttp

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
from ats.log.utils import banner
from pyats.aetest.loop import Iteration
import time
from texttable import Texttable
from genie.utils import Dq




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
ios_xr_run_count1 = 10
operational_count1 = 10
interface_up_count1 = 10

def Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data):
    step_txt = "Take_traffic_snapshot_before_trigger"
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
    step_txt = "Take_traffic_snapshot_after_trigger"
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
                        log.error(banner("One or more traffic streams not converge"))
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



#@aetest.skip(reason='debug')
class system_stability_check_before(aetest.Testcase):

    @aetest.test
    def test(self, steps, script_args, testbed, test_data, timing,testscript):


        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)
        self.router.execute('show version',timeout = 300)
        self.router.execute('clear context',timeout = 300)
        self.router.execute('show inventory',timeout = 300)
        self.router.execute('show install log',timeout = 300)
        self.router.execute('show install active',timeout = 300)
        self.router.execute('show install committed',timeout = 300)
        self.router.execute('show run',timeout = 300)
        self.router.execute('show log',timeout = 300)
        self.router.execute('dir harddisk:/',timeout = 300)
        self.router.execute('show media',timeout = 300)
        self.router.execute('show hw-module fpd')
        self.router.execute('show platform',timeout = 300)
        self.router.execute('show redundancy',timeout = 300)
        self.router.execute('show interface summary',timeout = 300)
        self.router.execute('show interface description',timeout = 300)
        self.router.execute('show bundle',timeout = 300)
        self.router.execute('show route summary',timeout = 300)
        self.router.execute('show route ipv6 summary',timeout = 300)
        self.router.execute('show mpls traffic-eng tunnels summary',timeout = 300)
        self.router.execute('show isis neighbors',timeout = 300)
        self.router.execute('show isis database summary',timeout = 300)
        output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN',timeout = 300)
        # Split the text after the "--------------------------------------------------------------------------------"
        output_lines = output.split("--------------------------------------------------------------------------------")[1:]
        # Clean up and remove leading/trailing whitespace
        output_lines = [line.strip() for line in output_lines if line.strip()]
        # Check if the list is not empty and fail the test case if it's not
        if output_lines:
            self.failed('System is not stable')

        output = self.router.execute('sh platform',timeout = 300)
        # Count occurrences of keywords
        global ios_xr_run_count1
        global operational_count1
        ios_xr_run_count1 = output.count("IOS XR RUN")
        operational_count1 = output.count("OPERATIONAL")
        log.info(f"Count of 'IOS XR RUN' before upgrade: {ios_xr_run_count1}")
        log.info(f"Count of 'OPERATIONAL' before upgrade: {operational_count1}")

        output = self.router.execute('show interface summary',timeout = 300)

        # Extract the value under the "UP" column
        match = re.search(r"ALL TYPES\s+\d+\s+(\d+)", output)
        global interface_up_count1
        interface_up_count1 = int(match.group(1))
        log.info("Total number of interface in UP state before upgrade: %s", interface_up_count1)
        

        self.router.destroy()
        self.router.disconnect()
#@aetest.skip(reason='debug')
class upgrade(aetest.Testcase):

    @aetest.test
    def test(self, steps, script_args, testbed, test_data, timing,testscript):

        skip_copy = 0
        if 'skip_copy' in test_data:
            skip_copy = test_data['skip_copy']

        commit_force = 0
        if 'commit_force' in test_data:
            commit_force = test_data['commit_force']

        log.info('script_args[\'os_type\']:')
        log.info(script_args['os_type'])

        if 'direct_path' in test_data:
            self.direct_path = test_data['direct_path']
        else:
            self.failed('need -direct_path')

        log.info(test_data)

        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)
        version0 = ''
        version1 = ''
        self.router.execute('clear context')

        output = self.router.execute('show version')
        # Split the text by lines
        lines = output.splitlines()
        # Find the line containing "Label" and extract the version label
        for line in lines:
            if "Label" in line:
                version0 = line.split(":")[1].strip()
                log.info("Version: %s", version0)
                break
        if 'iso' in test_data:
            self.iso = test_data['iso']
        else:
            self.failed('need -iso')

        # Find the start and end positions of the substring
        start = self.iso.find("8000-goldenk9-x64-") + len("8000-goldenk9-x64-")
        end = self.iso.find(".iso")
        
        # Extract the desired substring
        result = self.iso[start:end]
        log.info("Current Iso from Jenkins: %s", result)

        if version0 != result:
            self.failed('DUT needs to be on correct image\n')

        
        self.router.execute('show install active summary',timeout = 300)
        
        output = self.router.execute('show media | i "Avail|harddisk"',timeout = 300)
        lines = output.split('\n')

        # Find the line that contains "harddisk:"
        for line in lines:
            if "harddisk:" in line:
                # Split the line into words and extract the "Avail" value
                words = line.split()
                avail_value = words[-1]
                # Check if the "Available Value" is not more than 5G
                if int(avail_value[:-1]) <= 5:
                    self.failed('DUT do not have enough space\n')
                else:
                    log.info("Have enough space to perform Install operation")

        

        if 'direct_path' in test_data:
            self.direct_path = test_data['direct_path']
        else:
            self.failed('need -direct_path')

        isoname = self.direct_path.split('/')[-1]
        log.info('upgrade info: ' + isoname)

        if skip_copy == 1:
            output = self.router.execute('dir harddisk:')
            if output.count('isoname') == 0:
                self.failed('there is no iso file under harddisk with skip_copy 1 : ' + isoname)

        #MD5 verification 
        log.info(banner("MD5 Check"))
        self.router.execute('cd harddisk:/',timeout = 300)
        output = self.router.execute('run md5sum ' + isoname,timeout = 300)
        time.sleep(5)
        log.info("MD5sum: %s", output)


        log.info(banner("Clearing configuration inconsitency"))
        self.router.execute('clear configuration inconsistency', timeout = 300)


        # FPD Check
        log.info(banner("FPD Config Check"))
        output = self.router.execute('show run fpd auto-upgrad', timeout = 300)
        # Check if "fpd auto-upgrade enable" is present in the output using .find()
        if 'fpd auto-upgrade enable' not in output:
            self.failed('fpd auto-upgrade enable is not configured\n')

        if output.find("fpd auto-upgrade enable") != -1:
            # Save it in a variable
            fpd_auto_upgrade = "fpd auto-upgrade enable"

        output = self.router.execute('sh hw-module fpd | e NOT READY', timeout = 300)
        lines = output.split('\n')
        # Initialize an empty list to store the "CURRENT" values
        status_values = []


        # Iterate through the lines and look for lines containing "CURRENT"
        for line in lines:
            if "CURRENT" in line:
                # Split the line by whitespace
                elements = line.split()
                # Find the element that contains "CURRENT" and append it to status_values
                for element in elements:
                    if "CURRENT" in element:
                        status_values.append(element)
        # Check if any value other than "CURRENT" is found
        if any(value != "CURRENT" for value in status_values):
            self.failed('FPD Status is Not Current\n')



        # Controller Fabric Plane Check
        log.info(banner("Controller Fabric Plane Check"))
        output = self.router.execute('show controller fabric plane all', timeout = 300) 

        # Split the output into lines
        controller = output.splitlines()
        # Initialize a variable to count the "UP" occurrences
        up_count = 0



        # Iterate through the lines and count the "UP" occurrences in the Admin and Plane State columns
        for line in controller:
            if "UP" in line:
                up_count += line.count("UP")

        # Check if there are a total of 16 entries with "UP" keyword
        if up_count != 16:
            self.failed('Admin State and Plane state are not in UP/UP state\n')

        ############################################START OF ISOLATING THE DEVICE##############################
        # Isolating the device from network
        log.info(banner("Isolating the device from network"))
        bgpconfig = self.router.execute('sh run router bgp | i "router bgp | neighbor-group" | e use', timeout = 300)
        # Split the output into lines and iterate through them
        lines = bgpconfig.split('\n')

        # Initialize variables to store BGP and neighbor-group info
        as_number = ''
        neighbor_groups = []

        # Iterate through lines to extract BGP and neighbor-group info
        for line in lines:
            if line.startswith("router bgp"):
                as_number = line.split(" ")[-1]
                log.info('####BGP AS_number' + as_number)
            elif line.startswith(" neighbor-group"):
                neighbor_group_info = line.split(" ")[-1]
                log.info('####Neighbor_GROUP' + neighbor_group_info)
                neighbor_groups.append(neighbor_group_info)




        # Generate configuration commands for each neighbor-group
        for neighbor_group in neighbor_groups:
            self.router.configure('router bgp ' + as_number + '\n'
                                    'neighbor-group ' + neighbor_group + '\n'
                                    'graceful-maintenance as-prepends 6\n'
                                    'graceful-maintenance activate\n', timeout=300)




        ############################################END OF ISOLATING THE DEVICE##############################





        # Clearing configuration inconsitency
        log.info(banner("Clearing configuration inconsitency"))
        self.router.execute('clear configuration inconsistency', timeout = 300)
        time.sleep(10)


        #############################################Upgrading to New Image Start#############################################
        log.info(banner("Install Replace Action"))
        
        try:
            self.router.execute('install replace harddisk:/' + isoname + ' noprompt commit', timeout = 7200)
        except:
            log.info("Install Replace operation still going on")
            time.sleep(300)
        #############################################Upgrading to New Image End#############################################
        time.sleep(900)
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)
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
        

        
        output = self.router.execute('show configuration failed startup')

        output = self.router.execute('show hw-module fpd')


        # Split the text into lines
        lines = output.split('\n')
        
        # Initialize an empty list to store the "CURRENT" values
        current_values = []
        
        # Iterate through the lines and look for lines containing "CURRENT"
        for line in lines:
            if "CURRENT" in line:
                # Split the line by whitespace and get the last element (which is "CURRENT")
                elements = line.split()
                
                current_value = elements[-3]
                
                current_values.append(current_value)

        if all(value != "CURRENT" for value in current_values):
            self.failed('FPD STATUS IS NOT CURRENT\n')

        log.info(banner("Verify VMs and interfaces "))
        self.router.execute('show interface summary', timeout = 300)

        log.info(banner("Checking Software Version "))
        output = self.router.execute('show version', timeout = 300)
        # Split the text by lines
        lines = output.splitlines()
        # Find the line containing "Label" and extract the version label
        for line in lines:
            if "Label" in line:
                version0 = line.split(":")[1].strip()
                break

        # Find the start and end positions of the substring
        start = isoname.find("8000-goldenk9-x64-") + len("8000-goldenk9-x64-")
        end = isoname.find(".iso")
        
        # Extract the desired substring
        result = isoname[start:end]

        if version0 != result:
            self.failed('DUT did not install correct image\n')
        time.sleep(30)

        self.router.execute('show install active summary', timeout = 300)
        self.router.execute('show install commit summary', timeout = 300)
        self.router.execute('show install fixes committed', timeout = 300)

        while 1:
            output = self.router.execute('show install request', timeout = 300)
            time.sleep(5)
            if output.count('No install operation in progress') or output.count('Success'):
                break

        log.info(banner("Clearing configuration inconsitency"))
        self.router.execute('clear configuration inconsistency', timeout = 300)
        time.sleep(10)
        

        while True:
            output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN | ex UP | ex POWERED_OFF | ex FAILED',timeout = 300)
            # Split the text after the "--------------------------------------------------------------------------------"
            output_lines = output.split("--------------------------------------------------------------------------------")[1:]
            # Clean up and remove leading/trailing whitespace
            output_lines = [line.strip() for line in output_lines if line.strip()]
            # Check if the list is empty and fail the test case if it's not
            if output_lines:
                log.info("Not all the unit came up yet")
            else:
                # If the list is empty, break out of the loop
                break
            time.sleep(15)

        ##################################################FPD DOWNGRADE START#############################################

        #Force FPD Downgrade
        
        if 'fpd_force' in test_data:
            self.fpd_force = test_data['fpd_force']
        else:
            log.info("FPD Force downgrade is not selected")

        if int(self.fpd_force) == 1:
            log.info(banner("Force FPD Downgrade"))
            self.router.execute('upgrade hw-module location all fpd all force', timeout = 300)
            time.sleep(300)
            while 1:
                output = self.router.execute('show hw-module fpd', timeout = 300)
                time.sleep(30)

                # Split the text into lines
                lines = output.split('\n')
                
                # Initialize an empty list to store the "CURRENT" values
                status_values = []
        
        
                # Iterate through the lines and look for lines containing "CURRENT"
                for line in lines:
                    if "%" in line:
                        # Split the line by whitespace
                        elements = line.split()
                        # Find the element that contains "CURRENT" and append it to status_values
                        for element in elements:
                            if "%" in element:
                                status_values.append(element)
                        

                        # Check if the list is empty
                if not status_values:
                    break

            log.info(banner("Reload Operation"))
        
            try:
                self.router.execute('reload location all', timeout = 7200)
            except:
                log.info("Reload in Progress")
                time.sleep(300)
            time.sleep(600)



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
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


            while True:

                output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN',timeout = 300)
                # Split the text after the "--------------------------------------------------------------------------------"
                output_lines = output.split("--------------------------------------------------------------------------------")[1:]
                # Clean up and remove leading/trailing whitespace
                output_lines = [line.strip() for line in output_lines if line.strip()]
                # Check if the list is not empty 
                if output_lines:
                    log.info("Not all the unit came up yet")
                else:
                    # If the list is empty, break out of the loop
                    break
                
                time.sleep(10)

        output = self.router.execute('sh hw-module fpd | e CURRENT | e NOT READY',timeout = 300)
        # Split the text after the "-------------------------------------------------------------------------------------------------"
        output_lines = output.split("-------------------------------------------------------------------------------------------------")[1:]
        # Clean up and remove leading/trailing whitespace
        output_lines = [line.strip() for line in output_lines if line.strip()]
        # Check if the list is not empty and fail the test case if it's not
        if output_lines:
            self.failed('FPD is not current')


        ##################################################FPD DOWNGRADE END#############################################



        ##################################################ZTP CHECK START#############################################
        ztp_check = 0
        if 'ztp_check' in test_data:
            ztp_check = int(test_data['ztp_check'])
        if ztp_check == 1:
            
            log.info(banner("ZTP CHECK"))

            self.router.execute('show version')
            output = self.router.execute('show run | i ztp')
            if output.count('ztp'):
                log.error('\nztp is configured')
                #self.failed('ztp is configured\n')

            output = self.router.execute('run cat /pkg/etc/giso_ztp.ini | grep start')
            if output.count('False'):
                log.info('start value is False')
            else:
                self.failed('start value is not False\n')
            
            self.router.execute('run cat /pkg/etc/giso_ztp.ini')

            output = self.router.execute('show log | i ztp')
            if output.count('ZTP is not configured to run'):
                log.info('ZTP is not configured to run is found in the log')
            else:
                self.failed('ZTP is not configured to run is not found in the log\n')


            output = self.router.execute('show log | i ztp')
            if output.count('ZTP exited'):
                log.info('ZTP exited is found in the log')
            else:
                self.failed('ZTP exited is not found in the log\n')


            output = self.router.execute('run tail /var/log/ztp.log')
            if output.count('Valid giso ini file found') == 0 or output.count('ZTP is not configured to start') == 0 or output.count('Exiting SUCCESSFULLY') == 0 or output.count('ZTP Exited') == 0:
                self.failed('ZTP check failed\n')

            else:
                log.info('ztp ini check skipped')


            ####################### Execute Repave and Verify ZTP again #####################

            self.router.configure('load harddisk:/backup_cli.cfg', replace=True, timeout=600)
            self.router.execute('clear configuration inconsistency', timeout=600)
            try:
                self.router.execute('reload location all', timeout = 7200)
            except:
                log.info("Reload in Progress")
                time.sleep(300)
            time.sleep(600)



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
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

            self.router.execute('run cat /pkg/etc/giso_ztp.ini')

            output = self.router.execute('show log | i ztp')
            if output.count('ZTP is not configured to run'):
                log.info('ZTP is not configured to run is found in the log')
            else:
                self.failed('ZTP is not configured to run is not found in the log\n')


            output = self.router.execute('show log | i ztp')
            if output.count('ZTP exited'):
                log.info('ZTP exited is found in the log')
            else:
                self.failed('ZTP exited is not found in the log\n')

        ##################################################ZTP CHECK END#############################################

        output = self.router.execute('show logging | in dumper', timeout = 300)
        if output.count('dumper'):
            log.error('\ncrash may happened, check the dumper info')
            return True
        output = self.router.execute('show logging | in Traceback', timeout = 300)
        if output.count('Traceback'):
            log.error('\ncrash may happened, check the Traceback info')
            return True
        
        output = self.router.execute('show logging | in ONLINE_DIAG_FAIL', timeout = 300)
        if output.count('ONLINE_DIAG_FAIL'):
            log.error('\nOnline Diag Failed message seen in log')
            return True

        output = self.router.execute('show context', timeout = 300)
        if output.count('node:') != output.count('No context'):
            log.error('\ncrash may happened, check the show context info')
            return True
        return False



        self.router.destroy()
        self.router.disconnect()

#@aetest.skip(reason='debug')
class system_stability_check_after(aetest.Testcase):

    @aetest.test
    def test(self, steps, script_args, testbed, test_data, timing,testscript):


        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)
        self.router.execute('show version',timeout = 300)
        self.router.execute('clear context',timeout = 300)
        self.router.execute('show inventory',timeout = 300)
        self.router.execute('show install log',timeout = 300)
        self.router.execute('show install active',timeout = 300)
        self.router.execute('show install committed',timeout = 300)
        self.router.execute('show run',timeout = 300)
        self.router.execute('show log',timeout = 300)
        self.router.execute('dir harddisk:/',timeout = 300)
        self.router.execute('show media',timeout = 300)
        self.router.execute('show hw-module fpd')
        self.router.execute('show platform',timeout = 300)
        self.router.execute('show redundancy',timeout = 300)
        self.router.execute('show interface summary',timeout = 300)
        self.router.execute('show interface description',timeout = 300)
        self.router.execute('show bundle',timeout = 300)
        self.router.execute('show route summary',timeout = 300)
        self.router.execute('show route ipv6 summary',timeout = 300)
        self.router.execute('show mpls traffic-eng tunnels summary',timeout = 300)
        self.router.execute('show isis neighbors',timeout = 300)
        self.router.execute('show isis database summary',timeout = 300)
        output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN',timeout = 300)
        # Split the text after the "--------------------------------------------------------------------------------"
        output_lines = output.split("--------------------------------------------------------------------------------")[1:]
        # Clean up and remove leading/trailing whitespace
        output_lines = [line.strip() for line in output_lines if line.strip()]
        # Check if the list is not empty and fail the test case if it's not
        if output_lines:
            self.failed('System is not stable')

        output = self.router.execute('sh platform',timeout = 300)
        # Count occurrences of keywords
        global ios_xr_run_count1
        global operational_count1
        ios_xr_run_count2 = output.count("IOS XR RUN")
        operational_count2 = output.count("OPERATIONAL")
        log.info(f"Count of 'IOS XR RUN' before upgrade: {ios_xr_run_count1}")
        log.info(f"Count of 'OPERATIONAL' before upgrade: {operational_count1}")
        log.info(f"Count of 'IOS XR RUN' after upgrade: {ios_xr_run_count2}")
        log.info(f"Count of 'OPERATIONAL' after upgrade: {operational_count2}")

        if ios_xr_run_count1 != ios_xr_run_count2 or operational_count1 != operational_count2:
            self.failed('All unit did not come up correctly')

        log.info("Waiting 3 mins for more interfaces to come up........")
        time.sleep(180)

        output = self.router.execute('show interface summary',timeout = 300)

        # Extract the value under the "UP" column
        match = re.search(r"ALL TYPES\s+\d+\s+(\d+)", output)
        interface_up_count2 = int(match.group(1))
        global interface_up_count1
        log.info("Total number of interface in UP state before upgrade: %s", interface_up_count1)
        log.info("Total number of interface in UP state after upgrade: %s", interface_up_count2)

        # Calculate the difference percentage
        diff_percentage = (abs(interface_up_count1 - interface_up_count2) / abs(interface_up_count1)) * 100
        log.info("Interface upcount percentage: %s", diff_percentage)
        # Check if the difference is within 5% tolerance level
        tolerance = 20
        if diff_percentage <= tolerance:
            log.info("Interface upcount is within tolerance limit")
        else:
            self.failed('Interface upcount is not in tolerance limit\n')

        self.router.destroy()
        self.router.disconnect()

#@aetest.skip(reason='debug')
class Data_Path_Check(aetest.Testcase):

    @aetest.test
    def test(self, steps, script_args, testbed, test_data, timing,testscript):


        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)
        dp_monitor = 0
        if 'dp_monitor' in test_data:
            self.dp_monitor = test_data['dp_monitor']
        else:
            log.info("FPD Force downgrade is not selected")

        if int(self.dp_monitor) == 1:
            output = self.router.execute('monitor dataplane-health module fabric',timeout = 7200)

            if output.count('FAILURES DETECTED IN DATAPATH.'):
                self.router.execute('bash cat /misc/disk1/dataplane_health_detail_report.txt',timeout = 300)
                self.failed('FAILURES DETECTED IN DATAPATH')

            if output.count('DATAPATH CHECK IS CLEAN.'):
                log.info("DATAPATH CHECK IS CLEAN")


        self.router.destroy()
        self.router.disconnect()


#@aetest.skip(reason='debug')
class CommonCleanup(aetest.CommonCleanup):
    global coredump_list, showtech_list

    @aetest.subsection
    def upload_log(self, steps, script_args, testbed, test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty')
        

        config_load = 0
        if 'config_load' in test_data:
            config_load = test_data['config_load']

        
        if int(config_load) == 1:
            log.info(banner("Loading New Config"))
            self.router.configure('load harddisk:/T2RH_new.cfg', replace=True, timeout=600)
            self.router.execute('clear configuration inconsistency', timeout=600)
        if int(config_load) == 0:
            self.router.configure('load harddisk:/backup_cli.cfg', replace=True, timeout=600)
            self.router.execute('clear configuration inconsistency', timeout=600)

    @aetest.subsection
    def disconnect(self, steps, script_args, testbed):
        step_txt = "Disconnect Device"
        with steps.start(step_txt):
            if testbed.devices:
                for host, connection in testbed.devices.items():
                    if connection:
                        log.info("Disconnecting from %s" % host)
                        connection.disconnect()


