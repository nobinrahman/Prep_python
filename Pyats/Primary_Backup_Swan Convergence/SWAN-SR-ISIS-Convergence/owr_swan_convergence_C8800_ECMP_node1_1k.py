#!/bin/env python

import sys

sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
from tabulate import tabulate # New Line
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

def _convert_tcl_list(tcl, delimiters="\s", level=1, currentlevel=0):
    # The function converts a Tcl-based list string into a Python list.
    # It works with embedded lists, and you can set the "level" to control
    # whether nested braces are treated as lists or strings.
    # You can also change the list delimiter.

    # Start by iterating through each character in the string.
    # Identify tokens (words) and append them to the converted list.
    # If a brace or quote, single or double, is encountered, find the matching
    # end brace/quote and recurrsively call "convertTclList" to handle that substring.

    convertedlist     = []          # This is the resulting list that is returned.
    escaped           = False       # The flag is set when a backslash is detected. The following character is always treated as a string.
    token             = ""          # This is used to store each word.
    substringend      = ""          # The stores the character that indicates the end of the current substring.
    substring         = ""          
    sublevel          = 0           # The level of braces for the current character.

    # Currentlevel is an internal variable. The user should not set it, as it keeps track
    # of how many levels deep we are.
    currentlevel += 1

    # Define a regular expression to match the specified delimiters (whitespace by default).
    pattern = "[" + delimiters + "]+"

    # Iterate through each character in the string.
    for character in tcl:
        if character == "\\" and escaped == False:            
            # We have found an escaped character. Just treat it as a normal character.            
            escaped = True

        elif escaped == True:            
            # The previous character was a backslash. That means this is an escaped character, which
            # we simply add as a string.        
            escaped = False
            token += "\\" + character   

        elif (character == "\'" or character == "\"" or character == "{") and substringend == "" and token == "":
            # A new brace or quote has been found. Start constructing a substring that ends
            # when a matching brace/quote is found, and recursively pass the substring to this function.
            if character == "{":
                # We are dealing with an opening brace.
                sublevel += 1
                substringend = "}"
            else:
                # We are dealing with an opening quote.
                substringend = character

        elif character == "{" and substringend == "}":
            # We have found an embedded opening brace. 
            if sublevel > 0:
                # Do not capture the opening brace.
                substring += character
            sublevel += 1

        elif character == "}" and substringend == "}":
            # We have found a closing brace.
            sublevel -= 1
            if sublevel == 0:               
                # This is the closing brace that matching the opening brace for the current substring. 
                if currentlevel <= level:
                    # Convert the substring to a list.
                    sublist = _convert_tcl_list(substring, delimiters, level, currentlevel)
                else:
                    # Treat the substring as a...string.
                    sublist = substring    

                convertedlist.append(sublist)                

                substringend = ""
                substring    = ""
                token        = ""

            else:
                # This is the closing brace for an embedded list. Just continue adding to the substring.
                substring += character

        elif character == substringend and substringend != "":
            # We have found the closing quote for the current substring.
            if currentlevel <= level:
                # Convert the substring to a list.
                sublist = convertTclList(substring, delimiters, level, currentlevel)
            else:
                # Treat the substring as a...string.
                sublist = substring

            convertedlist.append(sublist)

            substringend = ""
            substring    = ""
            token        = ""

        elif substringend != "":
            # We are currently building a substring.
            substring += character                        

        elif re.search(pattern, character):
            # A delimiter has been detected.
            if token != "":
                value = _convert_string_to_value(token)                
                convertedlist.append(value)
                token = ""

        else:
            # Just another character for the current token.
            token += character

    if token != "":        
        # This is to add the last token to the list.
        value = _convert_string_to_value(token)
        convertedlist.append(value)

    return convertedlist

def _convert_string_to_value(string):
    # This function attempts to convert strings into different datatypes (int/float/etc).
    try:
        value = ast.literal_eval(string)
    except:
        value = string
    return value      

