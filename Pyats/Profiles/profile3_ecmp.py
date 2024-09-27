#!/bin/env python

import sys

sys.path.append('cafykit/lib/')

from pyats import aetest
from pyats.aetest.loop import Iteration
from tabulate import tabulate # New Line
import re
import csv
import random
import datetime
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
from statistics import mean

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


def New_Verifier_test(failed, steps, script_args, testscript, testbed, test_data, timing):
    testbed_file = testbed.testbed_file
    genietestbed = load(testbed_file)
    
    log.info(genietestbed.devices)
    
    D8WAN = genietestbed.devices['D8WAN']
    
    try:
        D8WAN.connect(via='vty', connection_timeout=300)
        D8WAN.execute('term length 0', timeout=300)
        D8WAN.execute('term width 0', timeout=300)
    except Exception as e:
        log.error(f"Failed to connect to D8WAN: {str(e)}")
        return
    
    index = 0
    while True:
        try:
            outputDefault = D8WAN.execute('show service-layer mpls label 24000 exp default | in priority', timeout=600)
            outputScavenger = D8WAN.execute('show service-layer mpls label 24000 exp 1 | in priority', timeout=600)
            if outputDefault.count('path up') == 3 and outputScavenger.count('path up') == 4:
                time.sleep(60)
                break
        except Exception as e:
            log.error(f"Error executing commands: {str(e)}")
            break
        
        time.sleep(5)
        index += 1
        if index == 20:
            log.error('###################\nlabels not recovered\n###################')
            break    
    try:
        D8WAN.disconnect()
    except Exception as e:
        log.error(f"Failed to disconnect from D8WAN: {str(e)}")


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


