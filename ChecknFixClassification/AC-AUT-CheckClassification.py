#####################################################################
# This program deals with AC classification.
# 1. It reads all elements from AC, then their general properties (element ID & type) & elements classification.
# 2. Script insert data in postgreSQL DB so we can analyze it after in BI.
#####################################################################

# Set up globals
import sys
import json
import os
import psycopg2
import psycopg2.extras
import asyncio

from asynczip import AsyncZip
from types import SimpleNamespace
from archicad import ACConnection

# Classes
class Element:
    def __init__(self, guid, eID, eType, className, classGUID, classSysGUID):
        self.guid = guid
        self.ID = eID
        self.type = eType
        self.className = className
        self.classGUID = classGUID
        self.classSysGUID = classSysGUID

class ClassificationItem:
    def __init__(self, guid, id, name, description):
        self.guid = guid
        self.id = id
        self.name = name
        self.description = description

# Functions
# Configuration
def Config(sFilePath):
    with open(sFilePath) as json_file:
        objConfig = json.loads(json_file.read(), object_hook = lambda d: SimpleNamespace(**d))
    return objConfig

# Recursive function for Classification system tree data flattening
def GetClassificationSystemItem(classificationItems,aClassificationSystemItems):
    if classificationItems.children is not None and len(classificationItems.children) != 0:
        for classificationItemChild in classificationItems.children:
            aClassificationSystemItems.append(
                ClassificationItem(
                    classificationItemChild.classificationItem.classificationItemId.guid,
                    classificationItemChild.classificationItem.id,
                    classificationItemChild.classificationItem.name,
                    classificationItemChild.classificationItem.description
                )
            )
            GetClassificationSystemItem(classificationItemChild.classificationItem,aClassificationSystemItems)

