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
import sste_cxr
import sste_common
import sste_trigger
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



class MBBLOG(aetest.Testcase):

    @aetest.test
    def mbblogloop(self,testbed):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        log.info(genietestbed.devices)

        F9 = genietestbed.devices['F9']
        F7 = genietestbed.devices['F7']
        F18 = genietestbed.devices['F18']
        F8 = genietestbed.devices['F8']
        F31 = genietestbed.devices['F31']

        F9.connect(via='vty', connection_timeout=600)
        F7.connect(via='vty', connection_timeout=600)
        F18.connect(via='vty', connection_timeout=600)
        F8.connect(via='vty', connection_timeout=600)
        F31.connect(via='vty', connection_timeout=600)

        from ixnetwork_restpy import SessionAssistant

        session_assistant = SessionAssistant(IpAddress='172.24.78.137', ClearConfig=False)

        ixnetwork = session_assistant.Ixnetwork

        while 1:
            check_context(F9)
            check_context(F7)
            check_context(F18)
            check_context(F8)
            check_context(F31)

            traffic_statistics = session_assistant.StatViewAssistant('Traffic Item Statistics')

            for row in traffic_statistics.Rows:
                name = row['Traffic Item']
                txrate = row['Tx Frame Rate']
                rxrate = row['Rx Frame Rate']
                duration = row['Packet Loss Duration (ms)']
                if abs(float(txrate) - float(rxrate)) / float(txrate) > 0.05:
                    print('CHECKER: ' + name)
                print('Traffic Item: ' + name + '\tTx Rate:' + str(txrate) + '\tRx Rate:' + str(
                    rxrate) + '\tDuration:' + str(duration))

            time.sleep(10)


class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def upload_log(self):
        pass