def get_drop_duration_drv_non_zero(test_data):
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

    stc.perform('StreamBlockStop', streamblocklist=streamblock_list)
    time.sleep(5)

    result = stc.perform("GetObjects", ClassName="DynamicResultView", Condition="name = 'Frameloss_Duration_Worst'")
    drv_all = result['ObjectList'].split()

    if drv_all:
        # We are going to delete any existing DRV, so that we are assured that we are in a known state each time.
        for drv_object in drv_all:
            stc.delete(drv_object)
        drv_all = None

    drv_all = stc.create('DynamicResultView', under='project1', name='Frameloss_Duration_Worst')
    select_properties = ['StreamBlock.Name',
                         'StreamBlock.StreamId',
                         'StreamBlock.TxFrameCount',
                         'StreamBlock.RxFrameCount',
                         'StreamBlock.Frameloss',
                         'StreamBlock.FrameLossDuration',
                         'StreamBlock.DroppedFrameCount',
                         'StreamBlock.IsExpected']

    drvResultQ = stc.create('PresentationResultQuery', under=drv_all, name='Frameloss_Duration', LimitSize=2000)

    stc.config(drvResultQ, SelectProperties=select_properties,
               FromObjects=streamblock_list,
               DisableAutoGrouping=False)


    # To subscribe to DRV
    stc.perform('SubscribeDynamicResultViewCommand', DynamicResultView=drv_all)
    time.sleep(5)

    ret = {}
    ret['default'] = []
    ret['scavenger'] = []
    ret['srv4'] = []
    ret['srv6'] = []
    ret['rsvp'] = []

    ####default
    streamblocknames = ['D18WAN-D8W2-V4-SWAN-Convergence-Default-1250',
                        'D18WAN-D12W-V4-SWAN-Convergence-Default-380',
                        'D18WAN-D8W2-V4-SWAN-Convergence-Default-1120',
                        'D18WAN-D8W2-V6-SWAN-Convergence-Default-1250',
                        'D18WAN-D12W-V6-SWAN-Convergence-Default-380',
                        'D18WAN-D8W2-V6-SWAN-Convergence-Default-1120']
    for streamblock in streamblocknames:
        for sb in streamblock_list:
            if stc.get(sb, 'Name') == streamblock:
                break
            else:
                sb = None
        if sb == None:
            print('can not find streamblock handle for : '+streamblock)

        stc.config(drvResultQ, FromObjects=[sb])

        stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_all)
        time.sleep(5)

        # Deal with the worst performing flows first.

        for result in stc.get(drv_all, "children-PresentationResultQuery").split():
            columns = stc.get(result, 'SelectProperties').split()
            for view in stc.get(result, "children-resultviewdata").split():
                if stc.get(view, "IsDummy") != "true":
                    data_string = stc.get(view, "ResultData")
                    data = data_string.split()[5]
                    ret['default'].append(float("{:.3f}".format(float(data)/1000000)))
    #print(ret['default'])
    log.info(ret['default'])

    ####scavenger
    streamblocknames = ['D18WAN-D8W2-V4-SWAN-Convergence-Scavenger-1250',
                        'D18WAN-D12W-V4-SWAN-Convergence-Scavenger-380',
                        'D18WAN-D8W2-V4-SWAN-Convergence-Scavenger-1120',
                        'D18WAN-D8W2-V6-SWAN-Convergence-Scavenger-1250',
                        'D18WAN-D12W-V6-SWAN-Convergence-Scavenger-380',
                        'D18WAN-D8W2-V6-SWAN-Convergence-Scavenger-1120']
    for streamblock in streamblocknames:
        for sb in streamblock_list:
            if stc.get(sb, 'Name') == streamblock:
                break
            else:
                sb = None
        if sb == None:
            print('can not find streamblock handle for : '+streamblock)

        stc.config(drvResultQ, FromObjects=[sb])

        stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_all)
        time.sleep(5)

        # Deal with the worst performing flows first.

        for result in stc.get(drv_all, "children-PresentationResultQuery").split():
            columns = stc.get(result, 'SelectProperties').split()
            for view in stc.get(result, "children-resultviewdata").split():
                if stc.get(view, "IsDummy") != "true":
                    data_string = stc.get(view, "ResultData")
                    data = data_string.split()[5]
                    ret['scavenger'].append(float("{:.3f}".format(float(data)/1000000)))
    #print(ret['scavenger'])
    log.info(ret['scavenger'])

    ####rsvp
    streamblocknames = ['D8WAN-D12W-RSVP-50K-BE28003-Convergence',
                        'D8WAN-D12W-RSVP-50K-BE28002-Convergence',
                        'D8WAN-D12W-RSVP-50K-BE28001-Convergence',
                        'D8WAN-D12W-RSVP-50K-BE28000-Convergence']
    for streamblock in streamblocknames:
        for sb in streamblock_list:
            if stc.get(sb, 'Name') == streamblock:
                break
            else:
                sb = None
        if sb == None:
            print('can not find streamblock handle for : '+streamblock)

        stc.config(drvResultQ, FromObjects=[sb])

        stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_all)
        time.sleep(5)

        # Deal with the worst performing flows first.

        for result in stc.get(drv_all, "children-PresentationResultQuery").split():
            columns = stc.get(result, 'SelectProperties').split()
            for view in stc.get(result, "children-resultviewdata").split():
                if stc.get(view, "IsDummy") != "true":
                    data_string = stc.get(view, "ResultData")
                    data = data_string.split()[5]
                    ret['rsvp'].append(float("{:.3f}".format(float(data)/1000000)))
    #print(ret['rsvp'])
    log.info(ret['rsvp'])

    ####srv4
    streamblocknames = ['D18WAN-D12W-ISIS-SR-Labeled-V4-Convergence-380',
                        'D18WAN-D8W2-ISIS-SR-Labeled-V4-Convergence-1120',
                        'D18WAN-D8W2-ISIS-SR-Labeled-V4-Convergence-1250']
    for streamblock in streamblocknames:
        for sb in streamblock_list:
            if stc.get(sb, 'Name') == streamblock:
                break
            else:
                sb = None
        if sb == None:
            print('can not find streamblock handle for : '+streamblock)

        stc.config(drvResultQ, FromObjects=[sb])

        stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_all)
        time.sleep(5)
        # Deal with the worst performing flows first.

        for result in stc.get(drv_all, "children-PresentationResultQuery").split():
            columns = stc.get(result, 'SelectProperties').split()
            for view in stc.get(result, "children-resultviewdata").split():
                if stc.get(view, "IsDummy") != "true":
                    data_string = stc.get(view, "ResultData")
                    data = data_string.split()[5]
                    ret['srv4'].append(float("{:.3f}".format(float(data)/1000000)))
    #print(ret['srv4'])
    log.info(ret['srv4'])

    ####srv6
    streamblocknames = ['D18WAN-D12W-ISIS-SR-Labeled-V6-Convergence-380',
                        'D18WAN-D8W2-ISIS-SR-Labeled-V6-Convergence-1120',
                        'D18WAN-D8W2-ISIS-SR-Labeled-V6-Convergence-1250']
    for streamblock in streamblocknames:
        for sb in streamblock_list:
            if stc.get(sb, 'Name') == streamblock:
                break
            else:
                sb = None
        if sb == None:
            print('can not find streamblock handle for : '+streamblock)

        stc.config(drvResultQ, FromObjects=[sb])

        stc.perform("UpdateDynamicResultViewCommand", DynamicResultView=drv_all)
        time.sleep(5)

        # Deal with the worst performing flows first.

        for result in stc.get(drv_all, "children-PresentationResultQuery").split():
            columns = stc.get(result, 'SelectProperties').split()
            for view in stc.get(result, "children-resultviewdata").split():
                if stc.get(view, "IsDummy") != "true":
                    data_string = stc.get(view, "ResultData")
                    data = data_string.split()[5]
                    ret['srv6'].append(float("{:.3f}".format(float(data)/1000000)))
    #print(ret['srv6'])
    log.info(ret['srv6'])


 
    ret['default'].sort()
    ret['scavenger'].sort()
    ret['rsvp'].sort()
    ret['srv4'].sort()
    ret['srv6'].sort()

    print(ret)

    # # Sorting and removing zero values from the list
    # sorted_non_zero_values_default = sorted([x for x in ret['default'] if x != 0])
    # #sorted_non_zero_values_scavenger = sorted([x for x in ret['default'] if x != 0])
    # sorted_non_zero_values_srv4 = sorted([x for x in ret['srv4'] if x != 0])
    # sorted_non_zero_values_srv6 = sorted([x for x in ret['srv6'] if x != 0])

    # Handle list: remove zeros if there are non-zero values, otherwise keep as is
    if any(x != 0 for x in ret['default']):
        sorted_non_zero_values_default = sorted(x for x in ret['default'] if x != 0)
    else:
        sorted_non_zero_values_default = ret['default']
    
    if any(x != 0 for x in ret['scavenger']):
        sorted_non_zero_values_scavenger = sorted(x for x in ret['scavenger'] if x != 0)
    else:
        sorted_non_zero_values_scavenger = ret['scavenger']

    if any(x != 0 for x in ret['rsvp']):
        sorted_non_zero_values_rsvp = sorted(x for x in ret['rsvp'] if x != 0)
    else:
        sorted_non_zero_values_rsvp = ret['rsvp']

    if any(x != 0 for x in ret['srv4']):
        sorted_non_zero_values_srv4 = sorted(x for x in ret['srv4'] if x != 0)
    else:
        sorted_non_zero_values_srv4 = ret['srv4']

    if any(x != 0 for x in ret['srv6']):
        sorted_non_zero_values_srv6 = sorted(x for x in ret['srv6'] if x != 0)
    else:
        sorted_non_zero_values_srv6 = ret['srv6']

    ####[BEST,AVG,WORST]
    returnDict = {}
    returnDict['default'] = [str(sorted_non_zero_values_default[0]),str("{:.3f}".format(mean(sorted_non_zero_values_default))),str(sorted_non_zero_values_default[-1])]
    # returnDict['scavenger'] = [str(ret['scavenger'][0]),str("{:.3f}".format(mean(ret['scavenger']))),str(ret['scavenger'][-1])]
    returnDict['scavenger'] = [str(sorted_non_zero_values_scavenger[0]),str("{:.3f}".format(mean(sorted_non_zero_values_scavenger))),str(sorted_non_zero_values_scavenger[-1])]
    # returnDict['srv4'] = [str(ret['srv4'][0]),str("{:.3f}".format(mean(ret['srv4']))),str(ret['srv4'][-1])]
    returnDict['rsvp'] = [str(sorted_non_zero_values_rsvp[0]),str("{:.3f}".format(mean(sorted_non_zero_values_rsvp))),str(sorted_non_zero_values_rsvp[-1])]
    # returnDict['srv6'] = [str(ret['srv6'][0]),str("{:.3f}".format(mean(ret['srv6']))),str(ret['srv6'][-1])]
    returnDict['srv4'] = [str(sorted_non_zero_values_srv4[0]),str("{:.3f}".format(mean(sorted_non_zero_values_srv4))),str(sorted_non_zero_values_srv4[-1])]
    # returnDict['rsvp'] = [str(ret['rsvp'][0]),str("{:.3f}".format(mean(ret['rsvp']))),str(ret['rsvp'][-1])]
    returnDict['srv6'] = [str(sorted_non_zero_values_srv6[0]),str("{:.3f}".format(mean(sorted_non_zero_values_srv6))),str(sorted_non_zero_values_srv6[-1])]

    log.info('Debug: this is step 6. Abort the script')
    time.sleep(30)
    stc.perform('ResultClearAllTrafficCommand')
    time.sleep(5)

    stc.perform('StreamBlockStart', streamblocklist=streamblock_list)
    time.sleep(5)

    return returnDict


