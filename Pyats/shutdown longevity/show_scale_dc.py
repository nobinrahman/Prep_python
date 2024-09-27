#!/bin/env python

import sys
sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
import re
import random
import logging
import collections
import sste_exr
import sste_snmp
import sste_cxr
import sste_common
import sste_trigger
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
from stcrestclient import stchttp

from genie.testbed import load

def tree(): return collections.defaultdict(tree)

def get_time(time):
    multiplier = 1
    pattern = "(\d*).*s"
    time = str(time)
    if time.endswith("ms"):
        multiplier  = 0.001
        pattern = "(\d*).*ms"
    elif not time.endswith("s"):
        time = str(time)+"s"
    result = re.search(pattern,time)
    if result:
        return int(result.group(1)) * multiplier
    return 0


try:
    cli_mapping = sste_cli_keys.cli_mapping
    cli_parser_exclude_keys = sste_cli_keys.cli_parser_exclude_keys
    cli_parser_non_matching_keys = sste_cli_keys.cli_parser_non_matching_keys
except ImportError:
    cli_parser_exclude_keys = {}
    cli_parser_non_matching_keys = {}
    cli_mapping = {}
    pass

def check_context(ssh):
    ##check dumper and trace
    global coredump_list, showtech_list
    output = ssh.execute('show context',timeout = 300)
    if output.count('Core location') and output.count('user requested') == 0 :
        log.info('CHECKER: CRASH')
        ssh.execute('clear context', timeout=300)
        return False

    output = ssh.execute('show logging | in HW_PROG_ERROR ', timeout = 300)
    if output.count('HW_PROG_ERROR'):
        ssh.execute('clear log', timeout = 300)
        log.info('CHECKER: HW_PROG_ERROR')
        return False

    output = ssh.execute('show logging | in OOR_RED | exclude sipidxtbl', timeout = 300)
    if output.count('OOR_RED'):
        ssh.execute('clear log', timeout = 300)
        log.info('CHECKER: OUT_OF_RESOURCE')
        return False
    return False


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def establish_connections(self, testscript,testbed, steps,test_data):
        nest_data = {
            "user_id" : test_data['userid'],
            "testbed" : "CET_CVT",
            "trigger" : "cvtauto",
            "trigger_prefix" : "cetcvt"
        }
        result = True
        step_txt = "Connecting to UUT"
   


        step_txt = "Backup Running Config "
        with steps.start(step_txt, continue_=False) as s:
            try:
                args= {'sste_commands':'[\'show running-config | file harddisk:/running_config_beforetrigger.txt\']'}
                sste_common.exec_commands(args,testscript.parameters['script_args'])
            except Exception as e:
                log.error(str(e))
                self.passx(step_txt + ": Failed")


        testsuitename = "CVT MBB LOG Suite"
        if 'testsuite' in test_data:
            testscript.parameters['script_args']['testsuitename'] = test_data['testsuite']
        testgroup = "CVT Trigger Suite"
        if 'testgroup' in test_data:
            testscript.parameters['script_args']['testsuitename'] = test_data['testgroup']



