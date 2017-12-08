import re, os, sys, shutil, scipy, numpy, codecs
from numpy import dot
import a2bw
import json
from useful import *
from nltk.tokenize import sent_tokenize, word_tokenize
import stemmer
reload(stemmer)
try:
    import dtw
except:
    print "I don't think we currently need dtw"

    
from openpyxl import Workbook
from openpyxl.styles import colors, Font, Color
def toXLSX(lines, xlsxfile="test.xlsx"):
    wb = Workbook()
    ws = wb.active
    try:
        lines = lines.split("\n")
    except:
        pass
    colours = {"RED":colors.RED,
               "BLACK":colors.BLACK,
               "GREEN":"009900",
               "BLUE":colors.BLUE,
               "PURPLE":"bb00bb",
               }
    for l in lines:
        try:
            l = l.split("\t")
        except:
            pass
        ws.append(l)
    for l1, l2 in zip(ws, lines):
        for c in l1:
            try:
                [value, colour] = c.value.split("\t")
                c.font = Font(color=colours[colour])
                c.value = value.decode('ISO-8859-1')
            except:
                pass
    wb.save(xlsxfile)
    
"""
>>> test = makeTFIDF(ENGLISHDEV)
>>> training = makeTFIDF(ENGLISHTRAINING)

# this is just the raw counts
>>> sentidict = makeSentiDict(training)

# this is the one that produces a basic classifier
>>> k0 = makeScoreDict(training, sentidict, N=2500)
>>> plot(test, k0)

This will generate a list of classifiers with a range of thresholds.

>>> k = createAndTuneRange(training, test, sentidict)

# remove misleading words, set a threshold for each 
# sentiment. This a few seconds. The threshold set is now
# stored in the new classifier

>>> k1 = tune(training, k0)

# Put each tweet in a nice looking file: j is the Jaccard value: should be 0.415, f should be 0.586

>>> p, r, f, j, errors = scoreTweets(test, k1, threshold=k1.threshold, out="xxx.xlsx")

"""

TWEETS = 'twitter_samples/tweets.20150430-223406.json'
ENGLISHTRAINING = "Raw/EN/E-c-En-train.csv"
ENGLISHDEV = "Raw/EN/2018-E-c-En-dev.csv"
ARABICDEV = "Raw/AR/2018-E-c-Ar-dev.csv"
ARABICTRAINING = "Raw/AR/2018-E-c-Ar-train.csv"

languagePattern = re.compile("Raw/(?P<language>.*)/.*")

null = None
false = False
true = True

prefixes = re.compile("\s*((rt\s*)?@\S+)+")
urls = re.compile("//t.co/\S*|http|#|:")

class TWEET:

    def __init__(self, id=False, text=False, features=False, scores=False, tokens=False):
        self.id = id
        self.features = normalise(features)
        self.size = self.size()
        self.text = text
        self.GS = scores
        self.tokens = tokens
        
    def __repr__(self):
        return "<%s, %s>"%(self.size, self.text)

    def normalise(v):
        t = sum(v.values())
        for k in v:
            v[k] = v[k]/t
        return v

    def size(self):
        return scipy.sqrt(sum(map(scipy.square, self.features.values())))

    def cos(v1, v2):
        nom = 0
        f1 = v1.features
        f2 = v2.features
        for k in f1:
            if k in f2:
                nom += f1[k]*f2[k]
        return nom/(v1.size*v2.size)

morepunc = re.compile("(?P<punc>/|\.+|'|,|!|#|\$|%|\d+|&\S*|\(|\)|\*|\[|\]|-|\+|:|;|=|@|'|`|\")")

def tokenise(s, allowweirdchars=False):
    tokens = []
    for t in word_tokenize(morepunc.sub(" ", s)):
        try:
            t.encode("utf-8")
            tokens.append(t)
        except:
            print "T", t
            if not allowweirdchars:
                continue
            t = t.decode('ISO-8859-1')
            tokens.append(t)
    return tokens

class TESTSET:

    def __init__(self, cols, tweets, idf):
        self.cols = cols
        self.tweets = tweets
        self.idf = idf
        self.words = [w[0] for w in reversed(sortTable(idf))]
        self.makeIndex()

    def makeIndex(self):
        self.index = {}
        for tweet in self.tweets:
            for token in tweet.tokens:
                if not token in self.index:
                    self.index[token] = {}
                for col, score in zip(self.cols, tweet.GS):
                    if score == "1":
                        try:
                            self.index[token][col].append(tweet)
                        except:
                            self.index[token][col] = [tweet]