def get_values_non_zero(test_data):


    # Call get_drop_duration_drv only once and store the result
    drop_duration_data = get_drop_duration_drv_non_zero(test_data)

    # Get sorted values from the dictionary returned by get_drop_duration_drv
    sorted_default = drop_duration_data['default']
    sorted_scavenger = drop_duration_data['scavenger']

    sorted_srv4 = drop_duration_data['srv4']
    sorted_srv6 = drop_duration_data['srv6']
    sorted_rsvp = drop_duration_data['rsvp']


######################################### SWAN Measurement ######################################### 
    # Use sorted values directly in your logic
    log.info('FlOWOUTPUT_DEFAULT_SORT: %s' % sorted_default)
    log.info('FLOWOUTPUT_SCAVENGER_SORT: %s' % sorted_scavenger)

    log.info('FLOWOUTPUT_DEFAULT_BEST: %s' % sorted_default[0])
    log.info('FLOWOUTPUT_DEFAULT_WORST: %s' % sorted_default[-1])
    log.info('FLOWOUTPUT_DEFAULT_AGGREGATE: %s' % sorted_default[1])

    DBF = float(sorted_default[0])          
    DWF = float(sorted_default[-1])
    DAG = float(sorted_default[1])

    log.info('FLOWOUTPUT_SCAVENGER_BEST: %s' % sorted_scavenger[0])
    log.info('FLOWOUTPUT_SCAVENGER_WORST: %s' % sorted_scavenger[-1])
    log.info('FLOWOUTPUT_SCAVENGER_AGGREGATE: %s' % sorted_scavenger[1])


    SBF = float(sorted_scavenger[0])
    SWF = float(sorted_scavenger[-1])
    SAG = float(sorted_scavenger[1])


