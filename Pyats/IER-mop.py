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
        #self.router.execute('show run',timeout = 300)
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
        #self.router.execute('show mpls traffic-eng tunnels summary',timeout = 300)
        self.router.execute('show isis neighbors',timeout = 300)
        self.router.execute('show isis database summary',timeout = 300)
        output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | exclude UP | exclude FAILED',timeout = 300)
        # Split the text after the "--------------------------------------------------------------------------------"
        output_lines = output.split("--------------------------------------------------------------------------------")[1:]
        # Clean up and remove leading/trailing whitespace
        output_lines = [line.strip() for line in output_lines if line.strip()]
        # Check if the list is not empty and fail the test case if it's not
        if output_lines:
            self.failed('System is not stable')

        output = self.router.execute('show interface summary',timeout = 300)

        # Extract the value under the "UP" column
        match = re.search(r"ALL TYPES\s+\d+\s+(\d+)", output)
        global interface_up_count1
        interface_up_count1 = int(match.group(1))
        log.info("Total number of interface in UP state before upgrade: %s", interface_up_count1)
        

        self.router.destroy()
        self.router.disconnect()
        

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
        start = self.iso.find("ncs5500-goldenk9-x-") + len("ncs5500-goldenk9-x-")
        end = self.iso.find(".iso")
        
        # Extract the desired substring
        result = self.iso[start:end]
        log.info("Current Iso from Jenkins: %s", result)

        if version0 != result:
            log.info("DUT needs to be on correct image")

        self.router.execute('admin show version',timeout = 300)
        self.router.execute('show install active summary',timeout = 300)
        self.router.execute('admin show install active summary',timeout = 300)
        output = self.router.execute('show media | i "Avail|harddisk"',timeout = 300)
        lines = output.split('\n')

        # Find the line that contains "harddisk:"
        for line in lines:
            if "harddisk:" in line:
                # Split the line into words and extract the "Avail" value
                words = line.split()
                avail_value = words[-1]
                # Check if the "Available Value" is not more than 5G
                if float(avail_value[:-1]) <= 5:
                    self.failed('DUT do not have enough space\n')
                else:
                    log.info("Have enough space to perform Install operation")

        self.router.execute('admin show media | i "Avail|harddisk"',timeout = 300)

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

#        # Isolating the device from network
#        log.info(banner("Isolating the device from network"))
#        isisconfig = self.router.execute('show run | i router isis')
#        # Find the line with "router isis" and capture the content after it
#        isis = isisconfig.strip().splitlines()
#        last_item = isis[-1]
#        log.info('LAST_ITEM' + last_item)
#        isis_number = last_item.split()[-1]
#        log.info('####isis_number' + isis_number)
#        
#
#
#        self.router.configure('router isis ' + isis_number + '\n'
#                                    'max-metric level 2\n'
#                                    'root\n', timeout=60)
        
        log.info(banner("Install Remove Inactivate Operation"))
        # Performing install remove inactivate to prepare the box for install 
        self.router.execute('install remove inactivate all')
        time.sleep(10)

        
        self.router.send('admin\n', timeout = 300)
        time.sleep(5)
        self.router.send('install remove inactivate\n', timeout = 300)
        time.sleep(30)
        
        self.router.send('exit\n', timeout = 300)
        time.sleep(10)
        self.router.execute('show version', timeout = 300)


        # FPD Check
        log.info(banner("FPD Config Check"))
        output = self.router.execute('show run fpd auto-upgrad', timeout = 300)
        # Check if "fpd auto-upgrade enable" is present in the output using .find()
        if 'fpd auto-upgrade enable' not in output:
            self.failed('fpd auto-upgrade enable is not configured\n')

        if output.find("fpd auto-upgrade enable") != -1:
            # Save it in a variable
            fpd_auto_upgrade = "fpd auto-upgrade enable"
        self.router.execute('admin show run fpd auto-upgrad', timeout = 300)



        #############################################Upgrading to New Image Start#############################################
        log.info(banner("Install Replace Operation"))
        
        try:
            self.router.execute('install replace harddisk:/' + isoname + ' noprompt commit', timeout = 7200)
        except:
            log.info("Install Replace operation still going on")
            time.sleep(600)
        #############################################Upgrading to New Image End#############################################

        

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
        ######################################## FPD FORCE DOWNGRADE ########################################  
        #Force FPD Downgrade
        
        if 'fpd_force' in test_data:
            self.fpd_force = test_data['fpd_force']
        else:
            log.info("FPD Force downgrade is not selected")

        if int(self.fpd_force) == 1:
            log.info(banner("Force FPD Downgrade"))
            self.router.execute('upgrade hw-module location all fpd all force')
            time.sleep(30)
            while 1:
                output = self.router.execute('show hw-module fpd | e 0/PM0 | e 0/PM1')
                time.sleep(10)

                # Split the text into lines
                lines = output.split('\n')
                
                # Initialize an empty list to store the "CURRENT" values
                current_values = []
                # Iterate through the lines and look for lines containing "CURRENT"
                for line in lines:
                    if "%" in line:
                        # Split the line by whitespace and get the last element (which is "CURRENT")
                        elements = line.split()
                        
                        current_value = elements[-3]
                        
                        current_values.append(current_value)
                        

                        # Check if the list is empty
                if not current_values:
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

                output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | ex SHUT DOWN | ex UP | ex FAILED',timeout = 300)
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




        output = self.router.execute('sh hw-module fpd | e 0/PM0 | e 0/PM1')

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
        start = isoname.find("ncs5500-goldenk9-x-") + len("ncs5500-goldenk9-x-")
        end = isoname.find(".iso")
        
        # Extract the desired substring
        result = isoname[start:end]

        if version0 != result:
            self.failed('DUT did not install correct image\n')
        time.sleep(30)
        self.router.execute('admin show version', timeout = 300)
    
        while 1:
            output = self.router.execute('show install request', timeout = 300)
            time.sleep(5)
            if output.count('No install operation in progress') or output.count('Success'):
                break

        log.info('####T19:' + version0)

        log.info(banner("Checking required RPM's"))
        self.router.execute('show install active summary', timeout = 300)
        self.router.execute('admin show install active summary', timeout = 300)
        self.router.execute('show install commit summary', timeout = 300)
        self.router.execute('admin show install commit summary', timeout = 300)


        log.info(banner("Clearing configuration inconsitency"))
        self.router.execute('clear configuration inconsistency', timeout = 300)

        ztp_check = 0
        if 'ztp_check' in test_data:
            ztp_check = int(test_data['ztp_check'])
        if ztp_check == 1:

            if script_args['os_type'] in ['5500', 'ncs5500', 'NCS5500']:
                log.info(banner("------ZTP CHECK------"))
                log.info('ztp ini checking ...')
                output = self.router.execute('run cat /var/xr/ztp/ztp.ini')
                if output.count('start:         False') == 0 or output.count('retry_forever: False') == 0:
                    log.info('ZTP check failed\n')
        
                output = self.router.execute('run tail /var/log/ztp.log')
                if output.count('Valid giso ini file found') == 0 or output.count('ZTP is not configured to start') == 0:
                    log.info('ZTP check failed\n')
        
        else:
            log.info('ztp ini check skipped')

        output = self.router.execute('show logging | in dumper', timeout = 300)
        if output.count('dumper'):
            log.error('\ncrash may happened, check the dumper info')
            return True
        output = self.router.execute('show logging | in Traceback', timeout = 300)
        if output.count('Traceback'):
            log.error('\ncrash may happened, check the Traceback info')
            return True


        output = self.router.execute('show context', timeout = 300)
        if output.count('node:') != output.count('No context'):
            log.error('\ncrash may happened, check the show context info')
            return True
        return False
        
