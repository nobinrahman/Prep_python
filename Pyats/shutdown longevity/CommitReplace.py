'''
script.py

'''
# see https://pubhub.devnetcloud.com/media/pyats/docs/aetest/index.html
# for documentation on pyATS test scripts

# optional author information
# (update below with your contact information if needed)
__author__ = 'Cisco Systems Inc.'
__copyright__ = 'Copyright (c) 2019, Cisco Systems Inc.'
__contact__ = ['weswang@cisco.com']
__credits__ = ['list', 'of', 'credit']
__version__ = 1.0

import logging

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
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
from ats.log.utils import banner
from pyats.aetest.loop import Iteration
import time
from texttable import Texttable
from genie.utils import Dq
from genie.testbed import load
import os
import xmltodict

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

# Get your logger for your script
log = logging.getLogger(__name__)

coredump_list = []
showtech_list = []
intf_list = []
bundle_list = []
intf_optic_list = []

def check_context(script_args):
    ##check dumper and trace
    global coredump_list, showtech_list
    module_args = {}
    module_args['sste_commands'] = '["show context"]'
    output = sste_common.exec_commands(module_args, script_args)
    if output.count('Core location') and output.count('user requested') == 0 :


        log.error('\ncrash may happened, check the Traceback info')
        log.info(coredump_list)
        log.info(showtech_list)
        module_args = {}
        module_args['timeout'] = 300
        module_args['sste_commands'] = '["clear context"]'
        stoutput = sste_common.exec_commands(module_args, script_args)
        return True
    return False

def show_tech(script_args):
    global coredump_list, showtech_list
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show tech-support routing isis"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
        showtech_list.append(showtech_dict)
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show tech syslog"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/' + stoutput, stoutput]
        showtech_list.append(showtech_dict)

    log.info(showtech_list)
    return


def mem_leak_start(script_args):
    try:
        log.info(banner("Starting Memory Compare"))
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["sh platform | i CPU0"]'
        stoutput = sste_common.exec_commands(module_args, script_args)

        # Extract words containing "CPU0"
        cpu0_list = re.findall(r'\S*CPU0\S*', stoutput)

        log.info(banner(f"List of Active LC and RP {cpu0_list}"))

        for location in cpu0_list:
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = ['show memory compare start location ' + location]
            stoutput = sste_common.exec_commands(module_args, script_args)
        
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show memory summary location all"]'
        stoutput = sste_common.exec_commands(module_args, script_args)


        log.info(banner("Checking Show Drops"))
        if script_args['os_type'] in ['8000']:
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = '["show drops all ongoing location all"]'
            stoutput = sste_common.exec_commands(module_args, script_args)

        if script_args['os_type'] in ['5500','ncs5500','NCS5500']:
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = '["show drops-all ongoing location all"]'
            stoutput = sste_common.exec_commands(module_args, script_args)

    except Exception as e:
        log.error(str(e))
        show_tech(script_args)
        self.failed("show bundle brief | in BE: Failed")  


