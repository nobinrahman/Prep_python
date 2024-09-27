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

def check_context(script_args):
    ##check dumper and trace
    global coredump_list, showtech_list
    module_args = {}
    module_args['sste_commands'] = '["show context"]'
    output = sste_common.exec_commands(module_args, script_args)
    if output.count('Core location') and output.count('user requested') == 0 :
        contextPIB = output.split('Core for pid =')[-1].split('(')[-1].split(')')[0]
        contextLocation = output.split('Core location:')[-1].split('CPU0:')[-1].split()[0]
        contextLocation = contextLocation.replace(',','')
        contextProcess = output.split('Core for process:')[-1].split()[0]
        core_dict = [contextLocation + '/' + contextProcess, contextProcess]
        coredump_list.append(core_dict)

        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show tech platform timing"]'
        stoutput = sste_common.exec_commands(module_args, script_args)
        if stoutput.count('harddisk:/showtech/'):
            stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
            showtech_dict = ['harddisk:/showtech/'+stoutput, stoutput]
            showtech_list.append(showtech_dict)
        module_args = {}
        module_args['timeout'] = 7200
        module_args['sste_commands'] = '["show tech syslog"]'
        stoutput = sste_common.exec_commands(module_args, script_args)
        if stoutput.count('harddisk:/showtech/'):
            stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
            showtech_dict = ['harddisk:/showtech/'+stoutput, stoutput]
            showtech_list.append(showtech_dict)
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
    module_args['sste_commands'] = '["show tech-support platform timing"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/'+stoutput, stoutput]
        showtech_list.append(showtech_dict)
    module_args = {}
    module_args['timeout'] = 7200
    module_args['sste_commands'] = '["show tech-support syslog"]'
    stoutput = sste_common.exec_commands(module_args, script_args)
    if stoutput.count('harddisk:/showtech/'):
        stoutput = stoutput.split('harddisk:/showtech/')[-1].split()[0]
        showtech_dict = ['harddisk:/showtech/'+stoutput, stoutput]
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
                        log.error(banner( "One or more traffic streams not converge"))
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
    def establish_connections(self, testscript,testbed, steps,test_data):
        result = True
        step_txt = "Connecting to UUT"
   
        with steps.start(step_txt) as s:
            try: 
                testscript.parameters['timing']= tree()
                testscript.parameters['script_args']= tree()
                log.info('##########script_args')
                log.info(testscript.parameters['script_args'])
                if 'connect_via' in test_data:
                    testscript.parameters['script_args']['sste_connect_via'] = test_data['connect_via']
                testscript.parameters['script_args']['uut'] = sste_common._get_connection(testscript.parameters['script_args'],testbed,test_data['UUT'])
                args= {'sste_commands':'[\'show running-config\']'}
                sste_common.exec_commands(args,testscript.parameters['script_args'])
                sste_common.get_version_info(testscript.parameters['script_args'],testbed)
                args = {}
                args['sste_commands'] = ['show running-config | file harddisk:/xr_cli_automation_backup_config']
                sste_common.exec_commands(args,testscript.parameters['script_args'])

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
  
            for testcasename,data in test_data['test_list'].items():
                if data['testclass'] not in testcase_calss:
                    testcase_class.append(data['testclass'])
                    if data['testclass'] not in testcase_data:
                        testcase_data[data['testclass']] = []
                    testcase_data[data['testclass']].append(testcasename)

def get_time(time1,time2):
    ret = ''
    log.info('####time1:'+time1+'\n####time2:'+time2)
    time1_msec = time1.split('.')[-1]
    time1_sec = time1.split('.')[0].split(':')[-1]
    time1_min = time1.split('.')[0].split(':')[1]
    time1_hour = time1.split('.')[0].split(':')[0]
    log.info(time1_hour+':'+time1_min+':'+time1_sec+'.'+time1_msec)

    time2_msec = time2.split('.')[-1]
    time2_sec = time2.split('.')[0].split(':')[-1]
    time2_min = time2.split('.')[0].split(':')[1]
    time2_hour = time2.split('.')[0].split(':')[0]
    log.info(time2_hour+':'+time2_min+':'+time2_sec+'.'+time2_msec)

    ret = float((int(time2_hour))*3600 + (int(time2_min))*60 + int(time2_sec) + float('0.' + time2_msec)) - float((int(time1_hour))*3600 + (int(time1_min))*60 + int(time1_sec) + float('0.' + time1_msec))

    return ret


#@aetest.skip(reason='debug')
class precheck(aetest.Testcase):
    global coredump_list, showtech_list
    @aetest.test
    def precheck(self,steps,script_args,testbed,test_data,timing):
        log.info('in precheck ...')
        try:
            info = ['show interfaces summary', 'show interfaces summary', 'show ipv4 interface summary',
                    'show ipv6 interface summary','show platform','show inventory','show ethernet trunk',
                    'show macsec mka summary']
            script_args['precheck'] = sste_common._get_snapshot_data(script_args, info)
        except Exception as e:
            log.error(str(e))
            self.failed('precheck failed')

        log.info('#####postcheck:\n')
        log.info(script_args['precheck'])


