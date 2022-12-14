from cmath import nan
from code import compile_command
from ctypes import sizeof
from functools import total_ordering
from hashlib import new
from itertools import count
import json
from operator import length_hint
from types import NoneType 
import pandas
import re
import sys
from sub_standards import num_packets
from sub_standards import get_frameid
import numpy as np
from sub_standards import get_visit_target_frmid_range
from sub_standards import get_blocks
import os
import glob
import matplotlib.pyplot as plt
import datetime as dt
import csv

# dont know if every library is needed but keeping just incase 


# for using the stac table as the first cmd line arg
# with open(sys.argv[1]) as f:
#     lines = f.readlines()

with open(sys.argv[1],'r') as f:
    json = json.loads(f.read())

# pass in the starting frameID as well  frameID = 5034
frameID = int(sys.argv[2])

file = open("times.csv", "r")
times = list(csv.reader(file, delimiter=","))

with open('current_stac_table_22nov13_thru_22dec4.txt') as f:
    lines = f.readlines()

# **
# using times from ops to get unsuccesful exposures, use the times from ops to compare with json, dates in the time frame exclude from replay commands
# possible for multiple times
def notUsingStac(json, datesJSON, frameID, time1, time2):

    # normalizing the json using pandas into a dataframe: df = dataframe
    df = pandas.json_normalize(json)

    dfGoto = df.loc[:, ['mnemonic']].to_dict() # dictionary of command names aka mnemonics 
    
    # going through all the cmd names and finding just the GOTO cmds goto is a list
    goto = []
    for i in dfGoto:
        for j in dfGoto[i]:
            if dfGoto[i][j] == 'GOTO_ECI_ATTITUDE':
                goto.append(dfGoto[i][j])
    

    # gettings dates in a dcitionary with the numIds as keys
    # dict of utc time as keys then num of exposures as value for all cmds
    dctDates = df.set_index(df['utc_time'], df['args.NUM']).to_dict()

    # dict with utc time as keys then cmd names as value
    goto = df.set_index(df['utc_time'], df['mnemonic']).to_dict()   

    # ** THESE MAY NOT BE NEEDED KEEPING JUST INCASE **

    # the index of the rows with the GOTO command
    # goto_rows = [i for i in df.loc[df['mnemonic'] == 'GOTO_ECI_ATTITUDE'].index]
    # getting the times 
    # goto_times = df['utc_time'][goto_rows]

    # **                   ** 

    # dict of the uts times of just the GOTO cmds with their num of 
    timeVSnumExp = dctDates['args.NUM']

    # dict of the commands and their utc times
    dctGoto = goto['mnemonic']

    # will be the dict for the GOTO cmds with their exposure utc times and num exposures
    gotoVSnumExp = {}

    index = 0

    # getting the dates and num exposures from the dct
    lst = list(timeVSnumExp.values())
    lst2 = list(timeVSnumExp.keys())

    # looping through finding the GOTO cmds then adding to the dict the GOTO cmd as the key then the expsure utc times and num exp
    for i,j in zip(dctGoto, timeVSnumExp):
        if dctGoto[i] == 'GOTO_ECI_ATTITUDE':
            gotoVSnumExp[i] = lst2[index + 1],lst[index + 1]
        index += 1
    
    # looping through the cmds and comparing with the times given from ops, adding to the list of needed exposures
    needed = []
    for key in gotoVSnumExp:
        if key < time1 or key > time2:
            needed.append(gotoVSnumExp[key])

    
    # converting the list of utc times and num exp to a dict
    needed = dict(needed)
    
    # combining all into new dict with frameIDS 
    totalDates = {}
    for key in needed:
        if needed[key] > 1 and needed[key] < 10:
            for j in range(int(needed[key])):
                totalDates[frameID] = key
                frameID += 1


    # the list of frameIDS needed to generate replay cmds
    idList = list(totalDates.keys())


    return idList