"""
Remove rubbish from tweets, remove tweets that are very similar to one another
"""

SPACE = re.compile(" +")
def splitEmojis(s0):
    s1 = ""
    for c in s0:
        if ord(c) > 256:
            s1 += " "+c+" "
        else:
            s1 += c
    return SPACE.sub(" ", s1)

EMOJIS = {}
EMOJICOUNT = 0

def isEmoji(t):
    return ord(t[0]) > 3000

def fixEmojis(tweet0):
    tweet1 = []
    global EMOJICOUNT
    global EMOJIS
    for t in tweet0:
        if len(t) > 0:
            if isEmoji(t):
                try:
                    t = EMOJIS[t]
                except:
                    EMOJIS[t] = "eMJ%s"%(EMOJICOUNT)
                    EMOJICOUNT += 1
                    t = EMOJIS[t]
            tweet1.append(t)
    return tweet1

def addBigrams(tokens0):
    last = False
    tokens1 = []
    for x in tokens0:
        tokens1.append(x)
        if last:
            tokens1.append("%s-%s"%(last, x))
        last = x
    return tokens1
            
def makeTFIDF(docs=ENGLISHTRAINING, threshold=0, N=False):
    global LANGUAGE
    LANGUAGE = languagePattern.match(docs).group("language")
    idf = {}
    cols = False
    tweets = []
    index = {}
    """
    just read them and add them to a list

    calculate the tf vector and accumulate the idf vector as you go
    """
    for tweet in codecs.open(docs, encoding="UTF-8").read().split("\n"):
        tweet = tweet.strip().replace("=", "").replace("\\n", " ")
        if LANGUAGE == "AR":
            tweet = SPACE.sub(" ", re.compile("_|#|\.+").sub(" ", a2bw.convert(tweet, a2bw.a2bwtable)))
        tweet = splitEmojis(tweet)
        if tweet == "":
            continue
        if not cols:
            cols = tweet.split()[2:]
            continue
        tweet = tweet.strip().split("\t")
        tweet, text, scores = tweet[0], tweet[1], tweet[2:]
        if not tweet == []:
            d = {}
            text = prefixes.sub("", text).strip()
            # tokens = [w for w in tokenise(prefixes.sub("", text).strip())]
            # tokens = [w[2:] if w.startswith("al") else w for w in text.split()]
            if LANGUAGE == "AR":
                tokens = stemmer.stemAll(text)
            else:
                tokens = [w for w in tokenise(prefixes.sub("", text.lower()).strip())]
            tokens = [token for token in fixEmojis(tokens) if not token == ""]
            for w in tokens:
                try:
                    d[w] += 1
                except:
                    d[w] = 1
                    """
                    If we only update the IDF here, then that means
                    we are only updating it the first time we see this term in this 
                    tweet, which is what we want
                    """
                    try:
                        idf[w] += 1
                    except:
                        idf[w] = 1
            tweets.append(TWEET(id=tweet, text=text, features=d, scores=scores, tokens=tokens))
    """
    remove singletons from the idf count
    """
    for w in idf.keys():
        if idf[w] == 1:
            del idf[w]
        else:
            idf[w] = 1.0/float(idf[w])
    """
    multiply by idf value, remove terms that aren't in the idfvector
    (since they were singletons) or that have very low scores as you go
    """
    for tweet in tweets:
        for w in tweet.features.keys():
            try:
                t = float(tweet.features[w])*idf[w]
                if t < threshold:
                    del tweet.features[w]
                else:
                    tweet.features[w] = t
            except:
                del tweet.features[w]
        """
        If we've set a maximum number of features/tweet, set things so
        that's how many we've got
        """
        if N and len(d.features) > N:
            bestN = set([x[0] for x in sortTable(d.features)][:N])
            for f in d.features.keys():
                if not f in bestN:
                    del d.features[f]
        else:
            bestN = False
    """
    re-prune the idf table. Not sure that that's actually going to do anything!
    """
    if threshold > 0:
        allgoodtf = set()
        for d in tweets:
            for f in d.features:
                allgoodtf.add(f)
        for f in idf.keys():
            if not f in allgoodtf:
                del idf[f]
    return TESTSET(cols, tweets, idf)

