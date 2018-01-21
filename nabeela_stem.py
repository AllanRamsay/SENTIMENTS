from LSA.stemmer import stemAll
import LSA.a2bw

def stem(text, UTF8=False):
    text = [x.split(":") for x in stemAll(text)]
    stems = " ".join(x[0] for x in text if x[1] in "NV")
    if UTF8:
        return LSA.a2bw.convert(stems, LSA.a2bw.bw2atable)
    else:
        return stems
