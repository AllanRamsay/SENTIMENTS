# -*- coding: utf-8 -*-

import io
import re
from enum import Enum
import itertools
import NLTKTokeniser2

# import files in other folders
import cLibrary
import urllib
import string

#global BW_CHARS
#global BW_CHARS_AR
global goEnglishCharacters
global goPunctuation
global goPunctuationP	# partial set
global goNumeric
global mRE ; mRE = None
global mRE2 ; mRE2 = None
global mRE3 ; mRE3 = None
global gdEmoji ; gdEmoji = None
global glAnerGazet ; glAnerGazet = None
global gdAREN ; gdAREN = {}
global glPrepositions ; glPrepositions = None
global mre_Hashtag ; mre_Hashtag = re.compile(ur"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)" , re.VERBOSE | re.I  | re.UNICODE)
global mre_AtTag ; mre_AtTag = re.compile(ur"(?:@[\w_]+)" , re.VERBOSE | re.I  | re.UNICODE)
global mre_PunctuationAR ; mre_PunctuationAR = re.compile(ur"[،؟!.؛]\s*" , re.VERBOSE | re.I  | re.UNICODE)

URLS = ur"""			# Capture 1: entire matched URL
  (?:
  https?:				# URL protocol and colon
    (?:
      /{1,3}				# 1-3 slashes
      |					#   or
      [a-z0-9%]				# Single letter or digit or '%'
                                       # (Trying not to match e.g. "URI::Escape")
    )
    |					#   or
                                       # looks like domain name followed by a slash:
    [a-z0-9.\-]+[.]
    (?:[a-z]{2,13})
    /
  )
  (?:					# One or more:
    [^\s()<>{}\[\]]+			# Run of non-space, non-()<>{}[]
    |					#   or
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\) # balanced parens, one level deep: (...(...)...)
    |
    \([^\s]+?\)				# balanced parens, non-recursive: (...)
  )+
  (?:					# End with:
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\) # balanced parens, one level deep: (...(...)...)
    |
    \([^\s]+?\)				# balanced parens, non-recursive: (...)
    |					#   or
    [^\s`!()\[\]{};:'".,<>?«»“”‘’]	# not a space or one of these punct chars
  )
  |					# OR, the following to match naked domains:
  (?:
  	(?<!@)			        # not preceded by a @, avoid matching foo@_gmail.com_
    [a-z0-9]+
    (?:[.\-][a-z0-9]+)*
    [.]
    (?:[a-z]{2,13})
    \b
    /?
    (?!@)			        # not succeeded by a @,
                            # avoid matching "foo.na" in "foo.na@example.com"
  )
"""
global mre_URL ; mre_URL = re.compile(URLS , re.VERBOSE | re.I  | re.UNICODE)







class CharacterType(Enum):
	Nothing = 0
	Unknown = 1
	Arabic = 2
	English = 3
	Icon = 4
	Punctuation = 5
	BuckWalter = 6
	Numeric = 7
	Space = 8

def GetEmojiRegex():
	#from stackoverflow
	try:
		# Wide UCS-4 build
		oRes = re.compile(u'(['
			u'\U0001F300-\U0001F64F'
			u'\U0001F680-\U0001F6FF'
			u'\u2600-\u26FF\u2700-\u27BF]+)', 
			re.UNICODE)
	except re.error:
		# Narrow UCS-2  - used
		oRes = re.compile(u'(('
			u'\ud83c[\udf00-\udfff]|'
			u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
			u'[\u2600-\u26FF\u2700-\u27BF])+)', 
			re.UNICODE)
	return oRes

def GetEmojiRegex2():
	oRes = re.compile(
		u"(\ud83d[\ude00-\ude4f])|"  # emoticons
		u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
		u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
		u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
		u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
		"+", flags=re.UNICODE)
	
	return oRes

def GetEmojiRegex3():
	oRes = re.compile(
		u"(\ud83e[\udd00-\uddff])"
		"+", flags=re.UNICODE)

	return oRes

def GetEmojiRegexMINE_NOUSE():
	try:
		# Wide UCS-4 build
		oRes = re.compile(u'['
			u'\U0001F300-\U0001F64F'
			u'\U0001F680-\U0001F6FF'
			u'\u2600-\u26FF\u2700-\u27BF]+', 
			re.UNICODE)
	except re.error:
		# Narrow UCS-2 build
		oRes = re.compile(u'('
			u'\ud83c[\udf00-\udfff]|'
			u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
			u'[\u2600-\u26FF\u2700-\u27BF])+', 
			re.UNICODE)

	return oRes