#        log.info('Current version is' + version0)
#        if version0 == "7.3.4-41":
#            log.info(version0)
#            self.router.configure('hw-module profile load-balance algorithm mpls-lsr-ler-optimized', timeout = 300)
#            log.info(banner("Reload Action"))
#        
#            try:
#                self.router.execute('reload location all', timeout = 7200)
#            except:
#                log.info("Reload is in Progress")
#                time.sleep(300)
#            time.sleep(300)
#            testbed_file = testbed.testbed_file
#            genietestbed = load(testbed_file)
#            self.router = genietestbed.devices[test_data['UUT']]
#            retry = 0
#            while retry < 10:
#                try:
#                    self.router.connect(via='vty', connection_timeout=600, mit=True)
#                    break
#                except:
#                    time.sleep(300)
#                    retry += 1
#                    if retry == 10:
#                        log.failed('connect failed')
#            output = self.router.execute('show run | inc hw-module', timeout = 300)
#            
#
#            if output.count('hw-module profile load-balance algorithm mpls-lsr-ler-optimized'):
#                log.info('hw-module profile load-balance algorithm mpls-lsr-ler is configured')
#            else:
#                self.failed('hw-module profile load-balance algorithm mpls-lsr-ler-optimized is not properly configured\n')
#
#        if version0 == "7.3.4-36":
#            log.info(version0)
#            self.router.configure('no hw-module profile load-balance algorithm mpls-lsr-ler-optimized', timeout = 300)
#            self.router.execute('show run | inc hw-module', timeout = 300)
#            if output.count('hw-module profile load-balance algorithm mpls-lsr-ler-optimized'):
#                self.failed('hw-module profile load-balance algorithm mpls-lsr-ler-optimized is not properly configured\n')
#            else:
#                log.info('hw-module profile load-balance algorithm mpls-lsr-ler is not configured')

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
        #self.router.execute('show run',timeout = 300)
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
        #self.router.execute('show mpls traffic-eng tunnels summary',timeout = 300)
        self.router.execute('show isis neighbors',timeout = 300)
        self.router.execute('show isis database summary',timeout = 300)
        output = self.router.execute('sh platform | exclude OPERATIONAL | exclude IOS XR RUN | exclude UP | ex FAILED',timeout = 300)
        # Split the text after the "--------------------------------------------------------------------------------"
        output_lines = output.split("--------------------------------------------------------------------------------")[1:]
        # Clean up and remove leading/trailing whitespace
        output_lines = [line.strip() for line in output_lines if line.strip()]
        # Check if the list is not empty and fail the test case if it's not
        if output_lines:
            self.failed('System is not stable')

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

##@aetest.skip(reason='debug')
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

    @aetest.subsection
    def disconnect(self, steps, script_args, testbed):
        step_txt = "Disconnect Device"
        with steps.start(step_txt):
            if testbed.devices:
                for host, connection in testbed.devices.items():
                    if connection:
                        log.info("Disconnecting from %s" % host)
                        connection.disconnect()

