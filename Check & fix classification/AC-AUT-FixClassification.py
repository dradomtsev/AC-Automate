#####################################################################
# This program deals with AC classification.
# 1. It reads file with elements which classification you want to fix.
# 2. Reads Classification mapping file (where you write mapping between AC element type and AC classification items)
# 3. Script try to reset element's classification according to the mapping
#####################################################################

# Set up globals
import sys
import csv
import json
import os

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
# General program configuration
def Config():
    sFilePath = os.path.dirname(os.path.abspath(__file__)) + '\\'+ 'config.json'
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

# Config classification mapping
def ConfigClassification():
    sFilePath = os.path.dirname(os.path.abspath(__file__)) + '\\'+ 'AC-AUT-ClassificationMapping.json'
    with open(sFilePath) as json_file:
        objClassConfig = json.loads(json_file.read(), object_hook = lambda d: SimpleNamespace(**d))
    return objClassConfig

#####################################################################
# Main
def main():
    # Define locals
    aACElementsDB = []
    aElementClassification = []
    aClassificationSystemItems = []

    # Try read configuration file
    try:
        objConfig = Config()
    except:
        print("Can't configure program")

    # Read classification mapping file
    try:
        objClassConfig = ConfigClassification()
    except:
        print("Can't read classification mapping file")

    # Read classification fix file
    try:
        firstline = True
        with open(os.path.dirname(os.path.abspath(__file__)) + '\\'+ objConfig.aACClassificationFixFileName, 'r') as f:
            csvReader = csv.reader(f)
            for row in csvReader:
                if firstline:
                    firstline = False
                    continue
                aACElementsDB.append(Element(row[0], row[1], row[2], row[3], row[5], row[6]))
    except:
        print("Can't read classification fix file")

    # Set internal connection with ArchiCAD
    try:
        conn = ACConnection.connect(int('19723')) 
        assert conn
        acc = conn.commands
        act = conn.types
    except:
        print("Can't connect to ArchiCAD")

    # Get Classification system data
    try:
        # Get all Classification systems
        aClassificationSystems = acc.GetAllClassificationSystems()

        # Get specific classification system mentioned in config.json
        objClassificationSystem = next(c for c in aClassificationSystems if c.name == objConfig.sACClassificationName)

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

    # Prepare data for classification fixture
    try:
        for iACElement in aACElementsDB:
            sClassMappingName = next(c for c in objClassConfig.ElemClassMapping if c.element == iACElement.type).ACclassificationType[0]
            sClassACGUID = next(c for c in aClassificationSystemItems if c.id == sClassMappingName).guid
            aElementClassification.append(act.ElementClassification(
                act.ElementId(iACElement.guid),
                act.ClassificationId(act.ClassificationSystemId(iACElement.classSysGUID),act.ClassificationItemId(sClassACGUID))
            ))
    except:
        print("Can't prepare data for classification fixture")

    # Try fix elements classification
    try:
        acc.SetClassificationsOfElements(aElementClassification)
    except:
        print("Can't fix elements classification")

    return aACElementsDB

# Set up entry point
if __name__ == '__main__':
    main()