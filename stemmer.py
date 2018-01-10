
import sys, os

import re, a2bw, sys
from useful import *
from a2bw import convert, a2bwtable, bw2atable

import gc
try:
    import buck
except:
    print "Couldn't import buck.py (but probably didn't need to)"

"""
(?P<name>xya*b) will match any sequence like "xyaaaab" and call it "name"

(?(name)(abcd)|(pqrs)): if some group called "name" has already been matched, then this
will match "abcd", otherwise it will match "pqrs". This is fancy, and means that these things
are not really regexes and therefore matching is not linear time (https://swtch.com/~rsc/regexp/)
"""
rep = re.compile("(?P<x>.)(?P=x)+")

"""
Y
shadda, sukun

verb roots cannot have A as an internal vowel unless there are only
two consonants: they may have an A at the end as a mistake for Y

lookupword("EtAk", "VB") should be [['TENSE', ''], ['VDERIV', ''], ['VROOT', 'EtA'], ['PERSON', ''], ['PRON1', 'k]]

"h" as alternative to "p"

"A" is turning up as imperative where Hanady wants it to be present tense

If we allow short verb roots we get errors; if we allow long verb roots we get errors

lookupword("bdxl", "VB"): if we had lookupword("bOdxl", "VB") we'd get
what we want. But we don't, we have lookupword("bdxl", "VB")

>>> lookupword("nwyt", "VB")
[['TENSE', 'n'], ['VDERIV', ''], ['VROOT', 'wyt'], ['PERSON', '']]

Hanady wants (but probably can't have)

[['TENSE', ''], ['VDERIV', ''], ['VROOT', 'nwy'], ['PERSON', 't']]

jytnA should jyt+nA as suffix, but instead we get jytn+A.
"""
simpleNPatterns = {"NOUN": ".{2,3}",
"NCONJ": "w",
"PREP": "b|k|l",
"ART": "Al",
"PRON": "(?(G2)k)|kmA|km|kn|h(A+)|hm(A*)|hn|hm|nA|y",
"CASE": "SV | AF | (?(G2)A)",
"NN": "NCONJ? VOC? PREP? DET? NOUN ((AGREE PRON?)|CASE?)",}

patterns = {"LV": "A|w|y",
            "SV": "i|o|u|a",
            "V": "#SV? (#SV| #LV)",
            "CA": "[^AiouapF]",
            "CB": "[^iouapFy]",
            "X": "[^AiouapFwy]",
            "RC1": "(?P<C1>#CA)(?P=C1)*?",
            "RC2": "(?P<C2>#CA)(?P=C2)*?",
            
            # Three bits: at least one C+V*, then up to two C+V*s, then a C or A
            # G2 will be bound if there are at least three consonants in the root
            "ROOT": "((#RC1|^A) ((?P<V1>#V)(?P=V1)*)?) (?P<G2>(#RC2 ((?P<V2>#V)(?P=V2)*)?)){,3}? #CB",
            "VROOT": "(#RC1 ((?P<V1>#V)(?P=V1)*)?) (?P<G2>(#RC2 ((?P<V2>#V)(?P=V2)*)?)){,3}? #CA",
            
            "NDERIV": "mu?(?=(#X #V?){3,})|A(?=(.t.A))|A(s+)t|mst|Ist|I(?=..A)",
            "ADJ": "y",
            "NSTEM": "Allh|(NDERIV? ROOT ADJ?)",
            
            "VDERIV": "t(u|.A)|A(?=[^s].t)|(?<=(y|n|t))st|(?<!(y|t|n))Ast|An",
            "VSTEM": "VDERIV? VROOT",
            
            "XSTEM": "(#CA #V?){3,}",
            "NCONJ": "(w|f)(?=(Al|#XSTEM))",
            "VCONJ": "(w|f) (?=#XSTEM)",
            "NEG": "(m|l)A(?=...)",
            "INT": "O",
            "PREP": "(ba?|k(?:i?)|l)",
            "PREP1": "#PREP (?=(#DET|(#CA #V?){3,}))",
            "DET": "Al|(?<=l)l",
            
            "PX": "k(?:u?mA?|n|)|h(u?m)?(?:A*)|hn|nA|y",
            "PRON": "(?(G2)k)|k(?:u?mA?|n)|h(u?m)?(?:A*)|hn|nA|y",
            "PRON1": "#PRON|#NY",
            "NY": "ny",
            "PRON2": "#PREP #PRON1",
            
            "FUT": "s|H|h|b",
            "IV": "((?P<ON>O|(n(?=[^Awy]{3})))|(?P<Y>y)|(?P<T>t))(a|u)?",
            "PV": "(?P<PAST>)",
            "IMPER": "(?P<IMP>A)",
            "TENSE": "(FUT? IV)|PV",
            
            "AGR_ON": "",
            "AGR_A": "(?<=(.{3}))(?<!(?:n|h))A",
            "AGR_Y": "(?:An|#AGR_A|w(A|n)|n|)",
            "AGR_T": "(?:yn|An|wn|n|)",
            "AGR_PAST": "t(mA?|n?)|#AGR_A|wA|nA?|",
            "AGR_IMPER": "(#AGR_A|wA|n|)",
            "PERSON": "(?(ON)AGR_ON|(?(Y)AGR_Y|(?(T)AGR_T|(?(PAST)AGR_PAST|(?(IMP)AGR_IMPER)))))",

            "VOC": "yA",
            
            # "AGREE": "tAn|wn|yn|p|h|An|At|", 
            # "An" removed because it introduces too many false positives 
            # (people don't use duals in tweets)
            # Re-added, but only for words with tri-literal stems
            "AGREE": "tAn|wn|yn|a?p|t(?=.)|At|\|t|(?(G2)An)|", 
            
            "CASE": "SV | AF | FA? | (?(G2)(?<!(h|n))Axxxxx)",
            "ALLAH": "A?llh",
            "NAME": "Allh?",
            
            "NN": "(NCONJ? VOC? PREP? (PX$|(NAME | DET? NSTEM AGREE) (((ALLAH|PRON)?) | CASE?)))",
            "VB": "VCONJ? NEG? (IMPER|(INT? TENSE)) VSTEM PERSON (?(G2)(PRON1)?)"}