def InsertPlaceholders(oSet, sSentence, dcTokens):
	for sData in oSet:
		sToken = cLibrary.GetRandomString(20)
		dcTokens[sToken]=sData
		sSentence = sSentence.replace(sData, " " + sToken + " ")
	return sSentence

def ReplacePlaceholders(sSentence, dcTokens):
	for sToken,sData in dcTokens.iteritems():
		sSentence = sSentence.replace(sToken, sData)
	return sSentence

def NormalizeArabic(sText):
	
	if sText!=None:
		
		# [إأٱآا] to  "ا" 
		sText = re.sub(ur"[\u0625|\u0623|\u0671|\u0622|\u0627]", ur"\u0627", sText)

		# "ى" to "ي"
		sText = re.sub(ur"\u0649", ur"\u064A", sText)

		# "ؤ" to "ء"
		sText = re.sub(ur"\u0624", ur"\u0621", sText)

		# "ئ" to "ء"
		sText = re.sub(ur"\u0626", ur"\u0621", sText)

	return sText

def NormaliseSentence(sSentence, dUnknownObjects=None, nDocumPKey=0):
	global mRE
	global mRE2
	global mRE3
	PRINT_DEV=False

	sNewSentence=""

	if (sSentence!="" and sSentence!=None):

		sSentence = cLibrary.RemoveSpaces(sSentence)
		sSentence = cLibrary.StripNewline(sSentence)

		if PRINT_DEV==True: sys.stdout.write("\nINPUT= " + sSentence); sys.stdout.write("\nINPUT (spaces shown by *)= " + sSentence.replace(" ","***"))

		if mRE==None:
			mRE = GetEmojiRegex()
		
		if mRE2==None:
			mRE2 = GetEmojiRegex2()

		if mRE3==None:
			mRE3 = GetEmojiRegex3()

		sSentenceRaw = sSentence

		eLastLetter=CharacterType.Nothing
		eThisLetter=CharacterType.Nothing
		
		# tidy up first
		sSentence=cLibrary.RemoveSpaces(sSentence)

		# we want to preserve URLs, hashtags etc so replace with a random unique token
		oSet1 = set([i for i in sSentence.split() if i.startswith("#")])
		oSet2 = set([i for i in sSentence.split() if i.startswith("@")])	 
		oSet3 = set([i for i in sSentence.split() if i.startswith("http://")])	 
		oSet4 = set([i for i in sSentence.split() if i.startswith("https://")])	 
		oSet5 = set([i for i in sSentence.split() if i.find("@")>-1])	 
		oSet6 = set()

		dcTokens = {}
		sSentence = InsertPlaceholders(oSet1, sSentence, dcTokens)
		sSentence = InsertPlaceholders(oSet2, sSentence, dcTokens)
		sSentence = InsertPlaceholders(oSet3, sSentence, dcTokens)
		sSentence = InsertPlaceholders(oSet4, sSentence, dcTokens)
		sSentence = InsertPlaceholders(oSet5, sSentence, dcTokens)

		# replace flags
		# scan again for missed emojis
		LoadEmojiList()
		for sKey,sValue in gdEmoji.iteritems():
			if sKey in sSentence:
				oSet6.add(sKey)
		sSentence = InsertPlaceholders(oSet6, sSentence, dcTokens)

		if PRINT_DEV==True: sys.stdout.write("\nINPUT (hashtags, RT, flags etc tokenised)= " + sSentence)

		for cLetter in sSentence:
			if IsArabicCharacter(cLetter): eThisLetter=CharacterType.Arabic
			elif IsEnglishCharacter(cLetter): eThisLetter=CharacterType.English
			elif IsBWCharacter(cLetter): eThisLetter=CharacterType.BuckWalter
			elif IsPunctuationCharacter(cLetter): eThisLetter=CharacterType.Punctuation
			elif IsNumericCharacter(cLetter): eThisLetter=CharacterType.Numeric
			#elif IsEmoji(cLetter): eThisLetter=CharacterType.Icon ; print("###")
			elif (cLetter==" "): eThisLetter=CharacterType.Space
			else: eThisLetter=CharacterType.Unknown

			if eThisLetter==CharacterType.Unknown:
				if dUnknownObjects!=None:
					try:
						oList = dUnknownObjects[cLetter]
						oList.append(nDocumPKey)
						dUnknownObjects[cLetter]=oList
					except:
						oList = []
						oList.append(nDocumPKey)
						dUnknownObjects[cLetter]=oList

			if PRINT_DEV==True: sys.stdout.write(cLetter + " ")
			if PRINT_DEV==True: print(cLetter),
			if PRINT_DEV==True: print(ord(cLetter)),
			if PRINT_DEV==True: print(hex(ord(cLetter))),
			if PRINT_DEV==True: print(unichr(ord(cLetter)))

			if (eThisLetter==eLastLetter) or (sNewSentence==""):
				sNewSentence=sNewSentence+cLetter
			else:
				# have changed character class
				if (eLastLetter==CharacterType.Space) or (eThisLetter==CharacterType.Space):
					# last/current character is space, so need to add extra space
					sNewSentence=sNewSentence+cLetter
				else:
					# space out character classes
					sNewSentence=sNewSentence+" "+cLetter
					
			eLastLetter = eThisLetter

		sNewSentence = ReplacePlaceholders(sNewSentence, dcTokens)

		sNewSentence = mRE.sub(r' \1 ', sNewSentence)
		sNewSentence = mRE2.sub(r' \1 ', sNewSentence)
		sNewSentence = mRE3.sub(r' \1 ', sNewSentence)

		sNewSentence = cLibrary.RemoveSpaces(sNewSentence)

		if PRINT_DEV==True: 
			print ("INPUT=" + sSentenceRaw)
			print ("OUTPUT=" + sNewSentence)

	return sNewSentence