def tooSimilar(v1, v2):
    f1 = v1.tokens
    f2 = v2.tokens
    return f1 == f2 or dtw.array(f1, f2).findPath() == 2

def removeDuplicates(tweets0, printing=False):
    last = False
    """
    remove ones that are very similar
    
    (i) if we order them by their token lists, then ones that have
    similar token lists are *likely* to be adjacent. This is not
    guaranteed, so we may not remove all very similar tweets, but the
    downside of not doing it isn't enormous, and putting them in order
    makes it much easier to find similar ones.

    (ii) then look at adjacent ones. If they have identical or very
    similar (calculated by doing DTW) token lists then they are
    almost certainly retweets, in which case having them twice doesn't
    actually help me make up my mind about the significance of the
    terms they contain: I don't think that "love" is more positive if
    I see it in "@peter John loves Mary" and in "rt @martin @peter
    John loves Mary" than if I just see it in "John loves Mary"
    """
    tweets1 = []
    for dv in sorted(tweets0, key=lambda x: x.tokens):
        if last and tooSimilar(dv, last):
            if printing and not dv.tokens == last.tokens:
                print "merging \n'%s' and\n'%s\n"%(last.text, dv.text) 
                print dtw.array(last.tokens, dv.tokens).showAlignment()
            """
            keep the one with more features
            """
            if len(dv.features) > len(last.features):
                tweets1[-1] = dv
        else:
            tweets1.append(dv)
            last = dv
    return tweets1

def printFeatures(t):
    print ", ".join(["%s: %.3f"%(x[0], x[1]) for x in sortTable(t)])

def compare(r0, r1, t=0.001, idf=False):
    if idf:
        w2i, i2w = makeIndexes(idf)
    for i, (x0, x1) in enumerate(zip(r0, r1)):
        if abs(x1) > t:
            if idf:
                if abs(x0) < t:
                    star = "*"
                else:
                    star = ""
                print "%s%s, %s %.3f, %.3f"%(star, i, i2w[i], abs(x0), abs(x1))
            else:
                print i, x0, x1

def compareAll(l0, l1, tweets, idf, t=0.001):
    for r0, r1, tweet in zip(l0, l1, tweets):
        print tweet.text
        compare(r0, r1, t=t, idf=idf)
        
def makeSentiDict(testset, N=sys.maxint, printing=False):
    sdict = [{} for i in range(len(testset.cols))]
    for tweet in testset.tweets:
        if printing:
            print tweet.tokens
            print tweet.GS
        for w in tweet.tokens:
            for score, scorecard in zip(tweet.GS, sdict):
                s = 2 if w in INVEMOJIS else 1
                if score == '1':
                    try: 
                        scorecard[w] += s
                    except:
                        scorecard[w] = s
                    try: 
                        scorecard["%%%%%"] += s
                    except:
                        scorecard["%%%%%"] = s
        N -= 1
        if N == 0:
            break
    return SCOREDICT(scorelist=sdict)

def average(scores):
    t = sum(scores)
    for i, x in enumerate(scores):
        scores[i] = x/t
    return scores

def joinscores(scores):
    return "\t".join(["%.2f"%(s) for s in scores])

def getScores(word, sdict, printing=False, dicttype="FULL"):
    scores = []
    rawcount = []
    for d in sdict:
        try:
            scores.append(float(d[word])/float(d["%%%%%"]))
            rawcount.append(float(d[word]))
        except:
            rawcount.append(0.0)
            scores.append(0.0)
    scores = average(scores)
    if printing:
        print "rawcounts"
        print joinscores(rawcount)
        print "probability that a tweet that expresses sentiment I contains '%s'"%(word)
        print joinscores(scores)
    if dicttype == "TFIDF":
        return [word]+scores
    a = sum(scores)/len(scores)
    for i, x in enumerate(scores):
        scores[i] = x-a
    if printing:
        print "distance from the mean for each sentiment"
        print joinscores(scores)
    if dicttype == "DIST":
        return [word]+scores
    sd = sum(map(abs, scores))/len(scores)*1000
    for i, x in enumerate(scores):
        scores[i] = x*sd
    if printing:
        print "multiply that by standard deviation"
        print joinscores(scores)
    return [word]+scores

