# -*- coding: utf-8 -*-
import nltk
import cLibrary
import math
from cNLPLibrary import *
"""
from cMySQL import *
from cSQL import *
"""
import cPickle as pickle
from nltk.corpus import wordnet
from nltk.collocations import *

def ClearDFTable():
    # wipe the saved df table in the db
    dcDFTable = {}
    sData = pickle.dumps(dcDFTable)
    sData = MySQL_Escape(sData)
    sSQL=SQLSelectUtility("DFTABLE")
    rs = MySQL_NewUpdateSet(sSQL)
    rs["utils_data"] = sData
    MySQL_Update(rs)

def CombineTermFrequencyTables(dcTFTable1, dcTFTable2):
	# sum the tf tables
	dcRes = { k: dcTFTable1.get(k, 0) + dcTFTable2.get(k, 0) for k in set(dcTFTable1) | set(dcTFTable2) }
	return dcRes

def ExtractHashtags(sTweet):
    sRes = set(part[0:] for part in sTweet.split() if part.startswith('#'))
    return sRes

def GetDFTable(sCode="DFTABLE"):
    # get the existing DF table
    sSQL=SQLSelectUtility(sCode)
    rs = MySQL_NewSelectSet(sSQL)
    for dr in rs:
        sData = str(dr["utils_data"])

        try:
            dcDFTable = pickle.loads(sData)
        except:
            dcDFTable = {}

    return dcDFTable

def LogApplyDFToTF(dcDFTable, dcTFTable):
    #TODO: do this pythonically
    dcRes = {}
	
    #total #words in the DFTable
    nDFTotalWords = sum(dcDFTable.values())

    #total #words in the DFTable
    nTFTotalWords = sum(dcTFTable.values())
	
    for sKey, nTFValue in dcTFTable.iteritems():
        # nTFValue = number of times the word occurs in the document
        # ignore things like URLs
        if len(sKey)<101:
            try:
                # number of documents that contain the word 
                nDFValue = int(dcDFTable[sKey])
                bFound = True
            except:
                bFound = False
                print "**************************************-" + sKey

            # some words contain dots - remove them
            #if sKey.find(".")>-1:
            #    bFound = False


            """
            if bFound:
                # https://www.elastic.co/guide/en/elasticsearch/guide/master/scoring-theory.html
                # idf(t) = 1 + log ( numDocs / (docFreq + 1)) 
                lfIDF = 1 + math.log(float(705000) / (float(nDFValue) + 1))
                dcRes[sKey] = lfIDF
            """

            """
            if bFound:
				# from wikipedia
                nAllDocuments = 705000
                lfIDF = math.log(float(nAllDocuments)/float(nDFValue), 10)
                lfRes = float(nTFValue) * float(lfIDF)
                dcRes[sKey] = lfRes
            """
			
            # from Mike Bernico "Using TF-IDF to convert unstructured text to useful features" Youtube video
            # tfidf = A x B
            # where A = (#times word appears in a document)/(total #number of words in doc)
            # and B = log(#documents / #docs that contain the word)
            """
            if bFound:
                # (#times word appears in a document)
                A1 = nTFValue
                # (total #number of words in doc)
                A2 = nTFTotalWords

                # #documents
                B1 = 705423
                # #docs that contain the word
                B2 = nDFValue

                lfTop = float(A1) / float(A2)
                lfBottom = math.log(float(B1) / float(B2))

                lfRes = lfTop * lfBottom

                dcRes[sKey] = lfRes
            """
 
            if bFound:
                lfLog = math.log(nDFValue, 10)
                #lfLog = float(nDFValue)
                #lfLog = math.sqrt(nDFValue)
                #lfLog = nDFValue ** (1. / 3)
		
                if lfLog==0:
                    # set to 1.1 as advised by PAR 08/12/15
                    lfLog=1.1
		
                lfRes = nTFValue / lfLog
                dcRes[sKey] = lfRes

    return dcRes

def CleanString(sData, sChar):
	try:
		sRes = sData.replace(sChar, "")
	except:
		sRes = sData
	
	return sData
	
