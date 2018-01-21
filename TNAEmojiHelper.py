#!/usr/bin/python
# -*- coding: utf-8 -*-

#############################################################
#                                                       	#
# Routines to handle emojis					                #
# 10/09/2017   												#
#                                                       	#
# 18/12/2017 Updated name of EMOJIS variable                #
#############################################################

import os, sys
import NLTKTokeniser2
import TNAWordAnalyser
    
# things that dont get picked up
global TNA_EMOJI_HELPER_EMOJIS ; TNA_EMOJI_HELPER_EMOJIS = [u'☔',u'¤', u'¥', u'§', u'«', u'°', u'±', u'¶', u'»', u'×', u'÷', u'؈', u'؏', u'٭', u'۝', u'۞', u'ۤ', u'۩', u'च', u'जनत', u'ट', u'टजनत', u'त', u'तभ', u'द', u'भ', u'म', u'मस', u'र', u'रष', u'रस', u'ा', u'ी', u'ू', u'ो', u'्', u'আ', u'ৡ', u'ஒ', u'௸', u'ಠ', u'ರ', u'ೋ', u'็', u'้', u'์', u'ํ', u'๏', u'๑', u'๓', u'๓άηΐ', u'๛', u'༺', u'༻', u'ཌ', u'ད', u'ན', u'ོ', u'࿇', u'࿐', u'რ', u'ღ', u'Ꮜ', u'ᒧɕ', u'ᓚɺɹ', u'ᔕ', u'ᕙ', u'᛭', u'ᴍᴀʀʏᴀᴍ', u'ᴖ', u'ᴗ', u'ᴴᴰ', u'ᵏ', u'᷂', u'ἔ', u'–', u'—', u'―', u'‘', u'’', u'‚', u'“', u'”', u'•', u'…', u'‰', u'″', u'‶', u'‸', u'‹', u'›', u'‿', u'⁞', u'⁩', u'⁰', u'⁺', u'ⁿ', u'₩', u'€', u'₰', u'⃕', u'⃣', u'℅', u'ℓ', u'⅓', u'←', u'↑', u'→', u'↓', u'↚', u'↛', u'↜', u'↝', u'↞', u'↢', u'↣', u'↫', u'↯', u'↳', u'↴', u'↷', u'↼', u'⇀', u'⇇', u'⇈', u'⇊', u'⇐', u'⇓', u'⇘', u'⇜', u'⇠', u'⇡', u'⇣', u'⇤', u'⇦', u'⇩', u'∂', u'∆', u'∑', u'∗', u'√', u'∞', u'∫', u'∿', u'≈', u'≤', u'≥', u'⊕', u'⊙', u'⊱', u'⌘', u'⌜', u'⌝', u'⌣', u'①', u'②', u'③', u'④', u'⑤', u'⑦', u'⒈', u'⒉', u'⒊', u'⒋', u'⒌', u'⒍', u'⒎', u'⒏', u'⒐', u'⒑', u'ⓔ', u'ⓗ', u'ⓝ', u'ⓡ', u'ⓣ', u'ⓤ', u'⓶', u'⓷', u'⓸', u'⓹', u'─', u'━', u'│', u'┃', u'┄', u'┅', u'┆', u'┈', u'┉', u'┊', u'┏', u'┓', u'└', u'┗', u'┛', u'┠', u'┣', u'┫', u'┳', u'┻', u'═', u'║', u'╔', u'╗', u'╭', u'╮', u'╯', u'╰', u'▁', u'▂', u'▃', u'▄', u'▅', u'▆', u'▇', u'█', u'▌', u'░', u'▒', u'▓', u'■', u'□', u'▬', u'▲', u'►', u'▼', u'◄', u'◆', u'◇', u'◉', u'○', u'◌', u'●', u'◐', u'◔', u'◕', u'◘', u'◙', u'◦', u'★', u'☆', u'☇', u'☉', u'☏', u'☚', u'☜', u'☞', u'☟', u'☭', u'☻', u'☼', u'☽', u'♀', u'♂', u'♔', u'♕', u'♙', u'♚', u'♛', u'♞', u'♡', u'♢', u'♤', u'♧', u'♩', u'♪', u'♫', u'♬', u'♯', u'♷', u'⚀', u'⚁', u'⚂', u'⚑', u'⚘', u'⚚', u'⚬', u'⛆', u'⛛', u'⛦', u'✆', u'✎', u'✑', u'✓', u'✗', u'✘', u'✤', u'✦', u'✩', u'✪', u'✫', u'✬', u'✭', u'✮', u'✯', u'✰', u'✵', u'✷', u'✹', u'✺', u'✼', u'✽', u'✾', u'✿', u'❀', u'❁', u'❃', u'❅', u'❆', u'❈', u'❉', u'❊', u'❋', u'❍', u'❖', u'❜', u'❥', u'❦', u'❨', u'❭', u'❯', u'❶', u'❷', u'❸', u'❹', u'❺', u'➊', u'➋', u'➌', u'➍', u'➎', u'➏', u'➐', u'➘', u'➪', u'➯', u'➱', u'➷', u'⿻', u'《', u'》', u'「', u'」', u'【', u'】', u'ꜜ', u'ꜝ', u'', u'ﷺ', u'﷼', u'﷽', u'＊', u'～', u'￦']