def scoredict2scorelist(scoredict):
    scorelist = [{} for x in scoredict.values()[0]]
    for w in scoredict:
        for i, v in enumerate(scoredict[w]):
            scorelist[i][w] = v
    return scorelist

def scorelist2scoredict(scorelist):
    scoredict = {}
    for col in scorelist:
        for w in col:
            try:
                scoredict[w].append(col[w])
            except:
                scoredict[w] = [col[w]]
    return scoredict

class SCOREDICT:

    def __init__(self, scorelist=False, scoredict=False, threshold=0.3):
        self.scorelist = scorelist
        self.scoredict = scoredict
        if scorelist and not scoredict:
            self.scoredict = scorelist2scoredict(scorelist)
        if scoredict and not scorelist:
            self.scorelist = scoredict2scorelist(scoredict)
        self.threshold = threshold
        self.info = """
You make a scoredict out of a sentidict by doing some sums (whatever
sums you fancy) on the sentidict, which contains raw counts, and then
storing them as a dictionary of lists and a list of dictionaries

This is what you use for actually classifying a test set
"""

    def show(self, out=sys.stdout):
        with safeout(out) as write:
            for w in self.scoredict:
                write("%s\t%s\n"%(w, joinscores(self.scoredict[w])))
            
def makeScoreDict(training, sentidict, N=sys.maxint, dicttype="FULL"):
    words = [x[0] for x in reversed(sortTable(training.idf))][:N]
    scores = []
    scoredict = {}
    for word in words:
        try:
            scores.append(getScores(word, sentidict.scorelist, dicttype=dicttype))
            scoredict[word] = scores[-1][1:]
        except:
            pass
    return SCOREDICT(scoredict=scoredict)

"""
For some emotions the top scoring words actually score lower than they
do for others where they are not at the top. Consider "joy" vs
"love". Here's the top of the table when ordered by the highest scores
for "joy" and when ordered by the highest scores for "love":

            joy	    love
hearty	    16.21	25.86
rejoice	    14.71	15.19
birthday	12.83	51.83
cheerful	11.75	25.82
joy	        11.08	19.94
hilarious	10.58	9.48
laughter	10.13	19.55

	        joy	    love
birthday	12.83	51.83
love	    4.12	31.9
hearty	    16.21	25.86
cheerful	11.75	25.82
smiling	    9.77	25.19
smile	    7.36	22.24

The top few items for each contain some of the same things. Not too
surprising. They are ordered differently. Also not too
surprising. What is problematic is that the top items for "joy"
actually have higher scores for "love", e.g. love[hearty] = 25.86,
joy[hearty] = 16.21, despite hearty being the top item for "joy" and
the third item for "love"

This is problematic, because it means, pretty much, that *nothing*
will ever be assigned to "joy" without also being assigned to "love".

So we would like to find a way of reweighting things. One idea is
based on the observation that overall things get higher scores for
"love" than they do for "joy". That probably arises because of some
step in all the normalisations that I'm already doing, so ideally we
would fix it as it arises, but the idea here is to post-compensate for
it. There's more "mass" associated with "love" than with "joy": if we
fnd out how much mass each has and use that to (yet again) normalise
the weights then maybe that will fix it.

How to do that?

Collect all the positive scores that any word assigns to each emotion:
use that as a normalisation factor. Simple idea: implementation below
is too clever and hence is hard to follow.

allscores is a list of the form

[['the', -0.0028690608063188915, 0.017916775906057537, ...], 
['i', -0.03950372185301048, -0.008469566833805993, , ...], 
['to', 0.0021885805294468226, 0.0623218468960338, ...], 
['a', -0.008758094314166196, 0.02272586185456654, ...], 
['and', -0.012856867157346975, -0.11302221253628077, ...]]

So we can find the total mass of column i by adding together all the i'th elements of entries in this list: that's what colTotal does.

We do that for each column: that gives us a list of masses: that's
totals. Then all we really want to do is divide each word's score
for a sentiment by the weight for that sentiment. That gives us pretty
large numbers, so we before we do that we normalise totals back down
using totalOfTotals as a weight. We don't need to: we could use any
constant, we could just decide not to bother. Wouldn't make any
difference to anything, but doing it this way gives us
sensible-looking numbers (the numbers *are* sensible without it, they
just print nicely when we are looking at spreadsheets and the
like). And then we use this to change the weights.

This works a bit, but it's not great. I've tried doing some
more-or-less random weightings, but they don't help either so I
haven't included them here -- they don't help and they just make the
code even more unreadable. 

One alternative would be to use the ranking
of the term in its emotion as its weight -- that because "hearty" is
the top term for "joy" then it should score 1.0 for joy, and because
it's the third term for "love" is should score 1/3 (so the i'th item scores 1/i), or (500-3)/500 (the i'th item scores (N-i)/N), or
or 1/log(i+1) (only works for positive numbers, but I don't mind
that). That way at least the thing that was most positive for
sentiment[i] would contribute more for sentiment[i] than it would for
sentiment[j], even if it's actual score for j was higher than for
i. I quite fancy 1/log(i+1) -- it's smooth and it's order-preserving.

I'm sure there are others ...
"""