def MakeTermFrequencyTable(sData, dcTFTable, bTweet):
    # tokenise using the NLTK (simple split doesnt handle punctuation)?
    # apparently NLTK in general works just fine with arabic

    sData = cLibrary.StripHTML(sData)
    sData = sData.replace("'","")

    # fix it up
    # sData = RemoveNonAscii(sData)

    # if its a tweet get and remove the @ and # tags
    if bTweet:
        oSet1 = set([i for i in sData.split() if i.startswith("#")])
        oSet2 = set([i for i in sData.split() if i.startswith("@")])	 
        oSet3 = set([i for i in sData.split() if i.startswith("http://")])	 
        oSet4 = set([i for i in sData.split() if i.startswith("https://")])	 
        oSet5 = set([i for i in sData.split() if i.find("@")>-1])	 

		# now remove from the data
        for sTag in oSet1:
            sData = sData.replace(sTag,'')
        for sTag in oSet2:
            sData = sData.replace(sTag,'')
        for sTag in oSet3:
            sData = sData.replace(sTag,'')
        for sTag in oSet4:
            sData = sData.replace(sTag,'')
        for sTag in oSet5:
            sData = sData.replace(sTag,'')
    
	sData = sData.replace(".", " ")
    sDataRaw = sData

    # sometimes articles contain characters that cause word_tokenize to fail, so must try
    # also some strings are encoded and some arent
    # eg http://www.bbc.co.uk/news/world-latin-america-34623236#sa-ns_mchannel=rss&ns_source=PublicRSS20-sa		

    # try various things - must be a better way?
    try:
        asWords = nltk.word_tokenize(sData)
        bRes=True
    except:
        bRes=False
    
    if (bRes == False):
        try:
		    sData = sDataRaw
		    sData = codecs.decode(sData, "UTF-8")
		    asWords = nltk.word_tokenize(sData)
		    bRes=True
        except:
            bRes=False
        
    if (bRes == False):
        try:
            sData = sDataRaw
            sData = codecs.encode(sData, "UTF-8")
            asWords = nltk.word_tokenize(sData)
            bRes=True
        except:
            bRes=False

    if (bRes == False):
        cLibrary.WriteToLog("***Unable to tokenise***", None, None)
        # write out *what* we were unable to tokenise
        cLibrary.WriteToLog(sDataRaw, None, None)
        bRes=False

    if bRes==True:
        # if tweet reinsert the tags
        if bTweet:
            for sTag in oSet1:
                asWords.append(sTag)
            for sTag in oSet2:
                asWords.append(sTag)
            for sTag in oSet3:
                asWords.append(sTag)
            for sTag in oSet4:
                asWords.append(sTag)
            for sTag in oSet5:
                asWords.append(sTag)
			
        for sWord in asWords:

            # save upper case and lower case as lowercase if morphy thinks its a word 
            # Morphy only works on lower case words 
            sWordA = Morphy(sWord.lower(), "a")
            sWordN = Morphy(sWord.lower(), "n")
            sWordR = Morphy(sWord.lower(), "r")
            sWordV = Morphy(sWord.lower(), "v")

            #print "changed from " +  sWord + " to " ,
            # see if any words were returned by morphy
            if ((sWordA!=None) and (sWordA!=sWord)): 
                sWord=sWordA
            elif ((sWordN!=None) and (sWordN!=sWord)): 
                sWord=sWordN
            elif ((sWordR!=None) and (sWordR!=sWord)): 
                sWord=sWordR
            elif ((sWordV!=None) and (sWordV!=sWord)): 
                sWord=sWordV

            #print sWord

            try:
                dcTFTable[sWord]=dcTFTable[sWord]+1
            except:
                dcTFTable[sWord]=1

    return bRes

def MorphyANRV(sWord):
	sWordA = Morphy(sWord.lower(), "a")
	sWordN = Morphy(sWord.lower(), "n")
	sWordR = Morphy(sWord.lower(), "r")
	sWordV = Morphy(sWord.lower(), "v")

	#print "changed from " +  sWord + " to " ,
	# see if any words were returned by morphy
	if ((sWordA!=None) and (sWordA!=sWord)): 
		sWord=sWordA
	elif ((sWordN!=None) and (sWordN!=sWord)): 
		sWord=sWordN
	elif ((sWordR!=None) and (sWordR!=sWord)): 
		sWord=sWordR
	elif ((sWordV!=None) and (sWordV!=sWord)): 
		sWord=sWordV
	return sWord 

def Morphy(sWord,sType): 
	oRes = None

	try:
		oRes = wordnet.morphy(sWord, sType)
	except:
		oRes = None

	return oRes	

def RemoveNonAscii(s): 
    return "".join(i for i in s if ord(i)<128)

def SaveDFTable(dcDFTable, sCode="DFTABLE"):
    # save the table to the db
    sData = pickle.dumps(dcDFTable)
    sData = MySQL_Escape(sData)
    sSQL=SQLSelectUtility(sCode)
    rs = MySQL_NewUpdateSet(sSQL)
    rs["utils_data"] = sData
    MySQL_Update(rs)

