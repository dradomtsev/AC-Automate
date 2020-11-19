# Libraries
import psutil
import datetime
import time
import json
import os
import subprocess

from types import SimpleNamespace
from archicad import Utilities
from archicad import ACConnection

# Global Variables
iArchiCADPort = 0
iProcessID = []
aElementIdItems = []
aElementIdItemsDict = []

# Classes

# Functions
def Config(sFilePath):
    with open(sFilePath) as json_file:
        objConfig = json.loads(json_file.read(), object_hook = lambda d: SimpleNamespace(**d))
    return objConfig

def findProcessIdByName(processName):
    lProcessObjects = []
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
            # Check if process name contains the given name string.
            if processName.lower() in pinfo['name'].lower():
                lProcessObjects.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return lProcessObjects

def WriteToJSON(sFilePath,lAllItems):
    try:
        with open(sFilePath, 'w+', encoding='utf-8') as f:
            f.write(lAllItems)
        pass
    except:
        print('Can\'t write properties to file')
        pass

#####################################################################
# Main
def main():
    # Try read configuration file
    try:
        objConfig = Config(os.path.dirname(os.path.abspath(__file__)) + '\\'+ 'config.json')
    except:
        print("Can't configure program")

    # Rewrite with thread wrapper 'cause subprocess.popen call might be not thread-safe
    # Try open ArchiCAD and wait until it's full start
    try:
        # Open session data file
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'+ 'session.json', "r") as json_file:
            objSessionConfig = json.load(json_file)

        #ACInstance = Utilities.OpenFile(objConfig.sResourceFilePath) # Open AC with file
        # Another way to open file and get PID
        ACInstance  = subprocess.Popen([objConfig.sProcessPath, objConfig.sResourceFilePath], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        # Write session ArchiCAD PID to config
        objSessionConfig["iACPID"] = ACInstance.pid

        # Get additional process info
        ACProcess = psutil.Process(objSessionConfig["iACPID"])

        # Write AC process start datetime
        objSessionConfig["tACstartDatetime"] = datetime.datetime.fromtimestamp(ACProcess._create_time).strftime("%Y-%m-%d %H:%M:%S")
        
        time.sleep(objConfig.iWaitTimeForFileOpen) # Need to find corresponding event
    except:
        print("Can't start ArchiCAD and open %s" % objConfig.sResourceFilePath)

    try:
        # Get ArchiCAD API ports range
        rACPortRange = ACConnection._port_range()

        # Get process connections
        ACProcessConnections = ACProcess.connections() 
        for iACConnElem in ACProcessConnections:
            if iACConnElem.laddr.port in rACPortRange: # Check port in range. Have to be rewritten depending on connection type
                iArchiCADPort = iACConnElem.laddr.port

        # Write session ArchiCAD port to config
        objSessionConfig["iACProcessPort"] = iArchiCADPort

        # Write session data to file for other python-subprocesses
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'+ 'session.json', "w") as json_file:
            json.dump(objSessionConfig, json_file)

        # Start internal connection with ArchiCAD
        try:
            conn = ACConnection.connect(objSessionConfig["iACProcessPort"]) 
            assert conn
            acc = conn.commands
        except:
            print('Can not establish connection')

        # Check internal connection and run futher if ok
        bIsAlive = acc.IsAlive()
        if bIsAlive:
            try:
                # Call external python script. You can change to your script by editing sExecutableScriptPath in config.json
                # objComplited = subprocess.run(["python",objConfig.sExecutableScriptPath,str(objSessionConfig["iACProcessPort"])], capture_output=True, text=True)
                objComplited = subprocess.check_call(["python",objConfig.sExecutableScriptPath])
                # Get result from external python script run
                # sResult = objComplited.stdout[objComplited.stdout.find("["):-1].replace("\'","\"")
                # Write result to JSON
                # WriteToJSON(objConfig.sResultFilePath, sResult)
                # Kill ArchiCAD process in any way. Can't find appropriate func in AC python library
                ACProcess.terminate()
            except:
                print('Can not external python script')
        else:
            pass
    except:
        print('Can not establish internal connection to %s' % objConfig.sProcessName)

# Set up entry point
if __name__ == '__main__':
    main()