def arabisepattern(p, patterns):
    return re.compile("([a-z][a-zA-Z]*)|[A-Z][a-z][a-zA-Z]*|AF?(?=[^A-Z1-2])").sub(lambda g: convert(g.group(0), bw2atable).decode("UTF-8"), patterns[p])

def arabisepatterns(patterns=patterns):
    arabicPatterns = {}
    for x in patterns:
        arabicPatterns[x] = arabisepattern(x, patterns)
    return arabicPatterns

"""
For each pattern, replace anything that is in uppercase, possibly with digits,
and is in the set of patterns, by the expansion of its value in the set, i.e.
replace "CONJ" in "(CONJ)?(DEFDET)?(STEM)(AGREE)?(PRON)?" by "w|B". Do this
recursively (e.g. VERBs contain TENSEs, but TENSEs contain FUTs and TNS1s)
"""
def expandpattern(p, patterns=patterns, expanded=False):
    if expanded == False:
        expanded = {}
    for i in re.compile("(?P<hash>#?)(?P<name>([A-Z0-9]|_)+)\s*").finditer(p):
        name = i.group("name")
        hash = i.group("hash")
        wholething = i.group(0)
        if name in patterns:
            if hash == "":
                p = p.replace(wholething, "(?P<%s>%s)"%(name, expandpattern(patterns[name], patterns, expanded)))
            else:
                p = p.replace(wholething, "(%s)"%(expandpattern(patterns[name], patterns, expanded)))
            expanded[name] = p
    return p

"""
Do that for all your patterns.

Once you've done it, replace the values by compiled regexes that have ^ and $
to make sure that they match the whole string
"""
def expandpatterns(patterns=patterns):
    expanded = {}
    epatterns = {p:expandpattern(patterns[p], patterns, expanded) for p in patterns}
    for p in epatterns:
        try:
            epatterns[p] = re.compile("^"+epatterns[p].replace(" ", "")+"$")
        except Exception as e:
            pass
    return epatterns

"""
Now just lookup the tag in the set of patterns and see if it matches your string

>>> m = lookupword("wsyktbwnh", "VERB")
>>> m = lookupword("wsyktbwnh", "NOUN")

This will give you a "match object". You can ask it what its stem is

>>> m.group("stem")
'ktb'

Or you can ask it what all its groups are: 

>> m.groups()
('w', 'sy', 's', 'y', 'ktb', 'wn', 'h')

It will go VERY fast. 500K words a second or so (slower now: 120Kw/s)
"""