#####################################################################
# Main
def main(iACProcessPort):
    # Define locals
    aElements = []
    aPropertyAllItems = []
    aPropertyGUID = []
    aElementsPropertyData = []
    aClassificationSystemItems = []
    objClassificationSystemID = []
    aACElementsDB = []
    aPropertyLocalListID = []
    
    # Try read configuration file
    try:
        objConfig = Config(os.path.dirname(os.path.abspath(__file__)) + '\\'+ 'config.json')
    except:
        print("Can't configure program")

    # Set internal connection with ArchiCAD
    try:
        conn = ACConnection.connect(iACProcessPort) 
        assert conn
        acc = conn.commands
    except:
        print("Can't connect to ArchiCAD")

    # Get Classification system data
    try:
        # Get all Classification systems
        aClassificationSystems = acc.GetAllClassificationSystems()

        # Get specific classification system mentioned in config.json
        objClassificationSystem = next(c for c in aClassificationSystems if c.name == objConfig.sACClassificationName and c.version == objConfig.sACClassificationVersion)

        # Get all Classification system items in tree
        tClassificationSystemItems = acc.GetAllClassificationsInSystem(objClassificationSystem.classificationSystemId)
    except:
        print("Can't get ArchiCAD Classification system data")

    # Flatten Classification system items for simplier usage
    try:
        for aClassificationSystemItem in tClassificationSystemItems:
            # First level for root Classification items 
            aClassificationSystemItems.append(
                ClassificationItem(
                    aClassificationSystemItem.classificationItem.classificationItemId.guid,
                    aClassificationSystemItem.classificationItem.id,
                    aClassificationSystemItem.classificationItem.name,
                    aClassificationSystemItem.classificationItem.description
                )
            )
            # Call recursive function for inner levels of items
            GetClassificationSystemItem(aClassificationSystemItem.classificationItem,aClassificationSystemItems)
    except:
        print("Can't flatten Classification system items")

    # Get all elements
    try:
        aElements = acc.GetAllElements()
    except:
        print("Can't get ArchiCAD elements")

    # Get properties data
    try:
        # Get all ArchiCAD properties names
        aPropertyAllItems = acc.GetAllPropertyNames()

        # Filter properties list to BuiltIn & properties defined in config.json
        # Just need to get Element ID & Element type
        aPropertyItems = list(filter(lambda p: p.type == 'BuiltIn' and p.nonLocalizedName in objConfig.aACPropertyName,aPropertyAllItems))

        # Iterate through filtered properties
        for pPropertyName in objConfig.aACPropertyName:
            aPropertyItem = [p for p in aPropertyItems if p.nonLocalizedName == pPropertyName]
            aPropertyLocalListID.append(aPropertyItems.index(aPropertyItem[0]))
        
        # Get filtered properties GUIDs
        aPropertyGUID = acc.GetPropertyIds(aPropertyItems)
    except:
        print("Can't get ArchiCAD properties")

    # Get elements properties data
    try:
        aElementsPropertyData = acc.GetPropertyValuesOfElements(aElements,aPropertyGUID)
    except:
        print("Can't get ArchiCAD elements properties data")
    
    # Get elements classification
    try:
        # Make temporal list of Classification system IDs
        objClassificationSystemID.append(objClassificationSystem.classificationSystemId)

        # Get elements classification data
        aElementsnClassificationItem = acc.GetClassificationsOfElements(aElements, objClassificationSystemID)
    except:
        print("Can't get elements Classification data")

    # Set elements data - guid, id, type, classificationName, classificationGUID, classificationSystemGUID for insertion in DB
    try:
        for iElementId,iElementProperty,iElementClassification in zip(aElements,aElementsPropertyData,aElementsnClassificationItem):
            if iElementClassification.classificationIds[0].classificationId.classificationItemId is not None:
                # Get Classification item based on element classification
                iClassSystemItemTemp = next((f for f in aClassificationSystemItems if f.guid == iElementClassification.classificationIds[0].classificationId.classificationItemId.guid), None)
            
                # Check classification item
                if iClassSystemItemTemp is not None:
                    iClassSystemItemTempID = iClassSystemItemTemp.id
                    iClassSystemItemTempGUID = iClassSystemItemTemp.guid
                else:
                    iClassSystemItemTempID = 'Unclassified'
                    iClassSystemItemTempGUID = '00000000-0000-0000-0000-000000000000'
            else:
                iClassSystemItemTempID = 'Unclassified'
                iClassSystemItemTempGUID = '00000000-0000-0000-0000-000000000000'
                
            # Insert data in temp list 
            aACElementsDB.append(
                (
                    iElementId.elementId.guid, 
                    iElementProperty.propertyValues[aPropertyLocalListID[0]].propertyValue.value,
                    iElementProperty.propertyValues[aPropertyLocalListID[1]].propertyValue.value,  
                    iClassSystemItemTempGUID,
                    iClassSystemItemTempID,
                    iElementClassification.classificationIds[0].classificationId.classificationSystemId.guid
                )
            )
    except:
        print("Can't set elements data for futher DB insertion")

    # Provide postgreSQL connection
    try:
        objPGConfig = Config(os.path.dirname(os.path.abspath(__file__)) + '\\'+ '__NOTSYNC_postgresqlConfig.json')
        pgConn = psycopg2.connect(
            database    = objPGConfig.database, 
            user        = objPGConfig.user, 
            password    = objPGConfig.password, 
            host        = objPGConfig.host
        )
        pgCur = pgConn.cursor()
        psycopg2.extras.register_uuid()
    except:
        print("Can't connect to DB")

    # Prepare table for insertion
    try:
        pgCur.execute("truncate table ac_classification_check")
        pgConn.commit()
    except:
        print("Can't truncate DB")

    # Insert data in DB
    try:
        pgQuery = """INSERT INTO ac_classification_check ("elemGUID", "elemID", "elemType", "classGUID", "classType", "classSysGUID") VALUES (%s, %s, %s, %s, %s, %s);"""
        psycopg2.extras.execute_batch(pgCur,pgQuery,aACElementsDB, page_size=10000)
        pgConn.commit()
    except:
        print("Can't insert data in DB")

    # Close connection
    pgCur.close()
    pgConn.close()

    return aACElementsDB

# Set up entry point
if __name__ == '__main__':
    # Init AC port
    # Try read configuration file
    try:
        objSessionConfig = Config(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'+ 'session.json')
    except:
        print("Can't configure program")
    # Check ArchiCAD port
    # Get ArchiCAD API ports range
    rACPortRange = ACConnection._port_range()
    try:
        if objSessionConfig.iACProcessPort in rACPortRange:
            main(objSessionConfig.iACProcessPort)
        else:
            # If args is empty set port with error value
            raise Exception("Invalid ArchiCAD port")
    except Exception as inst:
        print(inst.args)