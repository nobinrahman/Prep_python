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
    def mbblogloop(self,testbed,test_data):
        testbed_file = testbed.testbed_file
        genietestbed = load(testbed_file)

        log.info(genietestbed.devices)

        D18WAN = genietestbed.devices['D18WAN']
        D12W = genietestbed.devices['D12W']
        D4WAN = genietestbed.devices['D4WAN']
        D8WAN = genietestbed.devices['D8WAN']
        D8W = genietestbed.devices['D8W']

        D18WAN.connect(via='vty', connection_timeout=600)
        D12W.connect(via='vty', connection_timeout=600)
        D4WAN.connect(via='vty', connection_timeout=600)
        D8WAN.connect(via='vty', connection_timeout=600)
        D8W.connect(via='vty', connection_timeout=600)

        #from ixnetwork_restpy import SessionAssistant

        #session_assistant = SessionAssistant(IpAddress='172.24.78.137', ClearConfig=False)

        #ixnetwork = session_assistant.Ixnetwork

        while 1:
            check_context(D18WAN)
            check_context(D12W)
            check_context(D4WAN)
            check_context(D8WAN)
            check_context(D8W)

            if 'tgn' in test_data and 'spirent' == test_data['tgn']:
                T19 = "0"
                flowoutput_default = []
                flowoutput_scavenger = []
                for result in get_drop_duration_drv(test_data):
                    streamblock_name = result["StreamBlock.Name"]
                    duration = float(result["StreamBlock.DroppedFrameDuration"])

                    '''if 'Default' in streamblock_name:
                        flowoutput_default.append(float(duration))
                    if 'Scavenger' in streamblock_name:
                        flowoutput_scavenger.append(float(duration))
                    if float(duration) > float(T19):
                        T19 = str(duration)
                log.info('FlOWOUTPUT_DEFAULT: %s' %flowoutput_default)
                log.info('FLOWOUTPUT_SCAVENGER: %s' %flowoutput_scavenger)'''

            '''for row in traffic_statistics.Rows:
                name = row['Traffic Item']
                txrate = row['Tx Frame Rate']
                rxrate = row['Rx Frame Rate']
                duration = row['Packet Loss Duration (ms)']
                if abs(float(txrate) - float(rxrate)) / float(txrate) > 0.05:
                    print('CHECKER: ' + name)
                print('Traffic Item: ' + name + '\tTx Rate:' + str(txrate) + '\tRx Rate:' + str(
                    rxrate) + '\tDuration:' + str(duration))'''

            time.sleep(10)


class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def upload_log(self):
        pass

