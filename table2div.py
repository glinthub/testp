from myhtml import *
import sys

def replaceTableWithDiv(container):
    tableTag = container
    #print "replaceTableWithDiv", tableTag.getInfo()
    tableTagStr = tableTag.text
    firstMultiCellRow = None
    tableChanged = False
    isRecursive = False
    subElemList = tableTag.subElemList
    for trTag in subElemList:
        #print trTag.getInfo()
        if trTag.name != "tr":
            continue
        tdNum = 0
        for tdTag in trTag.subElemList:
            if tdTag.name != "td":
                continue
            tdNum += 1
        print "td num:",tdNum
        if tdNum > 1:
            if firstMultiCellRow == None:
                firstMultiCellRow = trTag
        else:
            trTag.replaceTag("<div class=from_tr style=\"border: 2px solid cyan; margin: 3px; padding: 5px; background-color: #99aa99;\">")

            if not tableChanged:
                #print "table changed!"
                tableTag.remove(isRecursive)
                tableChanged = True

            if firstMultiCellRow != None:
                #print "generate table at middle"
                newTableTag = Tag(tableTagStr, firstMultiCellRow.textRange)
                firstMultiCellRow.insertTag(newTableTag)
                firstMultiCellRow = None

            for tdTag in trTag.subElemList:
                if tdTag.name != "td":
                    continue
                tdTag.remove(isRecursive)

    if firstMultiCellRow != None:
        #print "generate table at tail"
        newTableTag = Tag(tableTagStr, firstMultiCellRow.textRange)
        firstMultiCellRow.insertTag(newTableTag)
    
def doTableTransfer(elem):
    if isinstance(elem, Content):
        return
    tag = elem
    if tag.name == "table":
        replaceTableWithDiv(tag)
    i = 0
    for subElem in tag.subElemList:
        doTableTransfer(subElem) 

page = Page(sys.argv[1])
page.reform()
doTableTransfer(page.dummyTag)
#outfile = open("out.html", "w")
outfile = sys.stdout
page.dump(outfile)

