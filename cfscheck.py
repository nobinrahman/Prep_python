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



class CFSCHECK(aetest.Testcase):

    @aetest.test
    def mbblogloop(self,testbed,test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        log.info(genietestbed.devices)

        D18WAN = genietestbed.devices['D18WAN']
        D12W = genietestbed.devices['D12W']
        D4WAN = genietestbed.devices['D4WAN']
        D8WAN = genietestbed.devices['D8WAN']
        D8W = genietestbed.devices['D8W']
        F9 = genietestbed.devices['F9']
        F7 = genietestbed.devices['F7']
        F18 = genietestbed.devices['F18']
        F8 = genietestbed.devices['F8']
        F31 = genietestbed.devices['F31']
        D18_R10 = genietestbed.devices['D18-R10']
        D8_R9 = genietestbed.devices['D8-R9']
        D12_R1 = genietestbed.devices['D12-R1']
        NCS5516_RH = genietestbed.devices['NCS5516-RH']

        D18WAN.connect(via='vty', connection_timeout=600)
        D12W.connect(via='vty', connection_timeout=600)
        D4WAN.connect(via='vty', connection_timeout=600)
        D8WAN.connect(via='vty', connection_timeout=600)
        D8W.connect(via='vty', connection_timeout=600)
        F9.connect(via='vty', connection_timeout=600)
        F7.connect(via='vty', connection_timeout=600)
        F18.connect(via='vty', connection_timeout=600)
        F8.connect(via='vty', connection_timeout=600)
        F31.connect(via='vty', connection_timeout=600)
        D18_R10.connect(via='vty', connection_timeout=600)
        D8_R9.connect(via='vty', connection_timeout=600)
        D12_R1.connect(via='vty', connection_timeout=600)
        NCS5516_RH.connect(via='vty', connection_timeout=600)
        
        
        D18WAN.execute('cfs check', timeout = 7200)
        D18WAN.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D18WAN.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D12W.execute('cfs check', timeout = 7200)
        D12W.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D12W.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D4WAN.execute('cfs check', timeout = 7200)
        D4WAN.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D4WAN.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D8WAN.execute('cfs check', timeout = 7200)
        D8WAN.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D8WAN.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D8W.execute('cfs check', timeout = 7200)
        D8W.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D8W.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        F9.execute('cfs check', timeout = 7200)
        F9.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        F9.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        F7.execute('cfs check', timeout = 7200)
        F7.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        F7.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        F18.execute('cfs check', timeout = 7200)
        F18.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        F18.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        F8.execute('cfs check', timeout = 7200)
        F8.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        F8.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        F31.execute('cfs check', timeout = 7200)
        F31.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        F31.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D18_R10.execute('cfs check', timeout = 7200)
        D18_R10.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D18_R10.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D8_R9.execute('cfs check', timeout = 7200)
        D8_R9.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D8_R9.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        D12_R1.execute('cfs check', timeout = 7200)
        D12_R1.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        D12_R1.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)
        NCS5516_RH.execute('cfs check', timeout = 7200)
        NCS5516_RH.execute('show cfgmgr trace last 50 | i REBASE_LOCK', timeout = 7200)
        NCS5516_RH.execute('show cfgmgr trace | i REBASE_LOCK', timeout = 7200)








class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def upload_log(self):
        pass