######################################### ISIS-SR Measurement ######################################### 
    log.info('FlOWOUTPUT_V4_SORT: %s' %sorted_srv4)
    log.info('FLOWOUTPUT_V6_SORT: %s' %sorted_srv6)

    log.info ('FLOWOUTPUT_V4_BEST: %s' %sorted_srv4[0])
    log.info ('FLOWOUTPUT_V4_WORST: %s' %sorted_srv4[-1])
    log.info ('FLOWOUTPUT_V4_AGGREGATE: %s' %sorted_srv4[1])

    V4BF = float(sorted_srv4[0])           
    V4WF = float(sorted_srv4[-1])
    V4AG = float(sorted_srv4[1])

    
    log.info ('FLOWOUTPUT_V6_BEST: %s' %sorted_srv6[0])
    log.info ('FLOWOUTPUT_V6_WORST: %s' %sorted_srv6[-1])
    log.info ('FLOWOUTPUT_V6_AGGREGATE: %s' %sorted_srv6[1])

    V6BF = float(sorted_srv6[0])
    V6WF = float(sorted_srv6[-1])
    V6AG = float(sorted_srv6[1])

######################################### RSVP Measurement ######################################### 
    
    log.info('flowoutput_rsvp_SORT: %s' %sorted_rsvp)

    log.info ('flowoutput_rsvp_BEST: %s' %sorted_rsvp[0])
    log.info ('flowoutput_rsvp_WORST: %s' %sorted_rsvp[-1])
    log.info ('flowoutput_rsvp_AGGREGATE: %s' %sorted_rsvp[1])

    RBF = float(sorted_rsvp[0])            
    RWF = float(sorted_rsvp[-1])
    RAG = float(sorted_rsvp[1])

    return [DAG, DBF, DWF, SAG, SBF, SWF, V4AG, V4BF, V4WF, V6AG, V6BF, V6WF, RAG, RBF, RWF]


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
class Profile3_ECMP(aetest.Testcase):
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
            self.controller.execute('cd /root/MBB_MASTER/MIXED && ./profile3_ecmp.sh', timeout = 300)
            time.sleep(30)            

            self.controller.disconnect()



            testbed_file = testbed.testbed_file
            genietestbed = load(testbed_file)
    
            log.info(genietestbed.devices)
    
            self.D8WAN = genietestbed.devices['D8WAN']
            self.D8WAN.connect(via='vty',connection_timeout=300)
            
            output= self.D8WAN.execute('show mpls forwarding labels 24000 24999 | in BE | utility wc lines', timeout = 300)
            self.D8WAN.disconnect()
        
        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)   

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)


        data_swan = []
        data_isis = []
        data_rsvp = []           

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            data_swan.append(["Ingress_Default_Primary_NH","Shut"] + get_values_non_zero(test_data))



            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Primary_NH"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args) 

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)



        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            data_swan.append(["Ingress_Default_Primary_NH","NoShut"] + get_values_non_zero(test_data))



            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_NH_Weight1"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28001 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Default_Backup_NH_Weight1","Shut"] + get_values_non_zero(test_data))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_NH_Weight1"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28001 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args) 

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            data_swan.append(["Ingress_Default_Backup_NH_Weight1","NoShut"] + get_values_non_zero(test_data))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_NH_Weight31"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Default_Backup_NH_Weight31","Shut"] + get_values_non_zero(test_data))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_NH_Weight31"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args) 

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            data_swan.append(["Ingress_Default_Backup_NH_Weight31","NoShut"] + get_values_non_zero(test_data))



            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_All_2NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28001-28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    
        if 'tgn' in test_data and 'spirent' == test_data['tgn']: 
            data_swan.append(["Ingress_Default_Backup_All_2NHs","Shut"] + get_values_non_zero(test_data))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_Backup_All_2NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28001-28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args)           

            ############ MPLS Label check on D8WAN ############
            


        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Default_Backup_All_2NHs","No Shut"] + get_values_non_zero(test_data))



            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Primary_Backup_2NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000,28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############
    

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Primary_Backup_2NHs","Shut"] + get_values_non_zero(test_data))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Primary_Backup_2NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000,28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)


            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args) 

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Primary_Backup_2NHs","NoShut"] + get_values_non_zero(test_data))


            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")

            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_All_3NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["interface Bundle-Ether 28000,28001,28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(90)

            ############ MPLS Label check on D8WAN ############

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Default_All_3NHs","Shut"] + get_values_non_zero(test_data))

            ##############  Triggers on D12W ################

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:

            log.info("Clear Traffic Stats")
            sste_tgn.tgn_clear_stats(script_args, test_data)

            ###################### SHUT_INTERFACE ######################
            log.info(banner("Ingress_Default_All_3NHs"))
            module_args = {}
            module_args['timeout'] = 300
            module_args['sste_commands'] = ["no interface Bundle-Ether 28000,28001,28002 shutdown"]
            output = sste_common.config_commands(module_args, script_args)
            time.sleep(100)

        New_Verifier_test(self.failed, steps, script_args, testscript, testbed, test_data, timing)

            # module_args = {}
            # module_args['timeout'] = 300
            # module_args['sste_commands'] = ["show mpls traffic-eng fast-reroute database summary"]
            # sste_common.exec_commands(module_args, script_args) 
            ############ MPLS Label check on D8WAN ############ 

        if 'tgn' in test_data and 'spirent' == test_data['tgn']:
            data_swan.append(["Ingress_Default_All_3NHs","No Shut"] + get_values_non_zero(test_data))

           
            ################################### Trigger Ends ###################################


            headers_swan = ["Swan Convergence", "Interface", "Aggregate", "Default best flow", "Default worst flow", "Aggregate", "Scavenger best flow", "Scavenger worst flow", "Aggregate", "ISISv4 best flow", "ISISv4 worst flow", "Aggregate", "ISISv6 best flow", "ISISv6 worst flow", "Aggregate", "RSVP best flow", "RSVP worst flow"]

            # Using the "grid" table format
            table_grid = tabulate(data_swan, headers_swan, tablefmt="grid")
            log.info(banner("Profile3_ECMP_SWAN_Convergence"))
            log.info(table_grid)

            file_path_swan = "/scratch/msftcvtauto/WAN/SWAN/CONVERGENCE/Logs/profile3_ecmp.csv"

            # Writing to CSV
            with open(file_path_swan, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Testcases', 'Trigger', 'Aggregate', 'Best Flow', 'Worst Flow','Aggregate', 'Best Flow', 'Worst Flow','Aggregate', 'Best Flow', 'Worst Flow','Aggregate', 'Best Flow', 'Worst Flow','Aggregate', 'Best Flow', 'Worst Flow',])
                writer.writerows(data_swan)


            # if 'tgn' in test_data:
            #     log.info('Take_traffic_snapshot_after_trigger')
            #     ret_val = Take_traffic_snapshot_after_trigger(steps, script_args, testbed, test_data)
            #     log.info(ret_val)
            #     if ret_val:
            #         log.info("traffic converged equals to : {}".format(ret_val))
            #     else:
            #         show_tech(script_args)
            #         self.failed("traffic not converged")
        log.info(banner("Table is saved in /scratch/msftcvtauto/WAN/SWAN/CONVERGENCE/Logs directory"))
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