def SeparateMultiEmojis(sSentence, PRINT_DEV=False):
	global mRE
	global mRE2
	global mRE3
	
	if (sSentence!="" and sSentence!=None):

		sSentenceRaw = sSentence
		sSentence = cLibrary.RemoveSpaces(sSentence)
		sSentence = cLibrary.StripNewline(sSentence)

		if mRE==None:
			mRE = GetEmojiRegex()
		
		if mRE2==None:
			mRE2 = GetEmojiRegex2()

		if mRE3==None:
			mRE3 = GetEmojiRegex3()

		try:
			sSentence = mRE.sub(r' \1 ', sSentence)
		except:
			pass

		try:
			sSentence = mRE2.sub(r' \1 ', sSentence)
		except:
			pass

		try:
			sSentence = mRE3.sub(r' \1 ', sSentence)
		except:
			pass

		sSentence = cLibrary.RemoveSpaces(sSentence)

		if PRINT_DEV==True:
			if sSentenceRaw != sSentence:
				print ("INPUT=" + sSentenceRaw)
				print ("OUTPUT=" + sSentence)

	return sSentence

def RemoveTokensByClass(sData, bRemoveHashtags, bRemoveEmojis, bRemoveAtTags, bRemoveURLs):
	global gdEmoji
	global mre_Hashtag
	global mre_URL
	global mre_AtTag

	if sData <> "":
		if bRemoveURLs:
			sData = mre_URL.sub("", sData)

		if bRemoveHashtags:
			sData = mre_Hashtag.sub("", sData)

		if bRemoveAtTags:
			sData = mre_AtTag.sub("", sData)

		if bRemoveEmojis:
			# must already be normalised
			print "TNAWordAnalyser:RemoveTokensByClass:bRemoveEmojis TODO"
			exit()
			exit()
			exit()
			LoadEmojiList()
			asParts = NLTKTokeniser2.casual_tokenize(sData) 
			sData = ""
			for sPart in asParts:
				sPart = sPart.strip()
				if sPart in gdEmoji.keys():
					sPart=""
				if sPart!="":
					sData = sData + " " + sPart

	sData = sData.strip()

	return sData

