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

cnxn_str = ("Driver={SQL Server Native Client 11.0};"
            "Server=localhost,8000;"
            "Database=bucit;"
            "UID=root;"
            "PWD=;")

cnxn = pyodbc.connect(cnxn_str)
print(cnxn)