class TAGPAIR:

    def __init__(self, tag, form, bw=False):
        self.tag = tag
        self.form = form
        self.bw = bw

    def __repr__(self):
        if self.bw:
            return "%s/%s/%s"%(self.tag, self.form, self.bw)
        else:
            return "%s/%s"%(self.form, self.tag)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return self.tag == other.tag and self.form == other.form
    
    def match(self, other):
        if self.tag == "???" or other.tag == "???":
            return self.form == other.form
        elif self.tag == other.tag:
            return self.form == "???" or other.form == "???" or self.form == other.form
        
EXPANDEDPATTERNS = expandpatterns()
try:
    ARABICPATTERNS = expandpatterns(arabisepatterns())
except:
    print "Couldn't do arabisepatterns"

STANDARDGROUPS = {"NN": ["NCONJ", "VOC", "PREP", "PX", "NAME", "DET", "NSTEM", "AGREE", "PRON", "ALLAH", "CASE"], 
                  "VB": ["VCONJ", "NEG", "IMPER", "INT", "FUT", "IV", "PV", "VSTEM", "PERSON", "PRON1", "PRON2"]}
import datetime
        
def lookupword(w, tag, expandedpatterns=EXPANDEDPATTERNS, tags=STANDARDGROUPS, N = False, arabic=True):
    if N:
        T0 = datetime.datetime.now()
        for i in range(N):
             lookupword(w, tag, expandedpatterns, tags=tags, arabic=arabic)
        T1 = datetime.datetime.now()
        print "%dK words/second"%(N/((T1-T0).total_seconds()*1000))
    else:
        if arabic:
            w = buck.uni2buck(w)
        w = w.replace(">", "O").replace("<", "I").replace("&", "W").replace("o", "")
        m = expandedpatterns[tag].match(w)
        if tags:
            try:
                g = m.groupdict()
                return [TAGPAIR(x, g[x]) for x in tags[tag] if x in g and not g[x] == None]
            except:
                return False
        else:
            return m

def shortform(t):
    return [x for x in t if not x[1] == None]

def getRoot(tags):
    for p in tags:
        if "ROOT" in p.tag:
            return p
    return False
        
def tagXandY(x, bw, tag, alttag, groups=STANDARDGROUPS):
    k0 = False
    try:
        k0 = lookupword(bw, tag, tags=groups)
        if not k0:
            k0 = lookupword(bw, alttag, tags=groups)
        k0 = x+[bw, "main", k0]
    except:
        pass
    return k0

def shaddas(s0):
    s1 = ""
    for c in s0:
        if not c == "o":
            if c == "~":
                try:
                    c = s1[-1]
                except:
                    pass
            s1 += c
    return s1

def readGS(ifile="GoldStandard.csv", N=1000000000):
    gs = [x.strip().split(",") for x in set(open(ifile).read().split("\n")[2:N])]
    return [x+[shaddas(convert(x[0].decode("UTF-8")))] for x in gs if len(x) > 1 and x[1][:2] in ["NN", "VB"]]
    
def lookupall(gs="GoldStandard.csv", groups=STANDARDGROUPS, N=1000000, both=True):
    if isinstance(gs, str):
        gs = readGS(gs)
    gc.collect()
    T0 = datetime.datetime.now()
    stemmed = []
    for x in gs:
        tag = x[1]
        form = x[0]
        bw = x[2]
        if tag[:2] == "NN":
            stemmed.append(tagXandY(x, bw, "NN", "VB", groups))
        elif tag == "VB":
            stemmed.append(tagXandY(x, bw, "VB", "NN", groups))
    T1 = datetime.datetime.now()
    print "%s words/second"%(int(len(stemmed)/((T1-T0).total_seconds())))
    return stemmed

def indexGSbyTag(stemmed):
    indexed = {}
    for s in stemmed:
        if len(s) == 5:
            for t in s[-1]:
                x = str(t)
                if not "ROOT" in t.tag:
                    if not x in indexed:
                        indexed[x] = []
                    if not s in indexed[x]:
                        indexed[x].append(s)
    return indexed
    
def showGS(gs, useAlt=[], N=0):
    i = 0
    for x in gs:
        if x[-2] in useAlt or x[-2] == "main":
            i += 1
            print i, "\t".join(map(str, x))
            if i == N:
                return