def mem_leak_end(script_args):
    try:
        log.info(banner("Waiting 10 minutes for the memory to settle down"))
        time.sleep(600)
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["sh platform | i CPU0"]'
        stoutput = sste_common.exec_commands(module_args, script_args)

        # Extract words containing "CPU0"
        cpu0_list = re.findall(r'\S*CPU0\S*', stoutput)

        log.info(banner(f"List of Active LC and RP {cpu0_list}"))
        log.info(banner("Ending Memory Compare "))
        for location in cpu0_list:           
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = ['show memory compare end location ' + location]
            stoutput = sste_common.exec_commands(module_args, script_args)

        log.info(banner("Memory Compare Report"))
        for location in cpu0_list:
        #log.info(banner("Memory Compare Report"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ['show memory compare report location ' + location]
            #module_args['sste_commands'] = ["show memory compare report location 0/RP0/CPU0 "]
            output = sste_common.exec_commands(module_args, script_args) 

            # Split the data into lines
            lines = output.split('\n')

            # Find the starting line of the data table
            start_index = next((i for i, line in enumerate(lines) if 'PID' in line), None)

            if start_index is not None:
                start_index += 2  # Move two lines down to reach the data
                # Extract and print the header
                header = lines[start_index - 3].split()
                # Initialize an empty list to store lists of Process Name and DIFFERENCE
                final_result_list = []


            # Iterate through the data and append lists of Process Name and DIFFERENCE to the result list
            for line in lines[start_index:]:
                if line.strip():  # Skip empty lines
                    columns = line.split()
                    process_name = str(columns[1])  # Convert Process name to string
                    difference = int(columns[-2])  # Convert DIFFERENCE to integer
                    final_result_list.append([process_name, difference])
            
            log.info("[PROCESS_NAME DIFFERENCE]: %s", final_result_list)

            for sublist in final_result_list:
                pname = sublist[0]
                difference = sublist[1]

                if difference > 0:
                    log.info("PROCESS_NAME: %s", pname)
                    log.info(banner(f"PROCESS_NAME: {pname}"))
                    module_args = {}
                    module_args['timeout'] = 300
                    #module_args['sste_commands'] = ["show memory-snapshots process " + pname + " location " + location for location in cpu0_list]
                    #module_args['sste_commands'] = ["show memory-snapshots process " + pname + " location 0/RP0/CPU0" ]
                    module_args['sste_commands'] = ["show memory-snapshots process " + pname + " location " + location]
                    output = sste_common.exec_commands(module_args, script_args)

        
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show memory summary location all"]'
        stoutput = sste_common.exec_commands(module_args, script_args)

        log.info(banner("Checking Show Drops"))
        if script_args['os_type'] in ['8000']:
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = '["show drops all ongoing location all"]'
            stoutput = sste_common.exec_commands(module_args, script_args)

        if script_args['os_type'] in ['5500','ncs5500','NCS5500']:
            module_args = {}
            module_args['timeout'] = 7200
            module_args['sste_commands'] = '["show drops-all ongoing location all"]'
            stoutput = sste_common.exec_commands(module_args, script_args)

    except Exception as e:
        log.error(str(e))
        show_tech(script_args)
        self.failed("show bundle brief | in BE: Failed")    

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


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testscript, testbed, steps, test_data):
        '''
        establishes connection to all your testbed devices.
        '''
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


                sste_common.get_version_info(testscript.parameters['script_args'], testbed)
                args = {}
                args['timeout'] = 7200
                args['sste_commands'] = ['show running-config | file harddisk:/xr_cli_automation_backup_config']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['timeout'] = 7200
                args['sste_commands'] = ['clear context']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['timeout'] = 7200
                args['sste_commands'] = ['clear log']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['timeout'] = 7200
                args['sste_commands'] = ['dir harddisk:']
                output = sste_common.exec_commands(args, testscript.parameters['script_args'])
                if output.count('backup_cli.cfg'):
                    args = {}
                    args['timeout'] = 7200
                    args['sste_commands'] = ['delete harddisk:/backup_cli.cfg']
                    sste_common.exec_commands(args, testscript.parameters['script_args'])

                args = {}
                args['timeout'] = 7200
                args['sste_commands'] = ['copy running-config harddisk:/backup_cli.cfg']
                sste_common.exec_commands(args, testscript.parameters['script_args'])

            except Exception as e:
                log.error(str(e))
                result = False
                s.failed(step_txt + ": Failed")
                self.failed(step_txt + ": Failed")

        log.info('##########test_data')
        log.info(test_data)

        if 'tgn' in test_data :
            step_txt = "Connecting to TGN"
            with steps.start(step_txt, continue_=True) as s:
                try:
                    if not sste_tgn.tgn_connect(testscript.parameters['script_args'],testbed,test_data['tgn'],test_data):
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

        # make sure testbed is provided
        assert testbed, 'Testbed is not provided!'
        # if 'jumphost' in list(genietestbed.devices):
        #     # Set environment variables
        #     os.environ['USER_NAME'] = getpass.getpass("CEC Username for jumphost:")
        #     os.environ['PASS_WORD'] = getpass.getpass("Password for " + os.environ['USER_NAME'] + ":")

        log.info("CommonSetup successfully ")