def UpdateDFTable(dcDFTable, dcTFTable):

    # update the table
    if (dcDFTable!=None):
        for sKey, sValue in dcTFTable.iteritems():
            try:
                dcDFTable[sKey]=dcDFTable[sKey]+1
            except:
                dcDFTable[sKey]=1 

# new functions to handle tweets that have tags in the stemmed data
global TAG_SEPERATOR ; TAG_SEPERATOR = "/////"

# sData is a string like: @HayatAsaad_ NN:بآح النور ? VV:حط/////PRO:ي NN:حرف ( NN:صآد ) VV:سيتو ?
# i.e. it contains words like حطي that have been tagged and stemmed and stored as: VV:حط/////PRO:ي
# take out the tags and in places where we have the ///// seperator as we are only interested in the VV or the NN bit
def ReduceStemmedTagged(sData, lTAGS):
    global TAG_SEPERATOR
    sRes = ""
    asParts = sData.split(" ")
    for sPart in asParts:
        if TAG_SEPERATOR in sPart:
            asParts2 = sPart.split(TAG_SEPERATOR)
            for sPart2 in asParts2:
                sTag = sPart2.split(":")[0]
                sWord = sPart2.split(":")[1]
                if sTag in lTAGS:
                    # we want to preserve the tag and the word it belongs to, in such
                    # a way that they dont get separated if we tokenise or split 
                    sResWord = sTag + sWord
                else:
                    # we are not interested in the tag, so keep the word only
                    sResWord = sWord
        else:
            # it not a multi-part object, so we want to preserve the tags in the lTAGS list only
            sResWord = sPart
            for sTag in lTAGS:
                sResWord = sResWord.replace(sTag + ":", sTag)
            
            # remove any tags (not the data that get turned into tokens regardless of what we do)
            if sResWord.startswith('RR:'): sResWord=sResWord[3:]
            if sResWord.startswith('HH:'): sResWord=sResWord[3:]
            if sResWord.startswith('PUNC:'): sResWord=sResWord[5:]

            # remove the other tags that came from the stemmer
            sResWord = sResWord.replace("CONJ:","")
            sResWord = sResWord.replace("IN:","")
            sResWord = sResWord.replace("PRO:","")
        
            # remove any other tag that we havent handled already that we come across
            OTHER_TAGS = ['CC', 'CD', 'CO', 'CONJ', 'DT', 'EMOJ', 'EMOT', 'FU', 'FW', 'HH', 'IN', 'JJ', 'JJR', 'JJS', 'LINK', 'LS', 'MD', 'MEN', 'NN', 'NNP', 'NNPS', 'NNS', 'NP', 'PN', 'PR', 'PRO', 'PRP', 'PUNC', 'PX', 'RB', 'RP', 'RR', 'SP', 'SYM', 'TO', 'UH', 'USERN', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'VV', 'WP', 'WR', 'WRB', 'ZZ']
            for sTag in OTHER_TAGS:
                sResWord = sResWord.replace(sTag + ":", "")

        sResWord=sResWord.strip()

        if sRes=="":
            sRes = sResWord
        else:
            if sResWord<>"":
                sRes = sRes + " " + sResWord

    return sRes

# sData is a string like: @HayatAsaad_ NN:بآح النور ? VV:حط/////PRO:ي NN:حرف ( NN:صآد ) VV:سيتو ?
# i.e. it contains words like حطي that have been tagged and stemmed and stored as: VV:حط/////PRO:ي
# take out all tags and in places where we have the ///// seperator as we are only interested in keeping
# the bits specified by lTAGS. ***NO TAGS ARE OUTPUT**
def ReduceStemmedTagged2(sData, lTAGS):
    global TAG_SEPERATOR
    sRes = ""
    asParts = sData.split(" ")
    for sPart in asParts:
        if TAG_SEPERATOR in sPart:
            asParts2 = sPart.split(TAG_SEPERATOR)
            for sPart2 in asParts2:
                sTag = sPart2.split(":")[0]
                sWord = sPart2.split(":")[1]
                if sTag in lTAGS:
                    # we want to preserve the word we tokenise or split 
                    sResWord = sWord
        else:
            # it not a multi-part object, so we want to preserve no tags at all
            sTag = sPart.split(":")[0]
            sWord = sPart.split(":")[1]
            sResWord = sWord

        sResWord=sResWord.strip()

        if sRes=="":
            sRes = sResWord
        else:
            if sResWord<>"":
                sRes = sRes + " " + sResWord

    return sRes


