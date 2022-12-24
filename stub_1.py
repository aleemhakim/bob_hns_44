#!/usr/bin/env python3
import subprocess
import sys,os
import argparse
import logging
import idna
import pandas as pd
import datetime
try:
    import netmiko
except:
    os.system("pip install netmiko")
    import netmiko
import re
from netmiko import ConnectHandler
import time

Username = 'aleem'
Password = 'Sup3r1234!'
I_p = '69.164.214.99'
result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                        password=Password)

uu = input("ti")
today = datetime. datetime. now()
date_time = today.strftime("%Y_%m_%d_%H_%M_%S")

LOGGER = logging.getLogger(__name__)

def arg_collection(args):
    """This function is to collect the arguments
        from the user, includes help if help is triggered
        return help then exit"""

    parser = argparse.ArgumentParser(
        description="This script will take a list of names and output the status of the names"
    )
#    parser.add_argument(
#        "-i",
#        "--input",
#        help="Input file containing list of names",
#        required=True,
#        type=str,
#    )
#    parser.add_argument(
#        #  update to be required if -c/--csv is used
#        "-o",
#        "--output",
#        help="Output file to write results to",
#        required=True,
#        type=str,
#    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose output, will log to /var/log/namerdbin.log",
        required=False,
        action="store_true",
    )
    return parser.parse_args(args)

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="/var/log/namerdbin.log",
    )

def is_punycode(our_string):
    """Tests if string is punycode"""
    try:
        idna.decode(our_string)
    except idna.InvalidCodepoint:
        return True
    except UnicodeError:
        return False
    else:
        return True

def decoded_punycode(our_string):
    """Decodes punycode and returns decoded punycode if possible"""

    try:
        translate = idna.decode(our_string)
        translate = translate.split(",")[0]
    except idna.InvalidCodepoint as e:
        elements = e.args
        translate = elements[0].split("\'")[1]
    return translate

def default_name_data(x):
    print("blah blah blah", x)
    global result
    global Username
    global Password
    global I_p
    """Run hsd-cli to capture state and reserved status of name"""
    try:
        state = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.state")
        print("state is here ", state, " .....")
        y = input("bla bla bla")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        state = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.state")
    try:
        reserved = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .start.reserved")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        reserved = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .start.reserved")
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    state = ansi_escape.sub('', state)
    state = state.strip()
    reserved = ansi_escape.sub('', reserved)
    reserved = reserved.strip()
    print("state: ", state)
    print("reserved: ", reserved)
  #  ghq = input("check this ")
    return state, reserved
# This function will capture data points for "OPENING" auctions
def open_state(x, translate, state, reserved):
    """Capturing and Writing Data for "OPENING" State for {x}"""
    templst = list()
    templst.append(translate)
    templst.append(state)
    templst.append(reserved)
#    print("opennnnnnnn")
    print(x)
    global result
    global Username
    global Password
    global I_p
    """Run hsd-cli to capture state and reserved status of name"""
    try:
        hoursuntilbidding = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilBidding")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        hoursuntilbidding = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilBidding")

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    hoursuntilbidding = ansi_escape.sub('', hoursuntilbidding)
    hoursuntilbidding = hoursuntilbidding.strip()
#    hoursuntilbidding = subprocess.getoutput(
 #       f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilBidding"
  #  )
    templst.append(hoursuntilbidding)
    templst.append("")
    templst.append("")
    templst.append("")
    return templst

def bidding_state(x, translate, state, reserved):
    """Capturing and Writing Data for "BIDDING" State for {x}"""
    templst = list()
    templst.append(translate)
    templst.append(state)
    templst.append(reserved)
    global result
    global Username
    global Password
    global I_p
    try:
        hoursuntilreveal = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilReveal")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        hoursuntilreveal = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilReveal")

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    hoursuntilreveal = ansi_escape.sub('', hoursuntilreveal)
    hoursuntilreveal = hoursuntilreveal.strip()


  #  hoursuntilreveal = subprocess.getoutput(
 #       f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilReveal"
#    )
    templst.append("")
    templst.append(hoursuntilreveal)
    templst.append("")
    templst.append("")
    return templst

def reveal_state(x, translate, state, reserved):
    """Capturing and Writing Data for "REVEAL" State for {x}"""
    templst = list()
    templst.append(translate)
    templst.append(state)
    templst.append(reserved)

    global result
    global Username
    global Password
    global I_p

    try:
        hoursuntilclose = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilClose")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        hoursuntilclose = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilClose")
  #  hoursuntilclose = subprocess.getoutput(
 #       f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilClose"
#    )

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    hoursuntilclose = ansi_escape.sub('', hoursuntilclose)
    hoursuntilclose = hoursuntilclose.strip()

    templst.append("")
    templst.append("")
    templst.append(hoursuntilclose)
    templst.append("")
    return templst

