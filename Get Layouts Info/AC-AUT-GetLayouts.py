# Set up globals
import json
import os
from archicad import ACConnection
from collections import namedtuple

ACconn = ACConnection.connect()
assert ACconn

ACcomm  =   ACconn.commands
ACtypes =   ACconn.types
ACutil  =   ACconn.utilities

# Classes

# Functions
def Config():
    sFilePath = os.path.dirname(os.path.abspath(__file__)) + '\\'+ 'config.json'
    with open(sFilePath) as json_file:
        objConfig = json.loads(json_file.read(), object_hook = lambda d: namedtuple('objConfig', d.keys())(*d.values()))
    return objConfig
    
def GetMasterLayout(objConfig):
    iCounter = 0
    for confNavigatorItem in objConfig.NavigatorItem:
        layoutBookTree = ACcomm.GetNavigatorItemTree(ACtypes.NavigatorTreeId(confNavigatorItem))
        #print(layoutBookTree)
        for confSubset in objConfig.Subset:
            objSubset = [t for t in layoutBookTree.rootItem.children[0].navigatorItem.children if t.navigatorItem.name == confSubset]
            #print(objSubset)
            if len(objConfig.Layout) == 0:
                for objLayout in objSubset[0].navigatorItem.children:
                    settLayout  = ACcomm.GetLayoutSettings(objLayout.navigatorItem.navigatorItemId)
                    #print(objLayout)
                    objLayout = objLayout.to_dict()
                    objLayout.update(settLayout.to_dict())
                    #print(objLayout)
                    objSubset[0].navigatorItem.children[iCounter] = objLayout
                    iCounter+=1
                iCounter = 0
    return layoutBookTree

def WriteToJSON(sFileName,lAllItems):
    try:
        sFilePath = os.path.dirname(os.path.abspath(__file__)) + '\\'+ sFileName
        with open(sFilePath, 'w', encoding='utf-8') as f:
            json.dump(lAllItems.to_dict(), f, ensure_ascii=False, indent=4)
        pass
    except:
        print('Can\'t write layout properties to file')
        pass

# Main
sFileName = 'AC-Layouts-Result.json'

objConfig = Config()
layoutBookTree = GetMasterLayout(objConfig)
WriteToJSON(sFileName,layoutBookTree)