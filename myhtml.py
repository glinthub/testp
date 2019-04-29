#!/bin/python

import os
import re

class Position:
    def __init__(self, row, col):
        self.row = row
        self.col = col

class TextRange:
    def __init__(self, start, stop):
        self.startPos = start
        self.stopPos = stop

class Element:
    def __init__(self, text, textRange):
        self.name = ""
        self.text = text
        self.textRange = textRange
        self.level = 0
        self.parent = None
        self.subElemList = []
        self.isEmpty = True
    def getInfo(self):
        return " line " + str(self.textRange.startPos.row) + ", col " + str(self.textRange.startPos.col) + ": " + self.name
    def dump(self, outfile):
        #print "dump " + self.getInfo()
        s = "  "*self.level + self.text
        outfile.write(s + "\n")
        for subElem in self.subElemList:
            subElem.dump(outfile)
        if isinstance(self, Tag) and not self.isSimple():
            s = "  "*self.level + "</" + self.name + ">"
            outfile.write(s + "\n")
            

class Content(Element):
    def __init__(self, text, textRange):
        Element.__init__(self, text, textRange)
        self.name = "content"
        
class Tag(Element):
    def __init__(self, text, textRange):
        Element.__init__(self, text, textRange)
        self.name = Tag.getTagName(text)
        self.text = text
        self.getAttrs()
    def replaceTag(self, text):
        self.name = Tag.getTagName(text)
        self.text = text
        self.getAttrs()
        self.tail.name = "/" + self.name
        self.tail.text = "</" + self.name + ">"
    def remove(self, isRecursive):
        if isRecursive:
            raise Error("not implemented yet")
        parent = self.parent
        index = parent.subElemList.index(self)
        for subElem in self.subElemList:
            index += 1
            parent.subElemList.insert(index, subElem)
            subElem.parent = parent
        parent.subElemList.remove(self)
        self.subElemList = []
    def insertTag(self, newTag):
        parent = self.parent
        index = parent.subElemList.index(self)
        parent.subElemList.insert(index, newTag)
        parent.subElemList.remove(self)
        newTag.parent = parent
        newTag.subElemList.insert(0, self)
        newTag.tail = Tag("</" + newTag.name + ">", TextRange(Position(-1, -1), Position(-1, -1)))
    def isSimple(self):
        simpleTags = ["meta", "link", "img", "input", "br"]
        if self.name in simpleTags:
            return True
        else:
            return False
    def isEmbedableTag(self):
        nonEmbedableTags = ["script", "meta", "link", "pre", "img", "input"]
        if self.name in nonEmbedableTags:
            return False
        else:
            return True
    def getAttrs(self):
        self.attrs = {}
        if self.text.find(" ") == -1:
            return
        attrStr = self.text[2+len(self.name):-1]
        while True:
            if len(attrStr) < 1:
                break
            eqAt = attrStr.find("=") 
            if eqAt != -1:
                valueBegin = eqAt + 1
                if attrStr[eqAt+1] == "\"":
                    valueBegin += 1
                    valueEnd = attrStr.find("\"", valueBegin)
                else:
                    valueEnd = attrStr.find(" ", valueBegin)
                attrName = attrStr[0:eqAt]
                if valueEnd == -1:
                    attrValue = attrStr[valueBegin:]
                else:
                    attrValue = attrStr[valueBegin: valueEnd]
                attrValue = attrValue.strip("\"")
                attrStr = attrStr[valueEnd+1:].lstrip()
                self.attrs[attrName] = attrValue
                if valueEnd == -1:
                    break
            else:
                break
        print self.attrs


    @staticmethod
    def isNameValid(name):
        if name[0] == "!" or name[0] == "-" or len(name) > 20:
            return False
        else:
            return True

    @staticmethod
    def getTagName(text):
        spacePos = text.find(" ")
        ltPos = text.find(">")
        if (spacePos > 0 and ltPos > 0):
            tagName = text[1 : min(spacePos, ltPos)]
        elif spacePos > 0:
            tagName = text[1 : spacePos]
        elif ltPos > 0:
            tagName = text[1 : ltPos]
        else:
            tagName = text[1 : ].strip("\n")
        return tagName

