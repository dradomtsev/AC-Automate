# Set up globals
import os
import json
from archicad import ACConnection

ACconn = ACConnection.connect()
assert ACconn

ACcomm  =   ACconn.commands

# Classes

# Functions
def GetACPropertiesInfo(lAllProps):
    try:
        lAllPropsName       = ACcomm.GetAllPropertyNames()
        lAllPropsId         = ACcomm.GetPropertyIds(lAllPropsName)
        lAllPropsDetails    = ACcomm.GetDetailsOfProperties(lAllPropsId)
        pass
    except:
        print('Can\'t get archicad properties')
        pass
    
    try:
        for itemName, itemID, itemDetatil in zip(lAllPropsName, lAllPropsId, lAllPropsDetails):
            objProps = itemName.to_dict()
            objProps.update(itemID.to_dict())
            objProps.update(itemDetatil.to_dict())
            lAllProps.append(objProps)
        pass
    except:
        print('Can\'t merge archicad properties')
        pass


def WriteToJSON(sFileName,lAllItems):
    try:
        sFilePath = os.path.dirname(os.path.abspath(__file__)) + '\\'+ sFileName
        with open(sFilePath, 'w', encoding='utf-8') as f:
            json.dump([p for p in lAllItems], f, ensure_ascii=False, indent=4)
        pass
    except:
        print('Can\'t write archicad properties to file')
        pass

        
# Main
lAllProps = []
sFileName = 'AC-Properties-24INT.json'

GetACPropertiesInfo(lAllProps)
WriteToJSON(sFileName,lAllProps)