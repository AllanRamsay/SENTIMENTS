import datetime
import os.path
import sys
import __main__
from colored import fg, bg, attr
import cHTMLStripper
import operator
import cPickle as pickle
from random import choice
from string import ascii_uppercase
import copy

# to check if string is Ararbic or English
import unicodedata as UD

global MIN_DATE ; MIN_DATE = datetime.datetime.strptime('01/01/1900', '%d/%m/%Y')
global MAX_DATE ; MAX_DATE = datetime.datetime.strptime('31/12/2999', '%d/%m/%Y')

# taken from stackoverflow 
def dump(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif type(obj) == list:
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)

def end():
	sys.exit("\n\nEnding   " + str(datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S ')) + "\n\n")

def CDate(sDate, sFormat="%d/%m/%y"):
    sRes = (datetime.datetime.strptime(sDate, sFormat)).date()
    return sRes

def DateAdd(sInterval, nNumber, sDate):
    if isinstance(sDate, datetime.date):
        sRes = sDate + datetime.timedelta(nNumber)
    elif isinstance(sDate, str):
        sRes = (datetime.datetime.strptime(sDate, "%d/%m/%y").date() + datetime.timedelta(nNumber)).strftime('%d/%m/%y')
    return sRes

def DateFormat(sDate, sFrom="%Y-%m-%d", sTo="%d/%m/%y"):
    sRes = datetime.datetime.strptime(sDate, sFrom).strftime(sTo)
    return sRes

def SDate(dDate, sFormat="%d/%m/%y"):
    sRes = dDate.strftime(sFormat)
    return sRes

def FileExists(sFile):
	bRes=os.path.isfile(sFile)
	return bRes

def FormatNumber(lfNumber):
    return lfNumber
    #return float("{0:.4f}".format(lfNumber))

def GetRandomString(nLen):
    return (''.join(choice(ascii_uppercase) for i in range(nLen)))

def AppSettings(sKey):
    EXECUTING_FOLDER,EXECUTING_FILE = GetExecutingFolder();
    with open(EXECUTING_FOLDER + '/' + EXECUTING_FILE + '.config') as oConfig:
        for line in oConfig:
            sLine = line.strip()
            if (sLine != ""):
                if (sLine[0] != "#"):
                    sCode = sLine.split(":")[0];
                    sValue = sLine.split(":")[1];
                    if sCode == sKey:
                        sRes = sValue
                        return sRes

def GetExecutingFolder():
    sPath, sFile = os.path.split(__main__.__file__)
    sFile = os.path.splitext(sFile)[0]

    # Python functions can return multiple values - awesome!
    return sPath, sFile

def IsArabic(sText):
    oRes = len([None for ch in sText if UD.bidirectional(ch) in ('R', 'AL')])/float(len(sText))
    bRes=False
    if oRes>0.5:
        bRes=True
    return bRes

def print2(sMsg, hFGColour="#ff0000", hBGColour="#ffffff"):
    try:
        # add colours for console
        oColor = fg(hFGColour) + bg(hBGColour)
        print (oColor + sMsg + attr('reset'))
    except:
        print sMsg
    
    sys.stdout.flush()

def PrintDictionary(aDict):
    for sValue, sKey in aDict.iteritems():
        print (sKey, sValue ),
        print (sValue)

def RemoveDictionaryItemsByValue(oDict, nRemoveValue, bPreserve=True):
    if bPreserve:
        # take copy - dont want to ruin original
        oDictCopy = copy.deepcopy(oDict)
    else:
        oDictCopy = oDict

    for sKey,nValue in oDictCopy.items():
        if nValue == nRemoveValue: del oDictCopy[sKey]
    
    return oDictCopy

def RemoveSpaces(sSentence):
	sSentence=sSentence.strip()
	while sSentence.find("  ")>-1:
		sSentence = sSentence.replace("  "," ")
    
	return sSentence

def RemoveTags(sData, sStartTag, sEndTag):

    while True:
        try:
            nPos1=sData.index(sStartTag)
        except:
            nPos1=-1

        try:
            nPos2=sData.index(sEndTag, nPos1)
        except:
            nPos2=-1

        if ((nPos1>-1) and (nPos2>-1)):
            nPos2 = nPos2 + len(sEndTag)
            sRemove = sData[nPos1:nPos2]
            sData = sData.replace(sRemove, ' ')
        else:
            break
        
    return sData

def SortDictionaryByValue(aDict, bReverse=False):
    aSorted = sorted(aDict.items(), key=operator.itemgetter(1), reverse=bReverse)
    return aSorted

def StripHTML(sData):

    sData = RemoveTags(sData, "<script", "</script>")
    sData = RemoveTags(sData, "<!--", "//-->")
    
    oHTMLStripper = cHTMLStripper.MLStripper()
    oHTMLStripper.feed(sData)
    sRes = oHTMLStripper.get_data()
    sRes = sRes.strip('\t\n\r')
        
    return sRes

def WriteToLog(sMsg, hFGColour="#ffffff", hBGColour="#000000"):
    # write to log without the colours
    sPath,sFile = GetExecutingFolder()
    sPath = sPath + '/PublishLogs/' + str(datetime.date.today()) + ".log"
	
    try:
        sMsg = str(datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S ')) + sMsg   
        oFile = open(sPath,"a")
        oFile.write(sMsg + '\n') 
        oFile.close()
    except:
        pass

    try:
        # add colours for console
        oColor = fg(hFGColour) + bg(hBGColour)
        print (oColor + sMsg + attr('reset'))
    except:
        print sMsg
    
    sys.stdout.flush()

def LoadObject(sFilePath):
	with open(sFilePath, 'rb') as oHandle:
		dcRes = pickle.loads(oHandle.read())
	return dcRes

def SaveObject(oObject, sFilePath):
	with open(sFilePath, 'wb') as oFile:
		pickle.dump(oObject, oFile)
	oFile.close() 

def StripNewline(sObject):
	sRes = sObject.strip().replace("\r\n"," ").replace("\r"," ").replace("\n"," ").strip()
	return sRes