# ARIKAS CODE MIXED WITH MINE TOWARDS THE END *******
def getFrmIds_LASPStore(idList, frameID):

    visit, vs, ve, ts, te = get_visit_target_frmid_range(frameID)
    print(frameID)

    dk_loc = '/Users/calebkumar/desktop/Kumar_Caleb_CUTE_Work/frameCheckTool/cuteFiles/DARK/'
    bs_loc = '/Users/calebkumar/desktop/Kumar_Caleb_CUTE_Work/frameCheckTool/cuteFiles/BIAS/'
    sc_loc = '/Users/calebkumar/desktop/Kumar_Caleb_CUTE_Work/frameCheckTool/cuteFiles/KELT-9b/'

    # finding all the frames we need
    dk_frms = sorted([i for i in glob.glob(dk_loc+'*.fits') if get_frameid(i) in np.arange(ts, te+1)], key = get_frameid)
    bs_frms = sorted([i for i in glob.glob(bs_loc+'*.fits') if get_frameid(i) in np.arange(ts, te+1)], key = get_frameid)
    sc_frms = sorted([i for i in glob.glob(sc_loc+'*.fits') if get_frameid(i) in np.arange(ts, te+1)], key = get_frameid)
    

    # combing all the frames to one list 
    all_ims = np.concatenate((dk_frms, bs_frms, sc_frms))

    #sort these files in order of when they were madee
    sorted_frames = sorted(all_ims, key = os.path.getmtime)

    #find unique frameids that we have onground
    all_frmids = sorted(np.unique([get_frameid(i) for i in all_ims]))

    #get the number of packets for all of uniq
    num_pks = [num_packets(i) for i in all_ims]

    # fill dks are the frames we are missing
    fil_dks = sorted(np.unique([get_frameid(i) for i in all_ims if num_packets(i) < 440]))

    filled = sorted(np.unique([get_frameid(i) for i in all_ims if num_packets(i) == 446]))

    missing_frmids = [i for i in np.arange(ts, te+1, 1) if i not in all_frmids]

    frames_to_be_filled = sorted(np.concatenate((fil_dks, missing_frmids)))
    
    # MY CODE WHICH SHOULD BE COMPARING MY LIST OF IDS TO ERIKAS LIST OF IDS 
    # creating a list of the ids needed
    # Caleb Code
    needed = []
    # print(fil_dks, "fil_drks")
    for i in idList:
        for j in fil_dks:
            if i == j:
                needed.append(int(j))
    # print(idList, "idlist")
    # print(needed, "needed")

    # finding the gaps in the id list
    diff = np.diff(needed)
    gaps = np.where(diff>1)[0] 

    #use this function to return the start and end values of blocks with gaps larger than 1
    array_blocks = get_blocks(frames_to_be_filled, 1)

    abes = [[i[0], i[-1]] for i in array_blocks]

    #now need to search for single frames
    abes_flat = [item for sublist in array_blocks for item in sublist]
    singles = [i for i in frames_to_be_filled if i not in abes_flat]

    # now format the command to print
    for i in abes:
        file_size = '%.2f'%((i[1] - i[0] + 1)*449/1000)
        print('replay - {} to {}, {} MB, trim2d, nogaps'.format(i[0], i[1], file_size))
    for i in singles:
        file_size = 449/1000
        print('replay - {}, {} MB, trim2d, nogaps'.format(i, file_size))

    return
  

datesJSON = []
i,j,x = 0,0,0
idList2 = []
command = []
# while i != len(times[0]):
#     idList2.append(notUsingStac(json, datesJSON, frameID, times[0][i], times[0][j]))
#     i+=2
#     j+=2
#     x+=1
#     command.append(getFrmIds_LASPStore(idList2[-1]))


    

#                                       ** START OF THE STAC TABLE CODE CURRENTLY NOT NEEDED ** 




# function to find and return all command dates, takes in the json object and a lst to return
def readInFiles(json,lines, datesStac, datesJSON, frameID):

    # reading in the stac table and finind the payload commands, storing both the date and command description IE EXECUTED or whatever else it says
    for i in lines:
        if i[1:2] == "[":
            # print(i[11:28])
            if i[78:99] == 'PLD_CCD_EXPOSE_CLOSED':
                # print(i[31:65])
                datesStac[i[11:28]] = i[31:64]

    
    # normalizing the json using pandas into a dataframe
    df = pandas.json_normalize(json)

    # gettings dates in a dcitionary with the numIds as keys
    # datesJSON = df.loc[:, ['utc_time', 'args.NUM']]
    dct = {}
    
    dct = df.set_index(df['utc_time'], df['args.NUM']).to_dict()
    dctDates = dct['args.NUM']
    # getting only the frames/dates with a number, as some had nan
    totalDates = {}
    for key in dctDates:
        if dctDates[key] > 1 and dctDates[key] < 10:
            for j in range(int(dctDates[key])):
                totalDates[frameID] = key
                frameID += 1

    # comparing the datesStac to totalDates, which is json vs stac table, getting only the commands we want and storing just the frmIDs
    idList = []
    for i in datesStac:
        string = datesStac[i]
        if string[0:8] == "EXECUTED" or string[8:27] == "previously EXECUTED":
            for j in totalDates:
                if i == totalDates[j]:
                    idList.append(j)
    # sorting the ids
    idList = sorted(idList)

    return idList

# # will get date and time of when reset occurs, also a date and time when sci operations rseume 
# # any expose commands between above3 times are not onboard
# # for all ply expose commands if they exist between above times get those ids and exlude them from the list of replay commands

datesStac = {}
idlist3 = readInFiles(json, lines, datesStac, datesJSON, frameID)
getFrmIds_LASPStore(idlist3, frameID)