#@aetest.skip(reason='Skip ')
class Mem_Leak_Check_Start(aetest.Testcase):
    #global coredump_list, showtech_list, interface_list

    @aetest.test
    def memleak_check_start(self, steps, script_args, testscript, testbed, test_data, timing):
####################################### MEM_LEAK ####################################### 

        mem_leak_start(script_args)
        
######################################################################################## 


class reload_lc(aetest.Testcase):
    global coredump_list, showtech_list
    @aetest.test
    def reload_lc(self,steps,script_args,testbed,test_data,timing):

        LCs = []
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)

        if 'memory' in test_data:
            self.memory = test_data['memory']
        else:
            self.memory = 0
        if self.memory:
            self.router.execute('show memory summary location all', timeout = 300)

            output = self.router.execute('show platform | in CPU', timeout = 300)
            nodeList = []
            items = output.split('CPU0')
            for index in range(0,len(items) -1):
                nodeList.append(items[index].split()[-1] + 'CPU0')
            log.info('nodes to participate memory compare:')
            log.info(nodeList)

            for node in nodeList:
                self.router.execute('show memory compare start location ' + node, timeout = 300)

        
        if 'loop' in test_data:
            self.loop = test_data['loop']
        else:
            self.loop = 10
        try:
            output = self.router.execute('show platform | in CPU | in RUN | ex RP', timeout = 300)
            output = output.split('/CPU0')
            for index in range(0, len(output) - 1):
                tmp = output[index]
                LCs.append(tmp.split()[-1].replace('0/', ''))
            log.info(LCs)
        except Exception as e:
            log.error(str(e))
            self.failed('get RUN LC failed')

        time_loop = {}
        self.lc = str(random.choice(LCs))

        for loopindex in range(int(self.loop)):
            log.info('#### Loop ' + str(loopindex))
            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_before_trigger')
                ret_val = Take_traffic_snapshot_before_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)

            output = self.router.execute('show platform | in 0/' + self.lc +'/CPU0')
            if output.count('IOS XR RUN') == 0:
                self.failed('\nLC is not in IOS XR RUN before reload')

            self.router.execute('clear controller npu stats traps-all instance all location all')

            output = self.router.execute('show interfaces brief location 0/' + self.lc + '/CPU0')
            countup1 = output.count('up')

            lc_intfs = []
            for line in output.split('\r\n'):
                if line.count('up'):
                    lc_intfs.append(line.split()[0])

            self.router.execute('clear counters all', timeout = 300)

            output = self.router.execute('show clock')
            time1 = output.split()[-6]

            output = self.router.execute('clear log')
            if script_args['os_type'] in ['5500','ncs5500','NCS5500']:
                output = self.router.execute('admin hw-module location 0/' + self.lc + ' reload noprompt')
            if script_args['os_type'] in ['8000']:
                output = self.router.execute('reload location 0/' + self.lc + ' noprompt')
            time.sleep(60)

            if countup1 == 0:
                #if there is no interface up, only need wait for 30 mins to check it again
                time.sleep(1800)
            else:

                index = 0
                ##1 hours check
                while index < 720:
                    index = index + 1
                    output = self.router.execute('show interfaces brief location 0/' + self.lc + '/CPU0', timeout = 600)
                    countup2 = output.count('up')
                    if countup2 == countup1:
                        output = self.router.execute('show clock')
                        time2 = output.split()[-6]
                        break
                    time.sleep(5)

                if index == 720:
                    show_tech(script_args)
                    self.failed("not all intf up within 1 hours after reload")

                time_loop[loopindex] = get_time(time1,time2)

                log.info('#### Loop ' + str(loopindex) + '####Time: '+ str(time_loop[loopindex]))

                if loopindex > 0:
                    if abs(time_loop[loopindex] - time_loop[loopindex-1]) / time_loop[loopindex-1] > 0.5:
                        show_tech(script_args)
                        self.failed('LC reload time diff exceed 10%: ' + str(time_loop[loopindex]) + ' VS ' +str(time_loop[loopindex-1]))

            ##check no double flap
            self.router.execute('show logging | in \"PKT_INFRA-LINK-3-UPDOWN\"')
            output = self.router.execute('show logging | in \"changed state to Up\"')
            intfs = []
            for line in output.split('\r\n'):
                if line.count('PKT_INFRA-LINK-3-UPDOWN'):
                    intf = line.split(', changed state to Up')[0].split()[-1]
                    if intf in intfs:
                        self.router.execute('show logging | in \"PKT_INFRA-LINK-3-UPDOWN\" | in ' + intf)
                        #show_tech(script_args)
                        #self.failed('multple interface flap happend on interface: ' + intf)
                    else:
                        intfs.append(intf)
            log.info(intfs)

            output = self.router.execute('show controllers npu stats traps-all instance all location all | i GLEAN')
            if output.count('GLEAN') == output.count('0                    0'):
                pass
            else:
                log.info('dropped pkts happened')

            if 'tgn' in test_data:
                log.info('Take_traffic_snapshot_after_trigger')
                ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
                log.info(ret_val)
                if ret_val:
                    log.info("traffic converged equals to : {}".format(ret_val))
                else:
                    show_tech(script_args)
                    self.failed("traffic not converged")

            ##check CRC Errors and others
            for intf in lc_intfs:
                if intf.count('0/6/0/0') and test_data['UUT'].count('F8'):
                    continue
                output = self.router.execute('show interfaces ' + intf)
                # if output.count('0 input errors') == 0 and output.count(' input errors'):
                #     self.failed('input errors happened on intf: ' + intf)
                if output.count(', 0 CRC') == 0 and output.count(' CRC'):
                    self.failed('input CRC happened on intf: ' + intf)
                # if output.count(', 0 overrun') == 0 and output.count(' overrun'):
                #     self.failed('input overrun happened on intf: ' + intf)
                # if output.count(', 0 ignored') == 0 and output.count(' ignored'):
                #     self.failed('input ignored happened on intf: ' + intf)
                # if output.count(', 0 abort') == 0 and output.count(' abort'):
                #     self.failed('input abort happened on intf: ' + intf)
                # if output.count('0 output errors') == 0 and output.count(' output errors'):
                #     self.failed('output errors happened on intf: ' + intf)


        log.info(time_loop)

        if self.memory:
            log.info('sleep another hour wait for stable ... ')
            time.sleep(3600)
            self.router.execute('show memory summary location all', timeout=300)

            for node in nodeList:
                self.router.execute('show memory compare end location ' + node, timeout=300)

            for node in nodeList:
                self.router.execute('show memory compare report location ' + node, timeout=300)

        if check_context(script_args):
            self.failed('crash happened\n')