class SHOW_SCALE_D18_R10(aetest.Testcase):

    @aetest.test
    def showscale(self,testbed,test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        log.info(genietestbed.devices)

        D18_R10 = genietestbed.devices['D18-R10']
        D18_R10.connect(via='vty', connection_timeout=600)        
        D18_R10.execute('show version', timeout = 7200)
        D18_R10.execute('show bgp scale', timeout = 7200)
        D18_R10.execute('show rib attributes summary', timeout = 7200)
        D18_R10.execute('show rib ipv6 attribute summary', timeout = 7200)
        D18_R10.execute('show route summary', timeout = 7200)
        D18_R10.execute('show cef summary', timeout = 7200)
        D18_R10.execute('show context', timeout = 7200)
        D18_R10.execute('show interface summary', timeout = 7200)
        D18_R10.execute('show int tunnel-ip * | i tunnel-ip', timeout = 7200)
        D18_R10.execute('show monitor-session ERSPAN status internal', timeout = 7200)
        D18_R10.execute('show isis neighbors summary', timeout = 7200)
        D18_R10.execute('show mpls ldp summary', timeout = 7200)
        
        D18_R10.execute('show mpls forwarding summary', timeout = 7200)
        D18_R10.execute('show drops all ongoing location all', timeout = 7200)
        D18_R10.execute('show log | i ONLINE_DIAG_FAIL', timeout = 7200)
        D18_R10.execute('show mpls traffic-eng tunnels summary', timeout = 7200)
        D18_R10.execute('show isis topology summary', timeout = 7200)
        D18_R10.execute('show isis segment-routing label table | uti wc lines', timeout = 7200)
        D18_R10.execute('show memory-top-consumers location 0/RP0/CPU0', timeout = 7200)
        D18_R10.execute('show mpls traffic-eng tunnel tabular', timeout = 7200)

        D18_R10.execute('run netstat -s | grep -i tcp: -A15', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/RP0/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/0/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/1/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/2/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/3/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/4/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/5/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/6/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/7/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/8/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/9/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/10/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/11/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/12/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/13/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/14/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/15/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/16/CPU0', timeout = 7200)
        D18_R10.execute('show controllers switch statistics location 0/16/CPU0', timeout = 7200)

        #D18_R10.disconnet()
        time.sleep(10)

class SHOW_SCALE_D8_R9(aetest.Testcase):
    @aetest.test
    def showscale(self,testbed,test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        log.info(genietestbed.devices)
        D8_R9 = genietestbed.devices['D8-R9']
        D8_R9.connect(via='vty', connection_timeout=600)
        D8_R9.execute('show version', timeout = 7200)
        D8_R9.execute('show bgp scale', timeout = 7200)
        D8_R9.execute('show rib attributes summary', timeout = 7200)
        D8_R9.execute('show rib ipv6 attribute summary', timeout = 7200)
        D8_R9.execute('show route summary', timeout = 7200)
        D8_R9.execute('show cef summary', timeout = 7200)
        D8_R9.execute('show context', timeout = 7200)
        D8_R9.execute('show interface summary', timeout = 7200)
        D8_R9.execute('show int tunnel-ip * | i tunnel-ip', timeout = 7200)
        D8_R9.execute('show monitor-session ERSPAN status internal', timeout = 7200)
        D8_R9.execute('show isis neighbors summary', timeout = 7200)
        D8_R9.execute('show mpls ldp summary', timeout = 7200)
        
        D8_R9.execute('show mpls forwarding summary', timeout = 7200)
        D8_R9.execute('show drops all ongoing location all', timeout = 7200)
        D8_R9.execute('show log | i ONLINE_DIAG_FAIL', timeout = 7200)
        D8_R9.execute('show mpls traffic-eng tunnels summary', timeout = 7200)

        D8_R9.execute('show isis topology summary', timeout = 7200)
        D8_R9.execute('show isis segment-routing label table | uti wc lines', timeout = 7200)
        D8_R9.execute('show memory-top-consumers location 0/RP0/CPU0', timeout = 7200)
        D8_R9.execute('show memory-top-consumers location 0/RP1/CPU0', timeout = 7200)
        D8_R9.execute('show mpls traffic-eng tunnel tabular', timeout = 7200)

        D8_R9.execute('run netstat -s | grep -i tcp: -A15', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/RP0/CPU0', timeout = 7200)

        D8_R9.execute('show controllers switch statistics location 0/0/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/1/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/2/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/3/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/4/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/5/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/6/CPU0', timeout = 7200)
        D8_R9.execute('show controllers switch statistics location 0/7/CPU0', timeout = 7200)
        #D8_R9.disconnet()
        time.sleep(10)


class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def upload_log(self):
        pass