def AnalyseSentenceOLD(sSentenceOld):

	print ("0=",sSentenceOld)
	sSentenceNew = u""
	# check if any place where arabic/english/symbols/emoticons etc 
	# together but not seperated by a space

	# first split words that are mixed language into separate words
	# better to do this in seperate loop because spltting is most important thing
	asWords = sSentenceOld.split(" ")
	sSentenceNew = ""
	for sWord in asWords:
		sWord = sWord.lstrip().rstrip()
		bContainsArabicChars=ContainsArabicChars(sWord)
		bContainsEnglishChars=ContainsEnglishChars(sWord)
		bContainsPunctuation=ContainsPunctuation(sWord)
		bContainsEmoticons=ContainsEmoticons(sWord)
		if (bContainsArabicChars and bContainsEnglishChars) or (bContainsPunctuation):
			sWord = AnalyseWord(sWord)
		sSentenceNew = sSentenceNew + ("" if sSentenceNew=="" else " ") + sWord



	asWords = sSentenceNew.split(" ")
	sSentenceNew = ""
	for sWord in asWords:
		sWord = sWord.lstrip().rstrip()
		sWordBW = transliterateString(sWord, Mode.UnicodeToBuckwalterNew)
		sWordAR = transliterateString(sWordBW, Mode.BuckwalterToUnicode)
		if (sWord!=sWordAR):
			# word does nor BuckWalter properly
			sWord = "[" + sWord + "]"
		sSentenceNew = sSentenceNew + ("" if sSentenceNew=="" else " ") + sWord
	
	"""

	# now check for any words containing BW characters
	asWords = sSentenceNew.split(" ")
	sSentenceNew = ""
	for sWord in asWords:
		sWord = sWord.lstrip().rstrip()
		bContainsBWChars=ContainsBWChars(sWord)
		if (bContainsBWChars==True):
			sWord = "[" + sWord + "]"
		sSentenceNew = sSentenceNew + ("" if sSentenceNew=="" else " ") + sWord

	# now analyse the separate words
	asWords = sSentenceOld.split(" ")
	for sWord in asWords:

		sWord = sWord.lstrip().rstrip()

		bContainsArabicChars=ContainsArabicChars(sWord)
		bIsArabicObject=IsArabicObject(sWord)
		bContainsEnglishChars=ContainsEnglishChars(sWord)
		bContainsBWChars=ContainsBWChars(sWord)

		print (sys.stdout.write("\n" + sWord), 
				" ContainsArabicChars=" + str(bContainsArabicChars), 
				" IsArabicObject=" + str(bIsArabicObject), 
				" ContainsEnglishChars=" + str(bContainsEnglishChars), 
				" ContainsBWChars=" + str(bContainsBWChars))

		if (not bIsArabicObject):

			sNewSentence = AnalyseWord(sWord)
                
		sSentenceNew = sSentenceNew + ("" if sSentenceNew=="" else " ") + sWord.lstrip().rstrip()
	"""

	return sSentenceNew


"""
chek check every char it individually
 if you find something that is not Arabic insert  spaces
 then you will will be left with a bunch of words
 Put each word into Bookwalter
 If the op from Buckwalter contains characters which are not bookwalter
  then put tags aound the  word

also take op and unBW it and should get the original ip . if not then put tags around it
"""


def AnalyseWordOLD(sWord):
	print (sWord + "analysing word")
	sNewSentence=""
	eLastLetter=CharacterType.Nothing
	eThisLetter=CharacterType.Nothing
	
	for cLetter in sWord:
		
		if IsArabicObject(cLetter): eThisLetter=CharacterType.Arabic
		elif IsEnglishObject(cLetter): eThisLetter=CharacterType.English
		elif ContainsBWChars(cLetter): eThisLetter=CharacterType.BuckWalter
		elif IsPunctuationObject(cLetter): eThisLetter=CharacterType.Punctuation
		else: eThisLetter=CharacterType.Unknown

		if eLastLetter==CharacterType.Nothing:
			sNewSentence=cLetter
		else:
			if eThisLetter==eLastLetter:
				sNewSentence=sNewSentence+cLetter
			elif eThisLetter==CharacterType.Punctuation:
				# add seperator
				sNewSentence=sNewSentence+" "+cLetter
			elif eThisLetter==CharacterType.Unknown:
				# flag word and leave
				sNewSentence=sNewSentence+"?"+cLetter
			else:
				# add seperator
				sNewSentence=sNewSentence+" "+cLetter

		eLastLetter = eThisLetter

	return sNewSentence

"""

def HasArabicChars(s):
    var arabic = /[\u0600-\u06FF]/;

    alert(arabic.test(string)); // displays true
    return bRes
    """

"""
def ContainsArabicChars(s):
    return s in BuckWalterDictionary().values()
    return bRes
"""

def ContainsBWChars(s):
	return s in BuckWalterDictionary().keys()

def ContainsEnglishChars(s):
    bRes = any(c in string.letters for c in s)
    return bRes

def ContainsEmoticons(s):
	"""
	emoji_pattern = re.compile("["
			u"\U0001F600-\U0001F64F"  # emoticons
			u"\U0001F300-\U0001F5FF"  # symbols & pictographs
			u"\U0001F680-\U0001F6FF"  # transport & map symbols
			u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
							"]+", flags=re.UNICODE)
	print(emoji_pattern.sub(r'', text))
	"""

def ContainsPunctuation(s):
    return 1 in [c in s for c in string.punctuation]

def IsPunctuationObject(c):
    return [c in string.punctuation]

"""
def IsArabicObject(s):
    bRes = all(c in BW_CHARS_AR for c in s)
    return bRes

def IsBWObject(s):
    bRes = all(c in BW_CHARS for c in s)
    return bRes
"""