def colTotal(i, scorelist):
    """
    we can find the total mass of column i by adding together all the
    i'th elements of entries in this list
    """
    return sum(s for s in scorelist[i].values() if s > 0)

def balance(scorelist):
    if not isinstance(scorelist, list):
        return SCOREDICT(scorelist=balance(scorelist.scorelist))
    """
    We do that for each column: that gives us a list of masses
    """
    totals = [colTotal(i, scorelist) for i in range(len(scorelist))]
    """
    we normalise totals back down using totalOfTotals as a weight
    """
    totalOfTotals = sum(totals)
    for i, t in enumerate(totals):
        totals[i] = t*len(totals)/totalOfTotals
    balanced = [{} for t in totals]
    """
    all we really want to do is divide each word's score for a
    sentiment by the weight for that sentiment
    """
    for i, col in enumerate(scorelist):
        for w in col:
            balanced[i][w] = col[w]/totals[i]
    return balanced

def argmax(l):
    bestScore = -sys.maxint
    for x in l:
        y = l[x]
        if y > bestScore:
            bestScore = y
            best = x
    return best

def argmin(l):
    bestScore = sys.maxint
    for x in l:
        y = l[x]
        if y < bestScore:
            bestScore = y
            best = x
    return best
    
def ranktable(rankdict):
    table = {x[0]:1.0/(i+2) for i, x in enumerate(sortTable(rankdict))}
    m = min(table.values())
    for x in table:
        table[x] -= m
        table[x] *= 100
    return table
    
def rank(scoredict):
    rankdicts = [{} for i in scoredict.values()[0]]
    for w in scoredict:
        for i, x in enumerate(scoredict[w]):
            rankdicts[i][w] = scoredict[w][i]
    return [ranktable(t) for t in rankdicts]
        
def showAllScores(allscores, out=sys.stdout):
    with safeout(out) as write:
        write("\tanger	anticipation	disgust	fear	joy	love	optimism	pessimism	sadness	surprise	trust\n")
        for r in allscores:
            print r
            write("%s\t%s\n"%(r[0], joinscores(r[1:])))

def scoreTweet(tweet, sentidict, threshold=0.5):
    if not isinstance(sentidict, dict):
        sentidict = sentidict.scoredict
    sentiments = [0 for x in tweet.GS]
    scores = [0 for x in tweet.GS]
    best = [(0, " ") for x in tweet.GS]
    worst = [(sys.maxint, " ") for x in tweet.GS]
    for word in tweet.tokens:
        try:
            for i, s in enumerate(sentidict[word]):
                sentiments[i] += s
                if s > best[i][0]:
                    best[i] = (s, word)
                if s < worst[i][0]:
                    worst[i] = (s, word)
        except:
            pass
    if threshold:
        m = max(sentiments)
        if m > 0:
            for i, x in enumerate(sentiments):
                scores[i] = x/m
                try:
                    lt = threshold[i]
                except:
                    lt = threshold
                if x/m < lt:
                    sentiments[i] = 0
                else:
                    sentiments[i] = 1
    return sentiments, scores, best, worst

def prfj(right, wrong, missing):
    try:
        right = float(right)
        p = right/(right+wrong)
        r = right/(right+missing)
        f = 2*p*r/(p+r)
        return (p, r, f, right/(right+wrong+missing))
    except:
        return (0, 0, 0, 0)

M11 = 0
M10 = 1 # wrong
M01 = 2 # missing
M00 = 3