def closed_state(x, translate, state, reserved):
    """Capturing and Writing Data for "CLOSED" State for {x}"""
    templst = list()
    templst.append(translate)
    templst.append(state)
    templst.append(reserved)
    global result
    global Username
    global Password
    global I_p
    try:
        daysuntilexpire = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.daysUntilExpire")
    except:
        result = ConnectHandler(ip=I_p, device_type='autodetect', username=Username,
                                password=Password)
        daysuntilexpire = result.send_command(f"hsd-cli rpc getnameinfo {x}|jq .info.stats.daysUntilExpire")
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    daysuntilexpire = ansi_escape.sub('', daysuntilexpire)
    daysuntilexpire = daysuntilexpire.strip()

#    print(daysuntilexpire)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    daysuntilexpire = ansi_escape.sub('', daysuntilexpire)
    daysuntilexpire = daysuntilexpire.strip()
#    print("daysuntilexpire",daysuntilexpire)
 #   daysuntilexpire = subprocess.getoutput(
  #      f"hsd-cli rpc getnameinfo {x}|jq .info.stats.daysUntilExpire"
   # )
    templst.append("")
    templst.append("")
    templst.append("")
    templst.append(daysuntilexpire)
    return templst

def no_state(translate, state, reserved):
    """Capturing and Writing Data for "NO STATE" State for {x}"""
    templst = list()
    templst.append(translate)
    templst.append(state)
    templst.append(reserved)
    templst.append("")
    templst.append("")
    templst.append("")
    templst.append("")
    return templst

def main(args):
    """Main function"""
    our_arguments = arg_collection(args)
    # collect filename and output file from argparse
    filename = "input2.csv"
    outputfile = "db_input.csv"
    verbose = our_arguments.verbose
#    if verbose:
 #       setup_logging(logging.DEBUG)
  #  else:
   #     setup_logging(logging.INFO)
    #getting the file
    try:
        with open(filename) as f:
            data = f.readlines()[1:]
    except Exception as error:
        LOGGER.error("Input File not found %s", error)
        sys.exit(1)
    data = [x.strip() for x in data]
    print(data)
    t = input("this")
    # if data is empty log error and exit
    if not data:
        LOGGER.error("Input File is empty")
        sys.exit(1)
    if data == "":
        LOGGER.error("Input File is empty")
        sys.exit(1)


    translated = {}
    done = {}
    for x in data:
        print("this", x)
        if is_punycode(x):
            # if x is punycode decode it and store as translate or pass x to translate
            translate = decoded_punycode(x)
        else:
            translate = x
        # Capture default data for all names State and Reserved
        state, reserved = default_name_data(x.lower())

        # for "OPENING" state
        if "OPENING" in state:
            # call "OPENING" function
            templst = open_state(x.lower(), translate, state, reserved)
            translated[x.lower()] = templst
            print("open: ",templst)

        # for "BIDDING" state
        elif "BIDDING" in state:
            # call "BIDDING" function
            templst = bidding_state(x.lower(), translate, state, reserved)
            translated[x.lower()] = templst
            print(templst)

        # for "REVEAL" state
        elif "REVEAL" in state:
           templst = reveal_state(x.lower(), translate, state, reserved)
           translated[x.lower()] = templst
           print(templst)

            # for "CLOSED" state
        elif "CLOSED" in state:
            print("in closse call")
            # call "CLOSED" function
            templst = closed_state(x.lower(), translate, state, reserved)
            translated[x] = templst
            print("closed: ",templst)

        # for all other stateor no data
        else:
            print("no state::::", state," |||| ",reserved)
            # for "NO STATE" or unknown states
            templst = no_state(translate, state, reserved)
            translated[x.lower()] = templst
            print(templst)
        print("...")
        print(translated)

    translated = {
        "name": translated.keys(),
        "decoded_punycode": [a[0] for a in translated.values()],
        "status": [a[1] for a in translated.values()],
        "reserved": [a[2] for a in translated.values()],
        "hoursuntilbidding": [a[3] for a in translated.values()],
        "hoursuntilreveal": [a[4] for a in translated.values()],
        "hoursuntilclose": [a[5] for a in translated.values()],
        "daysuntilexpire": [a[6] for a in translated.values()]
    }
    nlst = []

    for key, value in translated.items():
        for i in value:
            nlst.append(i)
        done[key] = nlst
        nlst = []

        df = pd.DataFrame(done)
        # if -c/--cvs is set write to csv outputfile
        #  if our_arguments.csv:
        print("dataframe: ", df)

        df.to_csv(outputfile, index=None,encoding="utf-8", sep=",")
        print("done")
#        LOGGER.info("Done!")

if __name__ == "__main__":
    """This is executed when run from the command line passing command line arguments to main function"""

    main(sys.argv[1:])