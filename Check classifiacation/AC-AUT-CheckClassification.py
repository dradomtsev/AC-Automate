import sys
import itertools
from archicad import ACConnection

class Element:
    def __init__(self, guid, eType, eID, classificationName, classificationGUID):
        self.guid = guid
        self.type = eType
        self.ID = eID
        self.classificationName = classificationName
        self.classificationGUID = classificationGUID

class classificationItem:
    def __init__(self, guid, id, name, description):
        self.guid = guid
        self.id = id
        self.name = name
        self.description = description

def GetClassificationSystemItem(classificationItems,aClassificationSystemItems):
    if classificationItems.children is not None and len(classificationItems.children) != 0:
        for classificationItemChild in classificationItems.children:
            aClassificationSystemItems.append   (classificationItem(
                                                                    classificationItemChild.classificationItem.classificationItemId.guid,
                                                                    classificationItemChild.classificationItem.id,
                                                                    classificationItemChild.classificationItem.name,
                                                                    classificationItemChild.classificationItem.description
                                                ))
            GetClassificationSystemItem(classificationItemChild.classificationItem,aClassificationSystemItems)

def main(iArchiCADPort):
    # Define vars
    aElements = []
    aAllProps = []
    # sPropItem = []
    aProps = []
    aElementsProps = []
    aClassificationSystemItems = []
    ClassSysDict = []
    ACElementsDB = []
    ClassificationName = "ARCHICAD Classification"
    aPropNames = ["General_Type","General_ElementID"]
    aPropertIndexes = []

    # Set internal connection with ArchiCAD
    conn = ACConnection.connect(int('19723')) 
    assert conn
    acc = conn.commands

    # Get all elements
    aElements = acc.GetAllElements()

    # Get properties data
    aAllProps = acc.GetAllPropertyNames()
    pPropItem = list(filter(lambda p: p.type == 'BuiltIn' and p.nonLocalizedName in aPropNames,aAllProps))
    for pPropertyName in aPropNames:
        PropertyInstance = [p for p in pPropItem if p.nonLocalizedName == pPropertyName]
        aPropertIndexes.append(pPropItem.index(PropertyInstance[0]))
    aProps = acc.GetPropertyIds(pPropItem)

    aElementsProps = acc.GetPropertyValuesOfElements(aElements,aProps)
    # Get Classification system data
    aClassificationSystems = acc.GetAllClassificationSystems()
    oClassificationSystem = next(c for c in aClassificationSystems if c.name == ClassificationName)
    tClassificationSystemItems = acc.GetAllClassificationsInSystem(oClassificationSystem.classificationSystemId)

    for aClassificationSystemItem in tClassificationSystemItems:
        aClassificationSystemItems.append   (classificationItem(
                                                        aClassificationSystemItem.classificationItem.classificationItemId.guid,
                                                        aClassificationSystemItem.classificationItem.id,
                                                        aClassificationSystemItem.classificationItem.name,
                                                        aClassificationSystemItem.classificationItem.description
                                            ))
        GetClassificationSystemItem(aClassificationSystemItem.classificationItem,aClassificationSystemItems)

    # print(next(f for f in aClassificationSystemItems if  f.id == "Wall").id)

    # Get elements classification
    for ClassSys in aClassificationSystems:
        ClassSysDict.append(ClassSys.classificationSystemId)
    aElementsnClassificationItem = acc.GetClassificationsOfElements(aElements, ClassSysDict)
    
    # Set elements data - guid, type, classificationId
    for ElementId,ElementProp,ElementnClass in zip(aElements,aElementsProps,aElementsnClassificationItem):
        ClassSystemItemTemp = next((f for f in aClassificationSystemItems if f.guid == ElementnClass.classificationIds[0].classificationId.classificationItemId.guid), None)
        if ClassSystemItemTemp is not None:
            ClassSystemItemTempID = ClassSystemItemTemp.id
            ClassSystemItemTempGUID = ClassSystemItemTemp.guid
        else:
            ClassSystemItemTempID = 'Unclassified'
        ACElementsDB.append(Element (
                                    ElementId.elementId.guid, 
                                    ElementProp.propertyValues[aPropertIndexes[0]].propertyValue.value,
                                    ElementProp.propertyValues[aPropertIndexes[1]].propertyValue.value,  
                                    ClassSystemItemTempID,
                                    ClassSystemItemTempGUID
                                    ))
    for ACElemDBrec in ACElementsDB:
        print(ACElemDBrec.guid, ACElemDBrec.type, ACElemDBrec.ID, ACElemDBrec.classificationName, ACElemDBrec.classificationGUID)
    return ACElementsDB

if __name__ == '__main__':
    # Init AC port
    iArchiCADPort = 0
    # Check args
    if len(sys.argv) >= 2:
        iArchiCADPort = sys.argv[1]
        pass
    else:
        # If args is empty set port with error value
        iArchiCADPort = -1
        pass
    main(iArchiCADPort)