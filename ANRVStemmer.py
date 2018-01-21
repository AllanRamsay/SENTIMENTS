#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################
#														#
# English stemmer utilising Morphy to stem 4 ways and	#
# take the shortest					 					#
# 17/11/2017											#
#														#
#########################################################

import nltk

# next 3 lines are used to access files in other folders
import NLTKTokeniser2

import os, sys
import cLibrary
from cNLPLibrary import Morphy

# class to accept data, clean it, tag it, stem it and return it to consumer line-by-line
class ARNVStemmerHelper:
	RowData = []
	IsDirty = False

	def Append(self, oItem):
		self.RowData.append(oItem)
		self.IsDirty = True

	def Clear(self):
		self.RowData = []
		self.IsDirty = False

	# stem 4 different ways and take the shortest
	def MorphyStemANRV(self, sWord):
		# include the original so we always have something returned
		lWords = [sWord]

		# Syntactic category: n for noun files, v for verb files, a for adjective files, r for adverb files. 
		sWordA = Morphy(sWord.lower(), "a")
		sWordN = Morphy(sWord.lower(), "n")
		sWordR = Morphy(sWord.lower(), "r")
		sWordV = Morphy(sWord.lower(), "v")

		# see if any words were returned by morphy
		if ((sWordA!=None) and (sWordA!=sWord)): 
			lWords.append(sWordA)
		elif ((sWordN!=None) and (sWordN!=sWord)): 
			lWords.append(sWordN)
		elif ((sWordR!=None) and (sWordR!=sWord)): 
			lWords.append(sWordR)
		elif ((sWordV!=None) and (sWordV!=sWord)): 
			lWords.append(sWordV)

		# take the shortest
		lWords = sorted(lWords, key=len)
		sRes = lWords[0]

		return sRes 

	def StemARNV(self):

		for sTaggedLine in self.RowData:
			sTaggedLine = cLibrary.StripNewline(sTaggedLine)
			sTaggedLine = cLibrary.RemoveSpaces(sTaggedLine)
			asTaggedParts = NLTKTokeniser2.casual_tokenize(sTaggedLine)

			# stem each word
			sStemmedLine = ""
			for sWord in asTaggedParts:
				sItem = self.MorphyStemANRV(sWord)
				sStemmedLine = sStemmedLine + " " + sItem
		
		sStemmedLine = cLibrary.RemoveSpaces(sStemmedLine)
		sStemmedLine = sStemmedLine.strip()

		return sStemmedLine

# Standard boilerplate to call the main() function to begin
# the program. FOR TESTING ONLY FOR TESTING ONLY FOR TESTING ONLY
if __name__ == '__main__':
	oS = ARNVStemmerHelper()

	for i in range(1,100):
		oS.Append(u"The man was walking. 😀 #happy @fred http://www.bbc.co.uk taz@taz.com")
		oStemmedResults = oS.StemARNV()
		print oStemmedResults
		oS.Clear()
		oS.Append(u"The man went walking. 😀 #happy @fred http://www.bbc.co.uk taz@taz.com")
		oStemmedResults = oS.StemARNV()
		print oStemmedResults