class Page():
    def __init__(self, filename):
        self.tagStack = []
        self.file = open(filename)
        self.lines = self.file.readlines()
        for line in self.lines:
            line.strip("\n")
        self.pageContainer = Tag("<page>", TextRange(Position(-1, -1), Position(-1, -1)))
        self.tagStack = [self.pageContainer]

    def getText(self, pos1, pos2):
        row1 = pos1.row
        col1 = pos1.col
        row2 = pos2.row
        col2 = pos2.col
        if row1 == row2:
            s = self.lines[row1][col1:col2+1].strip("\n")
        else:
            s = self.lines[row1][col1:].strip("\n")
            row = row1+1
            while row < row2:
                s += self.lines[row].strip("\n")
                row += 1
            s += self.lines[row2][:col2+1].strip("\n")
        return s

    def recordElement(self, element):
        print "record " + element.getInfo()
        tagParent = self.tagStack[len(self.tagStack)-1]

        if isinstance(element, Content):
            #print "  add content to subList of " + tagParent.name
            element.parent = tagParent
            element.level = len(self.tagStack)-1
            tagParent.subElemList.append(element)
            return
        else:
            tag = element

        startPos = tag.textRange.startPos
        stopPos = tag.textRange.stopPos
        isHead = isTail = False
        if tag.name[0] != "/":
            isHead = True
        else:
            isTail = True
        if self.lines[stopPos.row][stopPos.col-1] == "/":
            isTail = True

        if isTail and not isHead:
            if tag.name == "/" + tagParent.name: #check if matched pair
                #print "  pop " + tagParent.name
                tagParent.tail = tag
                self.tagStack.pop()
                tagParent = self.tagStack[len(self.tagStack)-1]
            else:
                print element.getInfo()
                print "unmatched pair: expect " + tag.name + ", but " + tagHead.name
                pass

        #print "  add " + tag.name + " to subList of " + tagParent.name
        tag.level = len(self.tagStack)-1
        tag.parent = tagParent
        if isHead:
            tagParent.subElemList.append(tag)

        if tag.isSimple():
            #print "  single tag " + tag.name + " in " + tagParent.name
            return
        if isTail:
            return
        elif isHead:
            #print "  push " + tag.name
            self.tagStack.append(tag)
            return
        else:
            raise Error("illegal tag ! line",startPos.row,"col",startPos.col)

    def findNextElement(self, element):
        if element == None:
            row = 0
            col = 0
        else:
            row = element.textRange.stopPos.row
            col = element.textRange.stopPos.col + 1
        if col >= len(self.lines[row]) - 1:
                row += 1
                col = 0
        row0 = row
        col0 = col
        incomplete = False
        while row < len(self.lines):
            #print "search from line", row, "col", col
            line = self.lines[row]
            offset = 0
            while offset != -1:
                if incomplete == False:
                    offset = line.find("<", col)
                    if offset != -1:
                        col = offset+1
                        tagName = Tag.getTagName(line[offset:])
                        if not Tag.isNameValid(tagName):
                            continue
                        if row != row0 or offset != col0: #regular content found
                            pos1 = Position(row0, col0)
                            row_tmp = row
                            col_tmp = offset - 1
                            while col_tmp == -1:
                                row_tmp = row_tmp-1
                                col_tmp = len(self.lines[row_tmp]) - 1
                            pos2 = Position(row_tmp, col_tmp)
                            text = self.getText(pos1, pos2)
                            if re.search(r'[^ \n]', text):
                                content = Content(text, TextRange(pos1, pos2))
                                return content
                        incomplete = True
                        pos1=Position(row, offset)
                    continue
                else:
                    offset = line.find(">", col)
                    if offset != -1:
                        col = offset+1
                        incomplete = False
                        pos2=Position(row, offset)
                        tagText = self.getText(pos1, pos2)
                        tag = Tag(tagText, TextRange(pos1, pos2))
                        return tag
            row += 1
            col = 0

    def scanPage(self):
        element = None
        while True:
            element = self.findNextElement(element)
            if element == None:
                break
            self.recordElement(element)

    def scanEmptyTags(self, elem):
        print "scan " + elem.getInfo()
        isEmpty = True
        if isinstance(elem, Content):
            text = elem.text.replace("\n", "").replace(" ", "").replace("&nbsp;", "")
            if (len(text) > 0):
                isEmpty = False
        elif elem.isSimple():
            isEmpty = False
        e = elem
        if isEmpty == False:
            print "not empty: " + elem.text
            while e != None and e.isEmpty == True:
                e.isEmpty = False
                print "scan up" + e.getInfo()
                e = e.parent
        for subElem in elem.subElemList:
            self.scanEmptyTags(subElem)

    def removeEmptyTags(self, elem):
        if elem.isEmpty:
            parent = elem.parent
            parent.subElemList.remove(elem)
            print "remove empty " + elem.getInfo()
            return
        for subElem in elem.subElemList:
            self.removeEmptyTags(subElem)

    def reform(self):
        self.scanPage()
        self.scanEmptyTags(self.pageContainer)
        self.removeEmptyTags(self.pageContainer)

    def dump(self, outfile):
        for tag in self.pageContainer.subElemList:
            tag.dump(outfile)

