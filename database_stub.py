#!/usr/bin/env python3
import os
import subprocess
from subprocess import Popen, PIPE
import sys
import argparse
import logging
try:
    import idna
except:
    os.system("pip install idna")
    import idna

try:
    import pandas as pd
except:
    os.system("pip install pandas")
    import pandas as pd
import datetime
try:
    from paramiko import SSHClient, AutoAddPolicy
except:
    os.system("pip install paramiko")
    from paramiko import SSHClient, AutoAddPolicy
try:
    import pyodbc
except:
    os.system("pip install pyodbc")
    import pyodbc
try:
    import traceback
except:
    os.system("pip install traceback")
    import traceback

class HSDScheduler():
    def __init__(self):
        self.conn = pyodbc.connect('Driver={SQL Server};'
                                   'Server=(local)\SQLSERVER;'
                                   'Database=HSD;'
                                   'Trusted_Connection=yes;')
        print('Logging in to server')
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        isAuth = False
        try:
            rs = self.client.connect(hostname='69.164.214.99', port=22, username='aleem', password='Sup3r1234!')
            print(rs)
            isAuth = True
            print('Logged into server sucess!!')
        except Exception as e:
            print(str(e))
            print('Login Failed!!')
        if isAuth:
            # stdin, stdout, stderr = self.client.exec_command('hsd-cli rpc getnameinfo')
            # print(stderr.read().decode('utf-8'))
            # print(stdout.read().decode('utf-16'))
            stdin, stdout, stderr = self.client.exec_command(
                f"hsd-cli rpc getnameinfo gigaspeed|jq .info.state"
            )
            print("kkkkk")
            print(str(stdout.read().decode('utf-8')).strip())
            y = input("this")
            self.start()

            # try:
            #     inputDf = pd.read_csv('vdo/output_with_wallet.csv',encoding='utf-16')
            #     self.upload_to_db(inputDf)
            # except Exception as error:
            #     print(traceback.format_exc())
            #     sys.exit(1)
            # self.upload_to_db('sd')
        # self.client.close()
    def start(self):
        filename = "input_with_wallet.csv"
        outputfile = "vdo/output_with_wallet.csv"
        # try:
        #     with open(filename) as f:
        #         data = f.readlines()[1:]
        # except Exception as error:
        #     print("Input File not found %s", error)
        #     sys.exit(1)

        try:
            inputDf = pd.read_csv(filename)
        except Exception as error:
            print("Input File not found %s", error)
            sys.exit(1)

        # data = [x.strip() for x in data]

        translated = {}
        done = {}
        for index, row in inputDf.iterrows():
            x = row['name'].strip()
            print(x)
            if self.is_punycode(x):
                # if x is punycode decode it and store as translate or pass x to translate
                translate = self.decoded_punycode(x)
            else:
                translate = x
            # Capture default data for all names State and Reserved
            state, reserved = self.default_name_data(x.lower())
            # for "OPENING" state
            if state == '"OPENING"':
                # call "OPENING" function
                templst = self.open_state(x.lower(), translate, state, reserved)
                translated[x.lower()] = templst
            # for "BIDDING" state
            elif state == '"BIDDING"':
                # call "BIDDING" function
                templst = self.bidding_state(x.lower(), translate, state, reserved)
                translated[x.lower()] = templst
            # for "REVEAL" state
            elif state == '"REVEAL"':
                templst = self.reveal_state(x.lower(), translate, state, reserved)
                translated[x.lower()] = templst
            # for "CLOSED" state
            elif state == '"CLOSED"':
                # call "CLOSED" function
                templst = self.closed_state(x.lower(), translate, state, reserved)
                translated[x] = templst
            # for all other stateor no data
            else:
                # for "NO STATE" or unknown states
                templst = self.no_state(translate, state, reserved)
                translated[x.lower()] = templst

        translated = {
            "name": translated.keys(),
            # "wallet_id":[a[1] for a in translated.values()],
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
            df['walletID'] = inputDf['walletid']
            # if -c/--cvs is set write to csv outputfile
            #  if our_arguments.csv:
            df.to_csv(outputfile, index=None, encoding="utf-16", sep=",")

        # print(df)
        # print("Done!")
        self.upload_to_db(df)







if __name__ == "__main__":
    # """This is executed when run from the command line passing command line arguments to main function"""
    hsd = HSDScheduler()
    # #main(sys.argv[1:])