def IsEnglishObject(s):
    bRes = all(c in string.letters for c in s)
    return bRes

def IsNumericObject(s):
    bRes = all(c in goNumeric for c in s)
    return bRes

def IsArabicCharacter(c):
    bRes = c in BuckWalterDictionary().values()
    return bRes


def IsArabicObject(s):
    bRes = True
    for c in s:
        bRes = IsArabicCharacter(c)
        if bRes==False:
            break
    return bRes


def IsArabiziObject(s):
	bSeenAlpha=False
	bSeenNumeric=False
	for c in s:
		if IsNumericObject(c):bSeenNumeric=True
		if IsEnglishObject(c):bSeenAlpha=True

	return (bSeenAlpha and bSeenNumeric)


def IsArabiziObject2(s):
	bRes = True
	bRes1 = False
	bRes2 = False
	bRes3 = False
	bRes4 = False

	for c in s:
		bRes1 = IsNumericObject(c)
		bRes2 = IsEnglishObject(c)
		bRes3 = IsArabicCharacter(c)
		bRes4 = IsPunctuationCharacter(c)

		###print c, bRes1, bRes2, bRes3, bRes4

		if not bRes4:
			if bRes3==True or (bRes1==False and bRes2==False):
				bRes=False
				break

	return bRes


def IsBWCharacter(c):
    bRes = c in BuckWalterDictionary().keys()		
    return bRes


def IsBWObject(s):
    bRes = True
    for c in s:
        bRes = IsBWCharacter(c)
        if bRes==False:
            break
    return bRes


def IsEmoji(s):
	global mRE
	global mRE2
	global mRE3

	if mRE==None:
		mRE = GetEmojiRegex()

	if mRE2==None:
		mRE2 = GetEmojiRegex2()

	if mRE3==None:
		mRE3 = GetEmojiRegex3()

	bRes = (len(re.findall(mRE, s))>0)

	if (bRes==False):
		bRes = (len(re.findall(mRE2, s))>0)

	if (bRes==False):
		bRes = (len(re.findall(mRE3, s))>0)

	if (bRes==False):
		# refer to emojis list
		if gdEmoji==None:
			LoadEmojiList()

		bRes = (s in gdEmoji)

	return (bRes)


def IsEnglishCharacter(c):
    bRes = (c in goEnglishCharacters)
    return bRes


def IsNumericCharacter(c):
    bRes = (c in goNumeric)
    return bRes


def IsPunctuationCharacter(c):
    bRes = (c in goPunctuation)
    return bRes

def GetEmojiDescription(oEmoji):
	global gdEmoji
	sRes = ""

	if gdEmoji==None:
		LoadEmojiList()

	try:
		sRes = gdEmoji[oEmoji]
	except:
		pass
	
	return sRes

def LoadEmojiList():
	global gdEmoji

	# get pickled version
	try:
		gdEmoji = cLibrary.LoadObject("TNAWordAnalyser.LoadEmojiList.gdEmoji.pk")
	except:
		pass

	if gdEmoji == None:
		gdEmoji = {}
		print ("Getting emjois from unicode.org")
		sLines = urllib.urlopen("http://www.unicode.org/Public/emoji/1.0/emoji-data.txt").read()
		asLines = sLines.split("\n")
		for sLine in asLines:
			if sLine<>"":
				if (not sLine.startswith("#")):
					sCode = unicode(sLine.split("(")[1].split(")")[0].strip(),"utf-8")
					sDesc = sLine.split(")")[1].strip()
					# print (sCode, sDesc)
					gdEmoji[sCode] = sDesc

		print ("Loading dingbats file...")
		with open('Resources/dingbats.txt') as fDingbats:
			for line in fDingbats:
				sLine = line.strip()
				if (sLine != ""):
					if (sLine[0] != "#"):
						sCode = unicode(sLine.split("\t")[0].strip(),"utf-8")
						sDesc = sLine.split("\t")[4].strip()
						print (sCode, sDesc)
						gdEmoji[sCode] = sDesc

		cLibrary.SaveObject(gdEmoji, "TNAWordAnalyser.LoadEmojiList.gdEmoji.pk")

def RemovePrepositions(sText, sPrepFile="Prepositions.txt"):
	global glPrepositions

	sRes = sText

	if sRes!=None:
		LoadPrepositions(sPrepFile)

		sRes = " " + sRes + " "

		for sPreposition in glPrepositions:
			sRes = sRes.replace(" " + sPreposition + " ", " ")

		sRes = cLibrary.RemoveSpaces(sRes)
		sRes = sRes.strip()

	return sRes