def get_drop_duration_drv(test_data):
    """Returns a list of the best-performing and worst-performing flows.
    NOTE: Only a subset of the total flows are returned!
    """

    session_name = test_data['spirent_session_name']
    user_name = test_data['spirent_username']
    session_id = ' - '.join((session_name, user_name))
    labserverip = test_data['spirent_labserver_ip']
    stc = stchttp.StcHttp(labserverip, port='80')

    stc.join_session(session_id)

    port_list_str = stc.get('project1', 'children-port')
    streamblock_list = []
    port_list = []
    for port in port_list_str.split(' '):
        port_list.append(port)
        for streamblock in stc.get(port, 'children-streamblock').split(' '):
            if streamblock != '':
                if 'true' == stc.get(streamblock, 'active'):
                    streamblock_list.append(streamblock)
    
    #print(port_list)
    #print(streamblock_list)
    # To create a DRV
    
    # MGJ: We need to create a "best-performing" and a "worst-performing" DRV.
    result = stc.perform("GetObjects", ClassName="DynamicResultView", Condition="name = 'Frameloss_Duration_Worst'")
    drv_worst = result['ObjectList'].split()

    result = stc.perform("GetObjects", ClassName="DynamicResultView", Condition="name = 'Frameloss_Duration_Best'")
    drv_best = result['ObjectList'].split()    

    if drv_worst + drv_best:
        # We are going to delete any existing DRV, so that we are assured that we are in a known state each time.
        for drv_object in drv_worst + drv_best:
            stc.delete(drv_object)    
        drv_best = None
        drv_worst = None

    if not drv_worst:    
        drv_worst = stc.create('DynamicResultView', under='project1', name='Frameloss_Duration_Worst')
        select_properties = ['StreamBlock.Name', 
                             'StreamBlock.StreamId', 
                             'StreamBlock.TxFrameCount',
                             'StreamBlock.RxFrameCount', 
                             'StreamBlock.Frameloss',
                             'StreamBlock.DroppedFrameDuration',
                             'StreamBlock.DroppedFrameCount',
                             'StreamBlock.IsExpected']
        conditions = "{StreamBlock.DroppedFrameCount > 0 AND StreamBlock.IsExpected = 1}" ############ This is the condition to filter drop which is more than 0 ########
        drvResultQ = stc.create('PresentationResultQuery', under=drv_worst, name='Frameloss_Duration', LimitSize=100)
        stc.config(drvResultQ, SelectProperties=select_properties, 
                               WhereConditions=conditions, 
                               SortBy="{StreamBlock.DroppedFrameCount DESC}",
                               FromObjects=streamblock_list, 
                               DisableAutoGrouping=False)
        # To subscribe to DRV
        stc.perform('SubscribeDynamicResultViewCommand', DynamicResultView=drv_worst)
        stc.apply()

    if not drv_best:    
        drv_best = stc.create('DynamicResultView', under='project1', name='Frameloss_Duration_Best')
        select_properties = ['StreamBlock.Name', 
                             'StreamBlock.StreamId', 
                             'StreamBlock.TxFrameCount',
                             'StreamBlock.RxFrameCount', 
                             'StreamBlock.Frameloss',
                             'StreamBlock.DroppedFrameDuration',
                             'StreamBlock.DroppedFrameCount',
                             'StreamBlock.IsExpected']
        conditions = "{StreamBlock.DroppedFrameCount > 0 AND StreamBlock.IsExpected = 1}" ############ This is the condition to filter drop which is more than 0 ########
        drvResultQ = stc.create('PresentationResultQuery', under=drv_best, name='Frameloss_Duration', LimitSize=100)
        stc.config(drvResultQ, SelectProperties=select_properties, 
                               WhereConditions=conditions, 
                               SortBy="{StreamBlock.DroppedFrameCount ASC}",  
                               FromObjects=streamblock_list, 
                               DisableAutoGrouping=False)
        # To subscribe to DRV
        stc.perform('SubscribeDynamicResultViewCommand', DynamicResultView=drv_best)
        stc.apply()


    stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_worst)
    stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_best)

    # Deal with the worst performing flows first.
    result_list = []
    for result in stc.get(drv_worst,"children-PresentationResultQuery").split():
        columns = stc.get(result, 'SelectProperties').split()
        for view in stc.get(result, "children-resultviewdata").split():
            if stc.get(view, "IsDummy") != "true":
                data_string = stc.get(view, "ResultData")
                data = _convert_tcl_list(data_string, level=0)
                resultdict = dict(zip(columns, data))
                result_list.append(resultdict)        

                log.info(str(resultdict))

    # Now add the best performing flows.
    for result in stc.get(drv_best,"children-PresentationResultQuery").split():
        columns = stc.get(result, 'SelectProperties').split()
        for view in stc.get(result, "children-resultviewdata").split():
            if stc.get(view, "IsDummy") != "true":
                data_string = stc.get(view, "ResultData")
                data = _convert_tcl_list(data_string, level=0)
                resultdict = dict(zip(columns, data))
                result_list.append(resultdict)        

                log.info(str(resultdict))
                  
    return result_list       