def showAllIndexed(indexed, useAlt=[], N=20):
    for i in sorted(indexed.keys()):
        print "\n#### %s (%s) ####\n"%(i, len(indexed[i]))
        showGS(indexed[i], useAlt=useAlt, N=N)

def doItAll():
    showAllIndexed(indexGSbyTag(lookupall()), useAlt=["better"])
    
def printboth(stemmed, pyastemmed):
    pos = re.compile(".*pos: (?P<TAG>\S*)\s.*", re.DOTALL)
    pyad = re.compile("^\+|{|}|\+$")
    s = []
    colours = {}
    for i, (x, y) in enumerate(zip(stemmed, pyastemmed)):
        if set(x[0]).issuperset(x[2]):
            continue
        if len(x[2]) == 1:
            continue
        x5 = x[5]
        if not x5:
            x5 = ""
        try:
            if isinstance(x5, list):
                x5 = "+".join([str(m) for m in x5])
                x5 = re.compile("\+/[A-Z]*").sub("", x5)
        except:
            pass

        xu = x5
        xu = xu.replace("All/NAME", "Allh/NAME")
        xu = xu.replace("+A/CASE", "+AF/CASE")
        xu = xu.replace("+l/DET", "+Al/DET")
        xu = re.compile("/[^\+]*").sub("", xu)
        xu = re.compile("^\+|\+$").sub("", xu)
        xu = re.compile("\++").sub("+", xu)
        xu = xu.replace("}", "")
        xu = xu.replace("+FA", "+AF")
        xu = xu.replace("+F", "+AF")
        if not y and not xu:
            colour = "PURPLE"
        elif xu in y:
            colour = "BLACK"
        elif xu == "":
            colour = "GREEN"
        elif not y:
            colour = "BLUE"
        else:
            colour = "RED"
        try:
            r = "%s	%s	%s	%s		%s		%s"%(x[1], x[0].decode("UTF-8"), x[2], x5, ";".join(y), colour)
        except:
            try:
                r = "%s	%s	%s	%s		%s		%s"%(x[1], x[0], x[2], x5, ";".join(y), colour)
            except:
                continue
        s.append(r)
        try:
            colours[colour].append(r)
        except:
            colours[colour] = [r]
        
    u = []
    for x in s:
        try:
            u.append(x.encode("UTF-8"))
        except:
            pass
    for c in colours:
        print "%s: %s"%(c, len(colours[c]))
    return sorted(u), colours
    
def NATEST(word, tag):
    return  " ".join(["%s/%s"%(buck.buck2uni(x.form), x.tag) for x in lookupword(word, tag)])


DERIVGROUPS = {"NN": ["NCONJ", "VOC", "PREP", "PX", "NAME", "DET", "NSTEM", "PRON", "ALLAH"], 
               "VB": ["VCONJ", "NEG", "VSTEM", "PRON1", "PRON2"]}

def stemBest(word, tags=DERIVGROUPS, forNabeela=False, UTF8=False):
    wn = lookupword(word, "NN", tags=tags)
    wv = lookupword(word, "VB", tags=tags)
    if not wn:
        if not wv:
            return [word]
        else:
            w = wv
    else:
        if not wv:
            w = wn
        else:
            nparts = {x.tag:x.form for x in wn}
            if not "NSTEM" in nparts:
                try:
                    w = nparts["NAME"]
                except:
                    w = word
            else:
                vparts = {x.tag:x.form for x in wv}
                if len(vparts["VSTEM"]) < len(nparts["NSTEM"]):
                    w = wv
                else:
                    w = wn
    if forNabeela:
        nresult = w
        if not isinstance(w, str):
            for x in w:
                if "STEM" in x.tag:
                    nresult = x.form
                    break
        if UTF8:
            return a2bw.convert(nresult, a2bw.bw2atable)
        else:
            return nresult
    else:
        try:
            return ["%s:%s"%(x.form, x.tag[0]) for x in w]
        except:
            return [w]
    prefixes = []
    for p in w:
        if "STEM" in p.tag:
            break
        else:
            prefixes.append(p.form)
            word = word[len(p.form):]
    suffixes = []
    for s in reversed(w):
        if "STEM" in s.tag:
            break
        else:
            if not s.form == "":
                suffixes.append(s.form)
                word = word[:-len(s.form)]
    suffixes.reverse()
    return prefixes+[word]+suffixes
        
def stemAll(text0):
    text1 = []
    for w in text0.split(" "):
        text1 += stemBest(w)
    return text1

    