def RemoveEnglish(sText):
	
	if sText!=None:
		sText = re.sub("[a-zA-Z0-9]", "" , sText)

	return sText

def RemoveNumbersAR(sText):
	
	if sText!=None:
		sText = re.sub(ur"[\u0660|\u0661|\u0662|\u0663|\u0664|\u0665|\u0666|\u0667|\u0668|\u0669]", "", sText)

	return sText

def RemoveNumbersEN(sText):
	
	if sText!=None:
		sText = re.sub("[0-9]", "" , sText)

	return sText

def RemovePunctuationCharactersAR(sText):
	global mre_PunctuationAR

	sRes = mre_PunctuationAR.sub("", sText)
	
	return sRes

def RemovePunctuationCharactersEN(sText):
	global goPunctuation

	sRes = sText

	if sRes!=None:

		# preserve URLs, hashtags, at tags etc
		dcTokens = {}
		oSet1 = set([i for i in sRes.split() if i.startswith("#")])
		oSet2 = set([i for i in sRes.split() if i.startswith("@")])	 
		oSet3 = set([i for i in sRes.split() if i.startswith("http://")])	 
		oSet4 = set([i for i in sRes.split() if i.startswith("https://")])	 
		sRes = InsertPlaceholders(oSet1, sRes, dcTokens)
		sRes = InsertPlaceholders(oSet2, sRes, dcTokens)
		sRes = InsertPlaceholders(oSet3, sRes, dcTokens)
		sRes = InsertPlaceholders(oSet4, sRes, dcTokens)

		for sC in goPunctuation:
			sRes = sRes.replace(sC, "")

		sRes = ReplacePlaceholders(sRes, dcTokens)

		sRes = cLibrary.RemoveSpaces(sRes)

	return sRes

"""
def IsArabic(sText):
    oRes = len([None for ch in sText if UD.bidirectional(ch) in ('R', 'AL')])/float(len(sText))
    bRes=False
    if oRes>0.5:
        bRes=True
    return bRes

def IsBuckWalter(s):
    bRes = all(c in BW_CHARS for c in s)

    return bRes
"""

# check whether morphy recognises the word
def IsMorphyWord(sWord):
	from nltk.corpus import wordnet
	bRes = True
	oRes = wordnet.morphy(sWord)
	if oRes == None:
		bRes = False
	return bRes

def LoadANERGazet():
	global glAnerGazet

	if glAnerGazet == None:
		with io.open('/Users/ahmadt/Google Drive/Tools/Fahad/Tagger/Code/FromFahadEfficint/tagger/dist/ProperNames.txt', 'r', encoding='utf-8', errors='replace') as f:
			glAnerGazet = f.readlines()
			glAnerGazet = [oItem.replace("\n","") for oItem in glAnerGazet] 
		print len(glAnerGazet), "ANERGazet items loaded"

def LoadPrepositions(sPrepFile="Prepositions.txt"):
	global glPrepositions

	if glPrepositions == None:
		with io.open('Resources/'+ sPrepFile, 'r', encoding='utf-8', errors='replace') as f:
			glPrepositions = f.readlines()
			glPrepositions = [oItem.replace("\n","") for oItem in glPrepositions] 
		print len(glPrepositions), "Prepositions loaded"

# check if is an ANERGazet word
def IsANERGazetWord(sWord):
	global glAnerGazet
	bRes = False

	LoadANERGazet()

	if sWord in glAnerGazet:
		bRes = True

	return bRes

# sAR				an arabic word
# sEN				Googles translation of the  arabic word
# bPrintAnalysis 	print analysis