def convertible(w):
    if LANGUAGE == "AR" and ord(w[0]) < 256:
        return a2bw.convert(w, a2bw.bw2atable)
    else:
        return w

def scoreTweets(testset, sentidict, out=False, threshold=null, singleColumn=None):
    if threshold == null:
        threshold = sentidict.threshold
    J = [[0]*len(testset.cols) for i in range(4)]
    lines = []
    worderrors = [{} for x in testset.cols]
    for I, tweet in enumerate(testset.tweets):
        cols = testset.cols
        sentiments, scores, best, worst = scoreTweet(tweet, sentidict, threshold=threshold)
        for n, (col, sentiment, score, gs) in enumerate(zip(cols, sentiments, scores, map(int, tweet.GS))):
            if not singleColumn == None and not n == singleColumn:
                continue
            if sentiment == 1:
                if gs == 1:
                    J[M11][n] += 1
                    for token in tweet.tokens:
                        try:
                            worderrors[n][token] += 1
                        except:
                            worderrors[n][token] = 1
                    sentiments[n] = "%s:%.2f:\t%s"%(col, score, "GREEN")
                else:
                    J[M10][n] += 1
                    for token in tweet.tokens:
                        try:
                            worderrors[n][token] -= 1
                        except:
                            worderrors[n][token] = -1
                    sentiments[n] = "%s:%.2f\t%s"%(col, score, "RED")
            else:
                if gs == 1:
                    J[M01][n] += 1
                    sentiments[n] = "%s:%.2f\t%s"%(col, score, "BLUE")
                else:
                    J[M00][n] += 1
            tokens = " ".join(tweet.tokens)
            if LANGUAGE == "AR":
                tokens = a2bw.convert(tokens, a2bw.bw2atable)
        if singleColumn == None:
            sentiments.append(tokens)
        try:
            if singleColumn == None:
                lines.append(sentiments)
                lines.append(["%s:%.2f"%(convertible(b[1]), b[0]) for b in best])
                lines.append(["%s:%.2f"%(convertible(w[1]), w[0]) for w in worst])
                lines.append([""]*len(best))
        except Exception as e:
            print "Couldn't convert %s (tweet %s)"%(tweet.text, I)
            print "BEST", best
            print "WORST", worst
            raise(e)
    # print "\t".join(["%.2f"%(prfj(r, w, m)[-1]) for r, w, m in zip(J[M11], J[M10], J[M01])])
    if out:
        toXLSX(lines, xlsxfile="%s.xlsx"%(out))
        writecsv(lines, out=codecs.open("%s.csv"%(out), encoding="UTF-8", mode="w"))
    score = prfj(float(sum(J[M11])), float(sum(J[M10])), float(sum(J[M01])))
    return score+(worderrors, lines)

def selfcorrect(training, scoredict, N=1, threshold=0.3):
    removed = 0
    for i in range(N):
        (p, r, f, j, worderrors, lines) = scoreTweets(training, scoredict, out=False, threshold=threshold)
        for sd, wd in zip(scoredict.scorelist, worderrors):
            for w in wd:
                """
                Remove a stupid word if it thought it was being helpful
                """
                if wd[w] < 0 and w in sd and sd[w] > 0:
                    sd[w] = 0
                    removed += 1
        scoredict = SCOREDICT(scorelist=scoredict.scorelist)
    print "  removed %s words"%(removed)
    return scoredict

def setThresholds(training, scoredict):
    return [plot(training, scoredict, singleColumn=i, printing=False) for i in range(len(training.cols))]

"""
tuning involves getting rid of words that have led to bad decisions
and then finding the best per-column thresholds. The first bit in turn
depends on the threshold which was set for using the initial
classifier, so you have to optimise for that as well.
"""
def tune(training, scoredict, threshold=0.15, N=3):
    scoredict.threshold = threshold
    print "tune %.1f"%(threshold)
    for i in range(N):
        print "  selfcorrect, round %s"%(i)
        scoredict = selfcorrect(training, scoredict, threshold=scoredict.threshold)
        print "  setThresholds, round %s"%(i)
        scoredict.threshold = setThresholds(training, scoredict)
    return scoredict

def createAndTune(training, test, sentidict, threshold=0.15, N1=2500, N2=3):
    k = makeScoreDict(training, sentidict, N=N1)
    k = tune(training, k, threshold=threshold, N=N2)
    p, r, f, j, errors, lines = scoreTweets(test, k)
    print "T %.2f, P %.3f, R %.3f, Jaccard %.3f F0 %.3f"%(threshold, p, r, j, f)
    return k