def SeparateEmojis(sData, dcNONEmojiIndex, dcEmojiIndex, dcEmojiIDIndex, sPrefix="_", sPostfix="_"):
	global TNA_EMOJI_HELPER_EMOJIS

	PRINT_DEV=False

	if PRINT_DEV:
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		print "TWEET", sData

	asParts = NLTKTokeniser2.casual_tokenize(sData)

	nParts = len(asParts)
	nPart = 0
	sRes=""
	while (nPart < nParts):
		sPart1 = asParts[nPart]
		try:
			sPart2 = asParts[nPart+1]
		except:
			sPart2=""
		sPair = sPart1 + sPart2
		sPair = "\\" + repr(sPair).replace("'","").replace("\\","").replace("u","")

		if PRINT_DEV:
			print "\nsPart1", sPart1
			print "sPart2", sPart2
			print "sPair", sPair

		try:
			oEmoji = sPair.decode('unicode-escape')
			# is the pair an emoji?
			bEIsEmoji = TNAWordAnalyser.IsEmoji(oEmoji)

			# are the singles dingbats or singleton emoji codes?
			bPart1IsEmoji = TNAWordAnalyser.IsEmoji(sPart1)
			bPart2IsEmoji = TNAWordAnalyser.IsEmoji(sPart2)

			# are they odd ones?
			if not bPart1IsEmoji:
				bPart1IsEmoji = sPart1 in TNA_EMOJI_HELPER_EMOJIS
			if not bPart2IsEmoji:
				bPart2IsEmoji = sPart2 in TNA_EMOJI_HELPER_EMOJIS

			if PRINT_DEV:
				print "bEIsEmoji", bEIsEmoji
				print "bPart1IsEmoji", bPart1IsEmoji
				print "bPart2IsEmoji", bPart2IsEmoji

			if bEIsEmoji:
				# the combination is an emoji
				#############print (oEmoji)
				nPart+=2
				# add emoji to dictionary and replace in tweet with an ID
				if not oEmoji in dcEmojiIndex:
					sID = sPrefix + str(len(dcEmojiIndex)) + sPostfix
					dcEmojiIndex[oEmoji] = sID
					dcEmojiIDIndex[sID] = oEmoji
				sResWord = dcEmojiIndex[oEmoji]
			elif bPart1IsEmoji:
				nPart+=1
				if not sPart1 in dcEmojiIndex:
					sID = sPrefix + str(len(dcEmojiIndex)) + sPostfix
					dcEmojiIndex[sPart1] = sID
					dcEmojiIDIndex[sID] = sPart1
				#sResWord = sPart1
				sResWord = dcEmojiIndex[sPart1]
			elif bPart2IsEmoji==12345: ##########never call
				nPart+=1
				if not sPart2 in dcEmojiIndex:
					sID = sPrefix + str(len(dcEmojiIndex)) + sPostfix
					dcEmojiIndex[sPart2] = sID
					dcEmojiIDIndex[sID] = sPart2
				#sResWord = sPart1
				sResWord = dcEmojiIndex[sPart1]
			else:
				dcNONEmojiIndex[sPart1]=1
				sResWord = sPart1
				nPart+=1
		except BaseException, ex:
			#print ("TNAEmojiHelper.SeparateEmojis: Unexpected error", ex, sys.exc_info()[0])
			sResWord = sPart1
			nPart+=1
			pass
	
		if sRes=="":
			sRes = sResWord
		else:
			sRes = sRes + " " + sResWord

		if PRINT_DEV:
			print "sRes", sRes

	sRes = sRes.strip()

	if PRINT_DEV:
		print "\n"

	return sRes



