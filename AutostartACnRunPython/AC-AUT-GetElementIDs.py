import sys
from archicad import ACConnection

def main(iArchiCADPort):
    aElementIdItems = []
    aElementIdItemsDict = []

    # Set internal connection with ArchiCAD
    conn = ACConnection.connect(int(iArchiCADPort)) 
    assert conn
    acc = conn.commands

    # Get all elements ID
    aElementIdItems = acc.GetAllElements() 
    # Convert to dictionaries
    for ElementId in aElementIdItems:
        objProps = ElementId.to_dict()
        aElementIdItemsDict.append(objProps)
    print(aElementIdItemsDict)
    return aElementIdItemsDict

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