def get_values(keyword):
    T19 = "0"
    flowoutput_default = []
    flowoutput_scavenger = []
    print(f"Processing Keyword : '{keyword}'")
    for result in get_drop_duration_drv(test_data):
        streamblock_name = result["StreamBlock.Name"]
        duration = float(result["StreamBlock.DroppedFrameDuration"])

        if 'Default' in streamblock_name and keyword in streamblock_name: 
            flowoutput_default.append(float(duration))
        if 'Scavenger' in streamblock_name and keyword in streamblock_name:
            flowoutput_scavenger.append(float(duration))

        print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")

        if float(duration) > float(T19):
            T19 = str(duration)

    log.info(f"Processing Keyword : '{keyword}'")
    log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
    log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
    sorted(flowoutput_scavenger)
    sorted(flowoutput_default)
    flowscavenger_sort = sorted(flowoutput_scavenger)
    flowdefault_sort = sorted(flowoutput_default)

    if len(flowdefault_sort) == 0:
        flowdefault_sort.append("0")
    if len(flowscavenger_sort) == 0:
        flowscavenger_sort.append("0")

    log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
    log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)

    log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
    log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])

    DBF = float(flowdefault_sort[0]) / 1000000            
    DWF = float(flowdefault_sort[-1]) / 1000000

    
    log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
    log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])

    SBF = float(flowscavenger_sort[0]) / 1000000
    SWF = float(flowscavenger_sort[-1]) / 1000000

    log.info('####T19:' + T19)
    Aggrigate = float(T19) / 1000000

    return [DBF, DWF, SBF, SWF, Aggrigate]

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
                args['sste_commands'] = ['show appmgr source-table']
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
class SWAN_Convergence_ECMPv4_4k_Node1(aetest.Testcase):
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
            
            #########Connecting to SwanAgent###########
            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)

            log.info(genietestbed.devices)

            self.controller = genietestbed.devices['dhirshah-26']
            self.controller.connect(via='linux')
            self.controller.execute('unset http_proxy')
            self.controller.execute('unset https_proxy')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_empty_fib.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(2)
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_empty_fib.xml | curl -s -X POST http://172.25.124.75:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8_empty_fib.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18_empty_fib.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4_empty_fib.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            time.sleep(10)
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D8W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_swap_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D12W_pop_v4_NonCBF.xml | curl -s -X POST http://172.25.124.76:10000/instance/1/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/v4-ecmp-2nh-per-class-no-noncbf-250.xml | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: #gzip" --data-binary @-; echo;')
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            #self.controller.execute('gzip -c /root/CBF_Only/734-40/OWR-734-50/D4-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.79:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            
            self.controller.execute('gzip -c /root/MBB_MASTER/EXPLICIT_NULLV6_D18-4NH-500V4-500V6-to-250-V6-V4-ECMP.xml | curl -s -X POST http://172.25.124.54:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR5/OWR5_D8W2_MIXED.XML | curl -s -X POST http://172.25.124.74:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/OWR3/OWR3_D8W_MIXED.XML | curl -s -X POST http://172.25.124.72:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/MBB_MASTER/MIXED/D12W_MASTER/D12W_MASTER_MIXED.xml | curl -s -X POST http://172.25.124.75:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')
            self.controller.execute('gzip -c /root/MBB_MASTER/PRIMARY_BACKUP_MIXED/ECMP/OWR1/OWR1_D8WAN_SLICE_ECMP.XML | curl -s -X POST http://172.25.124.52:10000/flowtable -H "Content-Type:text/xml" -H "Content-Encoding: gzip" --data-binary @-; echo;')            

            self.controller.disconnect()



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)
            
            while 1:
                output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
                if output.count('1000'):
                    break
                time.sleep(5)
            

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_NH."))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)


        data_swan = []
        data_isis = []
        data_sr = []           

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                # print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#            
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            
#            #pdb.set_trace()
#            
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF1 = float(flowdefault_sort[0]) / 1000000            
#            DWF1 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])            
#
#            SBF1 = float(flowscavenger_sort[0]) / 1000000
#            SWF1 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate1 = float(T19) / 1000000


            data_swan.append(["Ingress_Default_Primary_NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Primary_NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Primary_NH","Shut"].extend(get_values(keyword="SR")))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_NH."))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                #print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#            DBF2 = float(flowdefault_sort[0]) / 1000000            