def isNE(sAR, sEN, bPrintAnalysis=False):
	global glAnerGazet
	
	bRes = False
	nConfidence = -1
	
	sARRaw = sAR
	sENRaw = sEN

	if bPrintAnalysis:
		print "\nsARRaw", sARRaw
		print "sENRaw", sENRaw

	# check if the translation is an English word
	if not bRes:
		if IsMorphyWord(sEN):
			bRes = False
			nConfidence=101
		else:
			# check if its in ANERGazet
			if not bRes:
				if IsANERGazetWord(sAR):
					bRes = True
					nConfidence = 100

			if not bRes:
				sAR = RemoveHarakaat(sAR)
				if bPrintAnalysis: print "RemoveHarakaat", sAR
				if sAR!="":
					# check if its in ANERGazet
					if IsANERGazetWord(sAR):
						bRes = True
						nConfidence = 90

			if not bRes:
				if sAR!="":
					sAR = RemoveDuplicateCharacters(sAR)
					if bPrintAnalysis: print "RemoveDuplicateCharacters", sAR
					if sAR!="":
						# remove duplicate contiguous characters
						if IsANERGazetWord(sAR):
							bRes = True
							nConfidence = 80

			if not bRes:
				if sAR!="" and sEN!="":
					# check if arabic "translation" is just a transliteration
					sEN = sEN.lower()
					sAR = RemoveArabicVowelLetters(sAR)
					if bPrintAnalysis: print "RemoveArabicVowelLetters", sAR
					sARP = ArabicToPhonetic(sAR)
					if bPrintAnalysis: print "ArabicToPhonetic", sARP
					sEN = RemoveDuplicateCharacters(sEN)
					if bPrintAnalysis: print "RemoveDuplicateCharacters", sEN
					sEN = RemoveEnglishVowelLetters(sEN)
					if bPrintAnalysis: print "RemoveEnglishVowelLetters", sEN
					if sEN.startswith("w"):
						# remove waw
						sEN = sEN[1:]
						if bPrintAnalysis: print "remove waw", sEN
					if sARP == sEN:
						bRes = True
						nConfidence = 70

			if not bRes:
				if sAR!="" and sEN!="":
					#replace p with b with a single token
					#replace p with b with a single token
					#replace g with j with a single token
					sEN = sEN.replace("k","c")
					sARP = sARP.replace("k","c")
					sEN = sEN.replace("p","b")
					sARP = sARP.replace("p","b")
					sEN = sEN.replace("g","j")
					sARP = sARP.replace("g","j")
					if bPrintAnalysis: print "after replace sEN", sEN
					if bPrintAnalysis: print "after replace sARP", sARP
					if sARP == sEN:
						bRes = True
						nConfidence = 50

	if bRes:
		# keep word in volatile glAnerGazet
		if not sAR in glAnerGazet:
			glAnerGazet.append(sAR)

	if bPrintAnalysis: print "returning ", bRes, nConfidence ," for ", sARRaw, sENRaw, "\n"
	
	return bRes, nConfidence

def RemoveHarakaat(text):
	noiseOLD = re.compile(""" ّ    | # Tashdid
								َ    | # Fatha
								ً    | # Tanwin Fath
								ُ    | # Damma
								ٌ    | # Tanwin Damm
								ِ    | # Kasra
								ٍ    | # Tanwin Kasr
								ْ    | # Sukun
								ـ     # Tatwil/Kashida
								 ْ      # some sort of sign
							""", re.VERBOSE)

	# from http://www.fileformat.info/search/google.htm?q=ARABIC&domains=www.fileformat.info&sitesearch=www.fileformat.info&client=pub-6975096118196151&forid=1&channel=1657057343&ie=UTF-8&oe=UTF-8&cof=GALT%3A%23008000%3BGL%3A1%3BDIV%3A%23336699%3BVLC%3A663399%3BAH%3Acenter%3BBGC%3AFFFFFF%3BLBGC%3A336699%3BALC%3A0000FF%3BLC%3A0000FF%3BT%3A000000%3BGFNT%3A0000FF%3BGIMP%3A0000FF%3BFORID%3A11&hl=en
	# and https://alraqmiyyat.github.io/2013/01-02.html

	noise1 = re.compile(ur"""\u064E  | # Fatha
							 \u064F  | # Damma
							 \u0650  | # kasra
							 \u0651  | # shaddah
							 \u0652  | # sukuun
							 \u064B  | # fatHatayn
							 \u064C  | # Dammatayn
							 \u064D  | # kasratayn
							 \u0622  | # madda
							 \u0640  | # taTwiil
							 \u066c  | # 'ARABIC THOUSANDS SEPARATOR' 
							 \u061b  | # 'ARABIC SEMICOLON'
							 \u06E4  | # 'ARABIC SMALL HIGH MADDA'
							 \u060C  | # 'ARABIC COMMA'
							 \u0674  | # 'ARABIC LETTER HIGH HAMZA'
							 \u0653  | # 'ARABIC MADDAH ABOVE'
							 \u06D4  | # 'ARABIC FULL STOP' 
							""", re.VERBOSE)

	text = re.sub(noise1, '', text)

	# text = text.replace(u'ي', u'ى')

	return text

