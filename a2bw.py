#!/usr/bin/env python
# -*- coding: utf-8 -*-

def safestr(x):
    try:
        x = str(x)
        while x[-1] > "z":
            x = x[:-1]
        return x
    except:
        return str(x[:-1])

a2bwtable = {"ا".decode('utf-8') : "A",
             "أ".decode('utf-8') : "O",
             "ب".decode('utf-8') : "b",
             "ت".decode('utf-8') : "t",
             "ث".decode('utf-8') : "v",
             "ج".decode('utf-8') : "j",
             "ح".decode('utf-8') : "H",
             "خ".decode('utf-8') : "x",
             "د".decode('utf-8') : "d",
             "ذ".decode('utf-8') : "*",
             "ر".decode('utf-8') : "r",
             "ز".decode('utf-8') : "z",
             "س".decode('utf-8') : "s",
             "ش".decode('utf-8') : "$",
             "ص".decode('utf-8') : "S",
             "ض".decode('utf-8') : "D",
             "ط".decode('utf-8') : "T",
             "ظ".decode('utf-8') : "Z",
             "ع".decode('utf-8') : "E",
             "غ".decode('utf-8') : "g",
             "ف".decode('utf-8') : "f",
             "ق".decode('utf-8') : "q",
             "ك".decode('utf-8') : "k",
             "ل".decode('utf-8') : "l",
             "م".decode('utf-8') : "m",
             "ن".decode('utf-8') : "n",
             "و".decode('utf-8') : "w",
             "ى".decode('utf-8') : "Y",
             "ه".decode('utf-8') : "h",
             "ي".decode('utf-8') : "y",
             "آ".decode('utf-8') : "|",
             "ء".decode('utf-8') : "G",
             "ؤ".decode('utf-8') : "W",
             "ئ".decode('utf-8') : "}",
             "ة".decode('utf-8') : "p",
             "ـ".decode('utf-8') : "" ,
             "ً".decode('utf-8') : "F",
             "ٌ".decode('utf-8') : "N",
             "ٍ".decode('utf-8') : "K",
             "َ".decode('utf-8') : "a",
             "ُ".decode('utf-8') : "u",
             "ِ".decode('utf-8') : "i",
             "ّ".decode('utf-8') : "~",
             "ْ".decode('utf-8') : "o",
             "إ".decode('utf-8') : "I",
             "٠".decode('utf-8') : "0",
             "١".decode('utf-8') : "1",
             "٢".decode('utf-8') : "2",
             "٣".decode('utf-8') : "3",
             "٤".decode('utf-8') : "4",
             "٥".decode('utf-8') : "5",
             "٦".decode('utf-8') : "6",
             "٧".decode('utf-8') : "7",
             "٨".decode('utf-8') : "8",
             "٩".decode('utf-8') : "9",
             ";".decode('utf-8') : ";",
             "£".decode('utf-8') : "P",
             "؟".decode('utf-8') : "?" ,
             "،".decode('utf-8') : "," ,
             "؛".decode('utf-8') : ";" ,
             "-".decode('utf-8') : "-",
             "--".decode('utf-8') : "--",
             "/".decode('utf-8') : "/",
             "“".decode('utf-8') : '"',
             "”".decode('utf-8') : '"',
             "!".decode('utf-8') : "!",
             ":".decode('utf-8') : ":",
             "؛".decode('utf-8') : ";",
             "..".decode('utf-8') : "..",
             "...".decode('utf-8') : "...",
             "^".decode('utf-8') : "^",
             " ".decode('utf-8') : " ",
         }

"""
s = 'بتوقيت'
teststring = 'بتوقيت'.decode('utf-8')
print teststring
"""

def invtable(t0):
     t1 = {}
     for x in t0:
          t1[t0[x]] = x
     return t1

htktable = {"$": "C",
            "*": "F",
            "|": "A",
            "}": "B"}

bw2atable = invtable(a2bwtable)

def convert(s0, table=a2bwtable):
     s1 = u''
     for c in s0:
          try:
               s1 += table[c]
          except:
               s1 += c
     return s1