#@aetest.skip(reason='Skip ')
class Mem_Leak_Check_End(aetest.Testcase):
    #global coredump_list, showtech_list, interface_list

    @aetest.test
    def memleak_check_end(self, steps, script_args, testscript, testbed, test_data, timing):

####################################### MEM_LEAK ####################################### 
        

        mem_leak_end(script_args)

######################################################################################## 

@aetest.skip(reason='debug')
class postcheck(aetest.Testcase):
    global coredump_list, showtech_list
    @aetest.test
    def postcheck(self,steps,script_args,testbed,test_data,timing):
        log.info('in postcheck ...')
        time.sleep(600)
        try:
            info = ['show interfaces summary', 'show interfaces summary', 'show ipv4 interface summary',
                    'show ipv6 interface summary','show platform','show inventory','show ethernet trunk',
                    'show macsec mka summary']
            script_args['postcheck'] = sste_common._get_snapshot_data(script_args, info)
        except Exception as e:
            log.error(str(e))
            self.failed('precheck failed')

        log.info('#####postcheck:\n')
        log.info(script_args['precheck'])
        log.info('#####postcheck:\n')
        log.info(script_args['postcheck'])

        from deepdiff import DeepDiff
        diff = DeepDiff(script_args['precheck'], script_args['postcheck'])
        if diff:
            log.info('snapshot precheck and postcheck compare diff:\n')
            log.info(diff)
            self.failed('snapshot precheck and postcheck compare failed\n')
        log.info('snapshot precheck and postcheck compare passed\n')



class CommonCleanup(aetest.CommonCleanup):
    global coredump_list, showtech_list

    @aetest.subsection
    def upload_log(self, steps, script_args, testbed,test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        self.router = genietestbed.devices[test_data['UUT']]
        self.router.connect(via='vty',connection_timeout=300)
        self.router.configure('load harddisk:/backup_cli.cfg', replace=True, timeout=600)
        self.router.execute('clear configuration inconsistency', timeout=600)
        if 'upload_result' not in test_data or str(test_data['upload_result']) == "1":
            sste_common.upload_log(script_args,testbed,test_data)

        log.info('######################Copy core files############################')
        log.info(coredump_list)
        for core in coredump_list:
            args = {}
            log.info('copying '+core[0]+' out to '+script_args['debug_log_path'])
            args['sste_commands'] = ['copy '+core[0]+' tftp://172.23.16.140'+script_args['debug_log_path']+'/'+core[1]+' vrf MGMT']
            sste_common.exec_commands(args, script_args)

        log.info('######################Copy show tech############################')
        log.info(showtech_list)
        for showtech in showtech_list:
            args = {}
            log.info('copying ' + showtech[0] + ' out to ' + script_args['debug_log_path'])
            args['sste_commands'] = ['copy ' + showtech[0] + ' tftp://172.23.16.140' + script_args['debug_log_path'] + '/' + showtech[1] + ' vrf MGMT']
            sste_common.exec_commands(args, script_args)

    @aetest.subsection
    def disconnect(self, steps, script_args, testbed):
        step_txt = "Disconnect Device"
        with steps.start(step_txt):
            if testbed.devices:
                for host,connection in testbed.devices.items():
                    if connection:
                        log.info("Disconnecting from %s" % host)
                        connection.disconnect()