def createAndTuneRange(training, test, t=1, end=0, step=0.1, N1=2500, N2=3):
    classifiers = []
    global INVEMOJIS
    INVEMOJIS = {EMOJIS[x]:x for x in EMOJIS}
    sentidict = makeSentiDict(training)
    print "Start training"
    while t >= end:
        classifiers.append(createAndTune(training, test, sentidict, threshold=t, N1=N1, N2=N2))
        t -= step
    return classifiers

def plot(testset, scoredict, threshold=1.0, end=0, step=0.1, singleColumn=None, printing=True):
    if not singleColumn == None:
        print "    setting threshold for %s"%(testset.cols[singleColumn])
    m = []
    while threshold > end:
        (p, r, f, j, w, l) = scoreTweets(testset, scoredict, threshold=threshold, out=False, singleColumn=singleColumn)
        m.append((threshold, p, r, f, j))
        if printing:
            print "%.1f\t%.2f\t%.2f\t%.3f\t%.3f"%(m[-1])
        threshold -= step
    lastT = 1.0
    bestJ = 0
    bestJt = 1.0
    allJ = []
    sweetspot = False
    for threshold, p, r, f, j in m:
        if j > bestJ:
            bestJ = j
            bestJt = threshold
        allJ.append((j, threshold))
        if not sweetspot and r > p:
            sweetspot = threshold+(lastT-threshold)/2.0
        lastT = threshold
    m.append((sweetspot,)+scoreTweets(testset, scoredict, threshold=sweetspot, out=False)[:-1])
    if printing:
        print "--------------------------"
        print "%.1f\t%.2f\t%.2f\t%.3f\t%.3f"%(m[-1])
        print "bestJ %.2f %.3f"%(bestJt, bestJ)
    if not singleColumn == None:
        return bestJt

def export(d, training=False, out=sys.stdout):
    try:
        d = d.scoredict
    except:
        pass
    with safeout(out) as write:
        try:
            write("\t".join([""]+training.cols)+"\n")
        except:
            pass
        for w in sorted(d.keys()):
            try:
                k = INVEMOJIS[w]
            except:
                if LANGUAGE == "AR":
                    k = a2bw.convert(w, a2bw.bw2atable)
                else:
                    k = w
            write("\t".join([k]+["%.3f"%(s) for s in d[w]])+"\n")
    
"""
bunch of stuff for doing LSA. I haven't made it pay off, but it is a correct implementation
so we can use it if we can find data that it does any good for
"""
def getMatches(v, vv):
    m = []
    for x in vv:
        if not x == v:
            m.append((x.cos(v), x))
    m.sort()
    m.reverse()
    return m

def makeIndexes(words):
    w2i = {}
    i2w = {}
    for i, w in enumerate(words):
        w2i[w] = i
        i2w[i] = w
    return w2i, i2w

def tfidf2array((tweets, idf)):
    w2i, i2w = makeIndexes(idf)
    a = numpy.zeros((len(tweets), len(idf)))
    for i, t in enumerate(tweets):
        features = t.features
        for f in features:
            a[i][w2i[f]] = features[f]
    return a

def svd((tweets, idf), N=sys.maxint):
    print tweets.__class__
    u, s0, v = numpy.linalg.svd(tfidf2array((tweets, idf))[:N])
    s1 = numpy.zeros((u.shape[0], v.shape[0]))
    s1[:s0.shape[0], :s0.shape[0]] = numpy.diag(s0)
    return u, s1, v

def prune(s0, t=0.0, N=sys.maxint):
    s1 = numpy.zeros(s0.shape)
    for i in range(min(s1.shape)):
        if s0[i][i] > t and i < N:
            s1[i][i] = s0[i][i]
    return s1

def dotdot((u, s, v)):
    return dot(u, dot(s, v))

def reconstruct(usv, (tfidf, idf), t=0.01):
    w2i, i2w = makeIndexes(idf)
    r = dotdot(usv)
    m = {}
    for i, t in enumerate(tfidf):
        m[t] = {}
        for j, x in enumerate(r[i]):
            if x > t:
                m[t][i2w[j]] = x
    return m