#@aetest.skip(reason='Skip ')
class Mem_Leak_Check_Start(aetest.Testcase):
    #global coredump_list, showtech_list, interface_list

    @aetest.test
    def memleak_check_start(self, steps, script_args, testscript, testbed, test_data, timing):
####################################### MEM_LEAK ####################################### 

        mem_leak_start(script_args)
        
######################################################################################## 

####interface: 1.3.6.1.2.1.2

#@aetest.skip(reason='debug')
class commitreplace(aetest.Testcase):
    global coredump_list, showtech_list

    @aetest.test
    def test(self, steps, script_args, testbed, test_data, timing):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty', connection_timeout=300)

#        if 'memory' in test_data:
#            self.memory = test_data['memory']
#        else:
#            self.memory = 0
#        if self.memory:
#            self.router.execute('show memory summary location all', timeout=300)
#
#            output = self.router.execute('show platform | in CPU', timeout=300)
#            nodeList = []
#            items = output.split('CPU0')
#            for index in range(0, len(items) - 1):
#                nodeList.append(items[index].split()[-1] + 'CPU0')
#            log.info('nodes to participate memory compare:')
#            log.info(nodeList)
#
#            for node in nodeList:
#                self.router.execute('show memory compare start location ' + node, timeout=300)

        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 1
        for loop in range(int(self.loop)):
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)

            saved = 'load harddisk:/backup_cli.cfg'

            # try:
            #     args = {}
            #
            #     args['timeout'] = 7200
            #     args['sste_commands'] = ['','commit replace']
            #     sste_common.config_commands(args, script_args)
            # except Exception as e:
            #     log.info('###exception###: ' + str(e))
            #     log.info('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
            #     show_tech(script_args)
            #     self.failed("something wrong with commit replace")
            # time.sleep(600)

            try:
                args = {}

                args['timeout'] = 300
                args['sste_commands'] = ['load harddisk:/backup_cli.cfg','commit replace']
                sste_common.config_commands(args, script_args)
            except Exception as e:
                log.info('###exception###: ' + str(e))
                log.info('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
                show_tech(script_args)
                self.failed("something wrong with commit replace")
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

#        if self.memory:
#            log.info('sleep another hour wait for stable ... ')
#            time.sleep(3600)
#            self.router.execute('show memory summary location all', timeout=300)
#
#            for node in nodeList:
#                self.router.execute('show memory compare end location ' + node, timeout=300)
#
#            for node in nodeList:
#                self.router.execute('show memory compare report location ' + node, timeout=300)
        if check_context(script_args):
            self.failed('crash happened\n')

    pass

    @aetest.cleanup
    def cleanup(self):
        pass

#@aetest.skip(reason='Skip ')
class Mem_Leak_Check_End(aetest.Testcase):
    #global coredump_list, showtech_list, interface_list

    @aetest.test
    def memleak_check_end(self, steps, script_args, testscript, testbed, test_data, timing):

####################################### MEM_LEAK ####################################### 
        
        mem_leak_end(script_args)

######################################################################################## 


class CommonCleanup(aetest.CommonCleanup):
    global coredump_list, showtech_list

    @aetest.subsection
    def upload_log(self, script_args, testbed, test_data):
        args = {}

        args['timeout'] = 7200
        args['sste_commands'] = ['load harddisk:/backup_cli.cfg', 'commit replace']
        sste_common.config_commands(args, script_args)

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
    def subsection_cleanup_one(self):
        pass

