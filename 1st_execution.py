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
try:
    import mysql.connector
except:
    os.system("pip install mysql-connector-python")
    import mysql.connector

today = datetime.datetime.now()
date_time = today.strftime("%Y_%m_%d_%H_%M_%S")
class HSDScheduler():
    def __init__(self):
        self.conn= mysql.connector.connect(
          host="localhost",
          user="root",
          password="",
          database = "testDB"
        )
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
#            u = input("this")
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
        filename = "input2.csv"
        outputfile = "output_with_wallet.csv"
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
            print("this: ",x)
            if self.is_punycode(x):
                # if x is punycode decode it and store as translate or pass x to translate
                translate = self.decoded_punycode(x)
            else:
                translate = x
            # Capture default data for all names State and Reserved
            state, reserved = self.default_name_data(x.lower())
            print("thi")

            print(state,reserved)
            print("thi")
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

    def is_punycode(self, our_string):
        """Tests if string is punycode"""

        try:
            idna.decode(our_string)

        except idna.InvalidCodepoint:
            return True
        except UnicodeError:
            return False
        else:
            return True

    def decoded_punycode(self, our_string):
        """Decodes punycode and returns decoded punycode if possible"""

        try:
            translate = idna.decode(our_string)
            translate = translate.split(",")[0]
        except idna.InvalidCodepoint as e:
            elements = e.args
            translate = elements[0].split("\'")[1]
        return translate

    def default_name_data(self, x):
        """Run hsd-cli to capture state and reserved status of name"""
        # in the future this will run once to capture each names data and parse from there
        # using hsd-cli rpc getnameinfo {x} --json
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .info.state"
        )
        state = str(stdout.read().decode('utf-8')).strip()
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .start.reserved"
        )
        reserved = str(stdout.read().decode('utf-8')).strip()
        return state, reserved

    def open_state(self, x, translate, state, reserved):
        """Capturing and Writing Data for "OPENING" State for {x}"""
        templst = list()
        templst.append(translate)
        templst.append(state)
        templst.append(reserved)
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilBidding"
        )
        hoursuntilbidding = str(stdout.read().decode('utf-8')).strip()
        templst.append(hoursuntilbidding)
        templst.append("")
        templst.append("")
        templst.append("")
        return templst

    def bidding_state(self, x, translate, state, reserved):
        """Capturing and Writing Data for "BIDDING" State for {x}"""
        templst = list()
        templst.append(translate)
        templst.append(state)
        templst.append(reserved)
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilReveal"
        )
        hoursuntilreveal = str(stdout.read().decode('utf-8')).strip()
        templst.append("")
        templst.append(hoursuntilreveal)
        templst.append("")
        templst.append("")
        return templst

    def reveal_state(self, x, translate, state, reserved):
        """Capturing and Writing Data for "REVEAL" State for {x}"""
        templst = list()
        templst.append(translate)
        templst.append(state)
        templst.append(reserved)
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .info.stats.hoursUntilClose"
        )
        hoursuntilclose = str(stdout.read().decode('utf-8')).strip()
        templst.append("")
        templst.append("")
        templst.append(hoursuntilclose)
        templst.append("")
        return templst

    def closed_state(self, x, translate, state, reserved):
        """Capturing and Writing Data for "CLOSED" State for {x}"""
        templst = list()
        templst.append(translate)
        templst.append(state)
        templst.append(reserved)
        stdin, stdout, stderr = self.client.exec_command(
            f"hsd-cli rpc getnameinfo {x}|jq .info.stats.daysUntilExpire"
        )
        daysuntilexpire = str(stdout.read().decode('utf-8')).strip()
        templst.append("")
        templst.append("")
        templst.append("")
        templst.append(daysuntilexpire)
        return templst

    def no_state(self, translate, state, reserved):
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

    def upload_to_db(self, df):
        print('Uploading To DB...')
        rows = []
        count = 0
        for index, row in df.iterrows():
            count = count + 1
            # print(row['walletID'])
            # print(row['decoded_punycode'])
            # print(str(row['status']).replace('"',""))
            # print(row['reserved'])
            # print(row['hoursuntilbidding'])
            # print(row['hoursuntilreveal'])
            # print(row['hoursuntilclose'])
            # print(row['daysuntilexpire'])
            rows.append([row['name'],
                         str(row['walletID']),
                         str(row['decoded_punycode']),
                         str(row['status']).replace('"', ""),
                         str(row['reserved']),
                         str(row['hoursuntilbidding']),
                         str(row['hoursuntilreveal']),
                         str(row['hoursuntilclose']),
                         str(row['daysuntilexpire'])])

            if count % 50 == 0:
                self.searchAndUploadData(rows)
                rows = []
        for row in rows:
            print("next")
            for u in row:
                print(type(u), " : ", u)
            # break
        self.searchAndUploadData(rows)

    def searchAndUploadData(self, rows):
        # print(rows)
        try:
            NewData = []
            data = ""
            data_to_be_inserted = ""
            for row in rows:
                data = data + "("
                data = data + "'" + row[0] + "','" + row[1] + "'),"

                data_to_be_inserted = data_to_be_inserted + "("
                data_to_be_inserted = data_to_be_inserted + "'" + row[0] + "','" + row[1] + "','" + row[2] + "','" + \
                                      row[3] + "','" + row[4] + "','" + row[5] + "','" + row[6] + "','" + row[
                                          7] + "','" + row[8] + "'" + "),"

            data = data[:-1]
            data_to_be_inserted = data_to_be_inserted[:-1]
            # print(data_to_be_inserted)
            # return
            # print(data_to_be_inserted)
            # return 1

            # row['walletID'],
            # row['decoded_punycode'],
            # str(row['status']).replace('"', ""),
            # row['reserved'],
            # row['hoursuntilbidding'],
            # row['hoursuntilreveal'],
            # row['hoursuntilclose']],
            # row['daysuntilexpire'])
            print("data")
            print(data)
            print("data to be inserted")
            print(data_to_be_inserted)
            query = '''
            Insert into domains(Name,WalletID,Decoded_Punycode,Status,Reserved,HoursUntilBidding,HoursUntilReveal,HoursUntilClose,DaysUntilExpire) VALUES {data_to_be_inserted}
            '''.format(data_to_be_inserted=data_to_be_inserted)

            print(" this is query")
            print(query)
            cursor = self.conn.cursor()
            cursor.execute(query)
            u = input("check this out")
            rows_affected = cursor.execute(query)
            for row in rows_affected.fetchall():
                NewData.append(row)
            cursor.close()
            self.conn.commit()
            print('New Data Rows Added to Db')
            print(NewData)
            return NewData
        except Exception as e:
            print(str(e))
            return None


if __name__ == "__main__":
    # """This is executed when run from the command line passing command line arguments to main function"""
    hsd = HSDScheduler()
    # #main(sys.argv[1:])