def RemoveArabicVowelLetters(text):

	# from http://www.fileformat.info/search/google.htm?q=ARABIC&domains=www.fileformat.info&sitesearch=www.fileformat.info&client=pub-6975096118196151&forid=1&channel=1657057343&ie=UTF-8&oe=UTF-8&cof=GALT%3A%23008000%3BGL%3A1%3BDIV%3A%23336699%3BVLC%3A663399%3BAH%3Acenter%3BBGC%3AFFFFFF%3BLBGC%3A336699%3BALC%3A0000FF%3BLC%3A0000FF%3BT%3A000000%3BGFNT%3A0000FF%3BGIMP%3A0000FF%3BFORID%3A11&hl=en
	# and https://alraqmiyyat.github.io/2013/01-02.html

	noise1 = re.compile(ur"""\u0627  | # bare alif
							 \u0648  | # waaw
							 \u06CC  | # YAA without 2 dots
							 \u064A  | # YAA with 2 dots
							 \u0622  | # madda
							 \u0623  | # hamza-on-'alif
							 \u0624  | # hamza-on-waaw
							 \u0625  | # hamza-under-'alif
							 \u0626  | # hamza-on-yaa'
							 \u0621  | # hamza-on-the-line

							""", re.VERBOSE)

	text = re.sub(noise1, '', text)

	while '  ' in text:
		text = text.replace('  ', ' ')

	return text

def RemoveDuplicateCharacters(s):
	sRes = ''.join(i for i, _ in itertools.groupby(s))
	return sRes

def RemoveEnglishVowelLetters(sWord):
	sWord = sWord.replace('a','')
	sWord = sWord.replace('e','')
	sWord = sWord.replace('i','')
	sWord = sWord.replace('o','')
	sWord = sWord.replace('u','')
	sWord = sWord.replace('A','')
	sWord = sWord.replace('E','')
	sWord = sWord.replace('I','')
	sWord = sWord.replace('O','')
	sWord = sWord.replace('U','')
	return sWord

def ArabicToPhonetic(sAR):
	global gdAREN

	sRes = ""
	for s in sAR:
		try:
			sRes = sRes + gdAREN[s]
		except KeyError, ex:
			sRes = sRes + "*"
	return sRes

#BW_CHARS, BW_CHARS_AR = GetBWChars()

goEnglishCharacters = set(string.letters)
goPunctuation = set(string.punctuation) # + "…“")#⁉”٪″—»«“،")
goPunctuationP = set(string.punctuation)
goPunctuationP.remove("@")
goPunctuationP.remove("#")
goPunctuationP.remove("/")
goPunctuationP.remove(":")
goPunctuationP.remove("_")
goNumeric = set("0123456789")

gdAREN[u"ا"] =  "a"
gdAREN[u"ب"] =  "b"
gdAREN[u"ت"] =  "t"
gdAREN[u"ث"] =  "s"
gdAREN[u"ج"] =  "j"
gdAREN[u"ح"] =  "h"
gdAREN[u"خ"] =  "k"
gdAREN[u"د"] =  "d"
gdAREN[u"ذ"] =  "z"
gdAREN[u"ر"] =  "r"
gdAREN[u"ز"] =  "z"
gdAREN[u"س"] =  "s"
gdAREN[u"ش"] =  "s"
gdAREN[u"ص"] =  "s"
gdAREN[u"ض"] =  "d"
gdAREN[u"ط"] =  "t"
gdAREN[u"ظ"] =  "z"
gdAREN[u"ع"] =  "a"
gdAREN[u"غ"] =  "g"
gdAREN[u"ف"] =  "f"
gdAREN[u"ق"] =  "q"
gdAREN[u"ك"] =  "k"
gdAREN[u"ل"] =  "l"
gdAREN[u"م"] =  "m"
gdAREN[u"ن"] =  "n"
gdAREN[u"و"] =  "w"
gdAREN[u"ى"] =  "y"
gdAREN[u"ه"] =  "h"
gdAREN[u"ء"] =  "a"
gdAREN[u"ة"] =  "t"
gdAREN[u"إ"] =  "!"
gdAREN[u"٠"] =  "0"
gdAREN[u"١"] =  "1"
gdAREN[u"٢"] =  "2"
gdAREN[u"٣"] =  "3"
gdAREN[u"٤"] =  "4"
gdAREN[u"٥"] =  "5"
gdAREN[u"٦"] =  "6"
gdAREN[u"٧"] =  "7"
gdAREN[u"٨"] =  "8"
gdAREN[u"٩"] =  "9"
gdAREN[u"؟"] =  "?" 
gdAREN[u"،"] =  "," 
gdAREN[u"؛"] =  ";" 
gdAREN[u"“"] =  '"'
gdAREN[u"”"] =  '"'
gdAREN[u"!"] =  "!"
gdAREN[u"•"] =  "."