"""



SyntaxError: invalid syntax
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> emoji_pattern = re.compile(
... u"(\u0001[\uf900-\uf9ff])"
... "+", flags=re.UNICODE)
>>> 
>>> 
>>> 
>>> 
>>> emoji_pattern.match(emoji)
>>> 
>>> 
>>> emoji
u'\U0001f923'
>>> emoji_pattern.pattern
u'(\x01[\uf900-\uf9ff])+'
>>> 
>>> 
>>> 
>>> emoji_pattern = re.compile(
... u"(\u0001[\uf900-\uf9ff])" #
... u"(\ud83c[\udf00-\uffff])|" # symbols & pictographs (1 of 2)
... u"(\ud83d[\u0000-\uddff])|" # symbols & pictographs (2 of 2)
... u"(\ud83d[\ude80-\udeff])|" # transport & map symbols
... u"(\ud83c[\udde0-\uddff])" # flags (iOS)
... "+", flags=re.UNICODE)
>>> 
>>> 
>>> emoji_pattern.pattern
u'(\x01[\uf900-\uf9ff])(\ud83c[\udf00-\uffff])|(\ud83d[\x00-\uddff])|(\ud83d[\ude80-\udeff])|(\ud83c[\udde0-\uddff])+'
>>> emoji_pattern.pattern.__class_
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'unicode' object has no attribute '__class_'
>>> emoji_pattern.pattern.__class__
<type 'unicode'>
>>> x = emoji[0]
>>> x
u'\ud83e'
>>> emoji
u'\U0001f923'
>>> emoji[1]
u'\udd23'
>>> emoji[2]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: string index out of range
>>> y = emoji[1]
>>> x
u'\ud83e'
>>> y
u'\udd23'
>>> x<y
True
>>> y < emoji[0]
False
>>> x
u'\ud83e'
>>> 
>>> 
>>> x
u'\ud83e'
>>> y
u'\udd23'
>>> 
>>> 
>>> 
>>> temp = u"\u0001F900"
>>> temp[0]
u'\x01'
>>> temp[1]
u'F'
>>> temp
u'\x01F900'
>>> 
>>> 
>>> 
>>> 
>>> temp = u"\u0001F9FF"
>>> temp[0]
u'\x01'
>>> temp[1]
u'F'
>>> temp[2]
u'9'
>>> temp[3]
u'F'
>>> temp[4]
u'F'
>>> temp
u'\x01F9FF'
>>> temp = x"0001f9ff"
  File "<stdin>", line 1
    temp = x"0001f9ff"
                     ^
SyntaxError: invalid syntax
>>> temp = u"\u1F900"
>>> temp[0]
u'\u1f90'
>>> temp[1]
u'0'
>>> 
>>> temp = u"\u1F9FF"
>>> temp[0]
u'\u1f9f'
>>> temp[1]
u'F'
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> emoji_pattern = re.compile(
... u"(\uD83E[\uDD00-\uDDFF])"
... "+", flags=re.UNICODE)
>>> 
>>> 
>>> emoji_pattern.pattern
u'(\ud83e[\udd00-\uddff])+'
>>> 
>>> emoji_pattern.match(emoji)
<_sre.SRE_Match object at 0x1041b2198>
>>> 
>>> x  = emoji_pattern.match(emoji)
>>> x
<_sre.SRE_Match object at 0x1041bb648>
>>> x.groups
<built-in method groups of _sre.SRE_Match object at 0x1041bb648>
>>> x.groups(0)
(u'\U0001f923',)
>>> x.groups
<built-in method groups of _sre.SRE_Match object at 0x1041bb648>
>>> x.groups()
(u'\U0001f923',)
>>> emoji_pattern.match(emoji)
<_sre.SRE_Match object at 0x1041b2198>
>>> emoji2 = u"fred"
>>> 
>>> 
>>> emoji_pattern.match(emoji2)


"""