#            DWF2 = float(flowdefault_sort[-1]) / 1000000
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])            
#
#            SBF2 = float(flowscavenger_sort[0]) / 1000000
#            SWF2 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate2 = float(T19) / 1000000


            data_swan.append(["Ingress_Default_Primary_NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Primary_NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Primary_NH","NoShut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28001 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                #print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#            
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#            DBF3 = float(flowdefault_sort[0]) / 1000000            
#            DWF3 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])            
#
#            SBF3 = float(flowscavenger_sort[0]) / 1000000
#            SWF3 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate3 = float(T19) / 1000000


            data_swan.append(["Ingress_Default_Primary_2NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Primary_2NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Primary_2NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000-28001 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF4 = float(flowdefault_sort[0]) / 1000000            
#            DWF4 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF4 = float(flowscavenger_sort[0]) / 1000000
#            SWF4 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate4 = float(T19) / 1000000

            data_swan.append(["Ingress_Default_Primary_2NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Primary_2NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Primary_2NH","NoShut"].extend(get_values(keyword="SR")))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Primary_NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    
        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF5 = float(flowdefault_sort[0]) / 1000000            
#            DWF5 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF5 = float(flowscavenger_sort[0]) / 1000000
#            SWF5 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate5 = float(T19) / 1000000
#
 
            data_swan.append(["Ingress_Scavenger_Primary_NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Primary_NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Primary_NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Primary_NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF6 = float(flowdefault_sort[0]) / 1000000            
#            DWF6 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF6 = float(flowscavenger_sort[0]) / 1000000
#            SWF6 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate6 = float(T19) / 1000000

            data_swan.append(["Ingress_Scavenger_Primary_NH","No Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Primary_NH","No Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Primary_NH","No Shut"].extend(get_values(keyword="SR")))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Primary_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28002-28003 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF7 = float(flowdefault_sort[0]) / 1000000            
#            DWF7 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF7 = float(flowscavenger_sort[0]) / 1000000
#            SWF7 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate7 = float(T19) / 1000000

            data_swan.append(["Ingress_Scavenger_Primary_2NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Primary_2NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Primary_2NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Primary_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28002-28003 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF8 = float(flowdefault_sort[0]) / 1000000            
#            DWF8 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF8 = float(flowscavenger_sort[0]) / 1000000
#            SWF8 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate8 = float(T19) / 1000000


            data_swan.append(["Ingress_Scavenger_Primary_2NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Primary_2NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Primary_2NH","NoShut"].extend(get_values(keyword="SR")))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Primary_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28003 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF9 = float(flowdefault_sort[0]) / 1000000            
#            DWF9 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF9 = float(flowscavenger_sort[0]) / 1000000
#            SWF9 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate9 = float(T19) / 1000000

            data_swan.append(["Ingress_Primary_4NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Primary_4NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Primary_4NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Primary_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000-28003 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############ 


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF10 = float(flowdefault_sort[0]) / 1000000            
#            DWF10 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF10 = float(flowscavenger_sort[0]) / 1000000
#            SWF10 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate10 = float(T19) / 1000000

            data_swan.append(["Ingress_Primary_4NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Primary_4NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Primary_4NH","NoShut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28001,28004-28005 shutdown"]
                                            
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF11 = float(flowdefault_sort[0]) / 1000000            
#            DWF11 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF11 = float(flowscavenger_sort[0]) / 1000000
#            SWF11 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate11 = float(T19) / 1000000

            data_swan.append(["Ingress_Default_4NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_4NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_4NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000-28001,28004-28005 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF12 = float(flowdefault_sort[0]) / 1000000            
#            DWF12 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF12 = float(flowscavenger_sort[0]) / 1000000
#            SWF12 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate12 = float(T19) / 1000000

            data_swan.append(["Ingress_Default_4NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_4NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_4NH","NoShut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28002-28003,28006-28007 shutdown"]
 
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF13 = float(flowdefault_sort[0]) / 1000000            
#            DWF13 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF13 = float(flowscavenger_sort[0]) / 1000000
#            SWF13 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate13 = float(T19) / 1000000
#

            data_swan.append(["Ingress_Scavenger_4NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_4NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_4NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28002-28003,28006-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF14 = float(flowdefault_sort[0]) / 1000000            
#            DWF14 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF14 = float(flowscavenger_sort[0]) / 1000000
#            SWF14 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate14 = float(T19) / 1000000


            data_swan.append(["Ingress_Scavenger_4NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_4NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_4NH","NoShut"].extend(get_values(keyword="SR")))

        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_8NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF15 = float(flowdefault_sort[0]) / 1000000            
#            DWF15 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF15 = float(flowscavenger_sort[0]) / 1000000
#            SWF15 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate15 = float(T19) / 1000000

            data_swan.append(["Ingress_8NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_8NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_8NH","Shut"].extend(get_values(keyword="SR")))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_8NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF16 = float(flowdefault_sort[0]) / 1000000            
#            DWF16 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF16 = float(flowscavenger_sort[0]) / 1000000
#            SWF16 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate16 = float(T19) / 1000000

            data_swan.append(["Ingress_8NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_8NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_8NH","NoShut"].extend(get_values(keyword="SR")))


        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_ALL_Scavenger_Primary_6NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28005 shutdown"]

            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF17 = float(flowdefault_sort[0]) / 1000000            
#            DWF17 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF17 = float(flowscavenger_sort[0]) / 1000000
#            SWF17 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate17 = float(T19) / 1000000

            data_swan.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","Shut"].extend(get_values(keyword="SR")))

        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_ALL_Scavenger_Primary_6NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28005 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF18 = float(flowdefault_sort[0]) / 1000000            
#            DWF18 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF18 = float(flowscavenger_sort[0]) / 1000000
#            SWF18 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate18 = float(T19) / 1000000
#


            data_swan.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_ALL_Scavenger_Primary_6NH","NoShut"].extend(get_values(keyword="SR")))


        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_ALL_Default_Primary_6NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000-28003,28006-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF19 = float(flowdefault_sort[0]) / 1000000            
#            DWF19 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF19 = float(flowscavenger_sort[0]) / 1000000
#            SWF19 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate19 = float(T19) / 1000000


            data_swan.append(["Ingress_Scavenger_ALL_Default_Primary_6NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_ALL_Default_Primary_6NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_ALL_Default_Primary_6NH ","Shut"].extend(get_values(keyword="SR")))

        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_ALL_Default_Primary_6NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000-28003,28006-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF20 = float(flowdefault_sort[0]) / 1000000            
#            DWF20 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF20 = float(flowscavenger_sort[0]) / 1000000
#            SWF20 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate20 = float(T19) / 1000000



            data_swan.append(["Ingress_Scavenger_ALL_Default_Primary_6NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_ALL_Default_Primary_6NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_ALL_Default_Primary_6NH ","NoShut"].extend(get_values(keyword="SR")))



        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_ALL_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28004-28005 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF21 = float(flowdefault_sort[0]) / 1000000            
#            DWF21 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF21 = float(flowscavenger_sort[0]) / 1000000
#            SWF21 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate21 = float(T19) / 1000000


            data_swan.append(["Ingress_Default_Backup_ALL_2NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Backup_ALL_2NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Backup_ALL_2NH","Shut"].extend(get_values(keyword="SR")))


        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_ALL_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28004-28005 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF22 = float(flowdefault_sort[0]) / 1000000            
#            DWF22 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF22 = float(flowscavenger_sort[0]) / 1000000
#            SWF22 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate22 = float(T19) / 1000000


            data_swan.append(["Ingress_Default_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Default_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Default_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="SR")))



        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Backup_ALL_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28006-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF23 = float(flowdefault_sort[0]) / 1000000            
#            DWF23 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF23 = float(flowscavenger_sort[0]) / 1000000
#            SWF23 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate23 = float(T19) / 1000000

            data_swan.append(["Ingress_Scavenger_Backup_ALL_2NH","Shut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Backup_ALL_2NH","Shut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Backup_ALL_2NH","Shut"].extend(get_values(keyword="SR")))


        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Scavenger_Backup_ALL_2NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28006-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF24 = float(flowdefault_sort[0]) / 1000000            
#            DWF24 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF24 = float(flowscavenger_sort[0]) / 1000000
#            SWF24 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate24 = float(T19) / 1000000


            data_swan.append(["Ingress_Scavenger_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Scavenger_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Scavenger_Backup_ALL_2NH","NoShut"].extend(get_values(keyword="SR")))

        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Backup_ALL_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28004-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            
            data_swan.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="SR")))

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

#            T19 = "0"
#            flowoutput_default = []
#            flowoutput_scavenger = []
#
#            for result in get_drop_duration_drv(test_data):
#                streamblock_name = result["StreamBlock.Name"]
#                duration = float(result["StreamBlock.DroppedFrameDuration"])
#
#                if 'Default' in streamblock_name:
#                    flowoutput_default.append(float(duration))
#                if 'Scavenger' in streamblock_name:
#                    flowoutput_scavenger.append(float(duration))
#
#                print(f"Streamblock name is: '{streamblock_name}' and Dropped Frame Duration is: '{duration}' and ******T19: '{T19}'")
#
#                if float(duration) > float(T19):
#                    T19 = str(duration)
#
#            log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
#            log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)
#            sorted(flowoutput_scavenger)
#            sorted(flowoutput_default)
#            flowscavenger_sort = sorted(flowoutput_scavenger)
#            flowdefault_sort = sorted(flowoutput_default)
#
#            if len(flowdefault_sort) == 0:
#                flowdefault_sort.append("0")
#            if len(flowscavenger_sort) == 0:
#                flowscavenger_sort.append("0")
#
#            log.info('FlOWOUTPUT_DEFAULT_SORT: %s' %flowdefault_sort)
#            log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' %flowscavenger_sort)
#
#            log.info ('FLOWOUTPUT_DEFAULT_BEST: %s' %flowdefault_sort[0])
#            log.info ('FLOWOUTPUT_DEFAULT_WORST: %s' %flowdefault_sort[-1])
#
#            DBF25 = float(flowdefault_sort[0]) / 1000000            
#            DWF25 = float(flowdefault_sort[-1]) / 1000000
#
#            
#            log.info ('FLOWOUTPUT_SCAVENGER_BEST: %s' %flowscavenger_sort[0])
#            log.info ('FLOWOUTPUT_SCAVENGER_WORST: %s' %flowscavenger_sort[-1])
#
#            SBF25 = float(flowscavenger_sort[0]) / 1000000
#            SWF25 = float(flowscavenger_sort[-1]) / 1000000
#
#            log.info('####T19:' + T19)
#            Aggrigate25 = float(T19) / 1000000
#
#            Aggrigate25, SWF25, SBF25, DWF25, DBF25 = get_values(keyword="SWAN")

        ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Backup_ALL_4NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28004-28007 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:





            data_swan.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="SWAN")))
            data_isis.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="ISIS")))
            data_sr.append(["Ingress_Backup_ALL_4NH","NoShut"].extend(get_values(keyword="SR")))

#            data = [["Ingress_Default_Primary_NH","Shut", DBF1, DWF1, SBF1, SWF1, Aggrigate1], 
#            ["Ingress_Default_Primary_NH","NoShut", DBF2, DWF2, SBF2, SWF2, Aggrigate2],
#            ["Ingress_Default_Primary_2NH", "Shut", DBF3, DWF3, SBF3, SWF3, Aggrigate3],
#            ["Ingress_Default_Primary_2NH","NoShut", DBF4, DWF4, SBF4, SWF4, Aggrigate4], 
#            ["Ingress_Scavenger_Primary_NH","Shut", DBF5, DWF5, SBF5, SWF5, Aggrigate5], 
#            ["Ingress_Scavenger_Primary_NH","NoShut", DBF6, DWF6, SBF6, SWF6, Aggrigate6],
#            ["Ingress_Scavenger_Primary_2NH","Shut", DBF7, DWF7, SBF7, SWF7, Aggrigate7],
#            ["Ingress_Scavenger_Primary_2NH","NoShut", DBF8, DWF8, SBF8, SWF8, Aggrigate8], 
#            ["Ingress_Primary_4NH","Shut", DBF9, DWF9, SBF9, SWF9, Aggrigate9], 
#            ["Ingress_Primary_4NH","NoShut", DBF10, DWF10, SBF10, SWF10, Aggrigate10],
#            ["Ingress_Default_4NH","Shut", DBF11, DWF11, SBF11, SWF11, Aggrigate11],
#            ["Ingress_Default_4NH","NoShut", DBF12, DWF12, SBF12, SWF12, Aggrigate12],
#            ["Ingress_Scavenger_4NH","Shut", DBF13, DWF13, SBF13, SWF13, Aggrigate13],
#            ["Ingress_Scavenger_4NH","NoShut", DBF14, DWF14, SBF14, SWF14, Aggrigate14],
#            ["Ingress_8NH","Shut", DBF15, DWF15, SBF15, SWF15, Aggrigate15],
#            ["Ingress_8NH","NoShut", DBF16, DWF16, SBF16, SWF16, Aggrigate16],
#            ["Ingress_Default_ALL_Scavenger_Primary_6NH","Shut", DBF17, DWF17, SBF17, SWF17, Aggrigate17],
#            ["Ingress_Default_ALL_Scavenger_Primary_6NH","NoShut", DBF18, DWF18, SBF18, SWF18, Aggrigate18],
#            ["Ingress_Scavenger_ALL_Default_Primary_6NH","Shut", DBF19, DWF19, SBF19, SWF19, Aggrigate19],
#            ["Ingress_Scavenger_ALL_Default_Primary_6NH","NoShut", DBF20, DWF20, SBF20, SWF20, Aggrigate20],
#            ["Ingress_Default_Backup_ALL_2NH","Shut", DBF21, DWF21, SBF21, SWF21, Aggrigate21],
#            ["Ingress_Default_Backup_ALL_2NH","NoShut", DBF22, DWF22, SBF22, SWF22, Aggrigate22],
#            ["Ingress_Scavenger_Backup_ALL_2NH","Shut", DBF23, DWF23, SBF23, SWF23, Aggrigate23],
#            ["Ingress_Scavenger_Backup_ALL_2NH","NoShut", DBF24, DWF24, SBF24, SWF24, Aggrigate24],
#            ["Ingress_Backup_ALL_4NH","Shut", DBF25, DWF25, SBF25, SWF25, Aggrigate25],
#            ["Ingress_Backup_ALL_4NH","NoShut", DBF26, DWF26, SBF26, SWF26, Aggrigate26],
#            ]

            headers = ["Swan Convergence", "Interface", "Default best flow", "Default worst flow", "Scavenger best flow", "Scavenger worst flow", "Aggrigate"]

            # Using the "grid" table format
            table_grid = tabulate(data_swan, headers, tablefmt="grid")
            log.info(banner("ECMP Ingress Node SWAN Convergence"))
            log.info(table_grid)

            with open("swan_data.txt", "wt") as f:
                f.write(table_grid)

            # Using the "grid" table format
            table_grid = tabulate(data_isis, headers, tablefmt="grid")
            log.info(banner("ECMP Ingress Node ISIS Convergence"))
            log.info(table_grid)

            with open("isis_data.txt", "wt") as f:
                f.write(table_grid)

            # Using the "grid" table format
            table_grid = tabulate(data_sr, headers, tablefmt="grid")
            log.info(banner("ECMP Ingress Node SR Convergence"))
            log.info(table_grid)

            with open("sr_data.txt", "wt") as f:
                f.write(table_grid)

            #self.D8WAN.disconnect()
            #self.D18WAN.disconnect()
            #self.D8W.disconnect()



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







