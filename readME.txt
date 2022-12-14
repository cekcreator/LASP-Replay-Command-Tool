Hello! This file entails all the details about "frameCheckTool.py". Includes how to run, with the correct inputs, and details the code itself

**The function using the stac table is commented out, i am keeping it in just incase** 

Why:
    When the satellite resets, the commands during the reset never happen, if resets happen during downlinks then data is still on-board the craft.
    This tool helps generate replay commands for the exposures still on board the craft. 
    Some nuances 
        -if the satellite went down and the GOTO_ECI_ATTITUDE was during the down period the corresponding
        exposures never happened 
        -with going down during when exposures happen, there might still be some exposures taken. 

Things Needed:
    -- frameCheckTool.py: created on Python 3.10.4
        - sub_standards.py: needed for Arikas code parts to the file *file written by Arika*

    -- CUTE JSON Created from the GUI app. 1st cmdline arg
        - remember to remove the first ten lines, up to **"commands": [**  KEEP THE BRACKET THAT YOU SEE IN THIS LINE 
        - remove the corresponding brackets at the end of the JSON plan

    -- times.csv. 2nd cmdline arg
        - or another file with the dates separated by commas, the file itself reads in from a CSV named times.csv

    -- frameID: for 3rd cmd line arg

Example command line: python3 frameCheckTool.py CUTE_Plan_Oct4th.json 5034
                                (file name)      (JSON)              (frameID)

                                2022/270-13:12:55,2022/270-17:55:15,2022/272-06:41:10,2022/272-11:28:40

Code Structure:
    -- Reads in files and cmdline arguments, the JSON and frameIDs are the args the csv must be in the same directory 

    -- notUsingStac (using the json and times provided to generate an ID List):
        - using data frames from pandas I normalized the JSON and the used the .loc() function to find our mnemonic
        - using loops I then found the 'GOTO_ECI_ATTITUDE' mnemonic and appended it to list named == 
        - using the .set_index() func and .to_dict() to create python dictionaries of 
            ~ dct = key: utc_time  value: args.num/num_of_exposures {"utc_time", "args.num"}
            ~ goto = key: utc_time value: mnemonic {"utc_time","mnemonic"}
        - created dicts of just the of the dates and the mnemonics
        - from dctDates (dict) created a 2 lists of the keys and the values respectively
        - looped through these lists and added corresponding times and the cmd to a new dict
            ~ the key is the time of GOTO_ECI_ATTITUDE cmd 
            ~ the value is num_of_exposures and utc_time of the exposure commands
        - looped through checking times vs the times in gotoPpics added the correct times to needed (lists)
        - converted needed to a dict then expanded needed by the num_of_exposures and put into totalDates (dict)
        - then passed to Arikas code to generate replay cmds


Credits:
    Arika Egan - LASP 
    Caleb Kumar - LASP 
