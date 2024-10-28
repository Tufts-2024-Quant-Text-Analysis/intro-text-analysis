from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText
from MyCapytain.common.constants import Mimetypes
from lxml import etree
from pathlib import Path

import pandas as pd
import spacy

# enable copy-on-write so that we can turn a slice into a new DataFrame
pd.options.mode.copy_on_write = True


def count_grc_dependency_collocations(x, w1, w2):
    w2_is_child_of_w1 = len(
        [t for t in x if t.lemma_ == w1 and w2 in [tt.lemma_ for tt in t.children]]
    )

    return w2_is_child_of_w1


def count_ngram_collocations(x, w1, w2, l_size: int = 1, r_size: int = 1):
    lemmata = [t.lemma_ for t in x]

    # NB: There is currently a bug in this code
    # the right-hand side of a slice in Python is exclusive, so we add 1 to make sure
    # we're actually getting one element to the right
    chunked_lemmata = [
        lemmata[i - l_size : i + r_size + 1] for i in range(0, len(lemmata))
    ]

    cooccurrences = [1 for l in chunked_lemmata if w1 in l and w2 in l]

    return sum(cooccurrences)


def load_pausanias(lang: str = "grc"):
    urn = f"urn:cts:greekLit:tlg0525.tlg001.perseus-{lang}2"
    file = Path(f"../tei/tlg0525.tlg001.perseus-{lang}2.pickle")

    df = None
    if file.exists():
        df = pd.read_pickle(file)
    else:
        data = prepare_data(f"../tei/tlg0525.tlg001.perseus-{lang}2.xml", urn)

        df = pd.DataFrame(data)

        df.to_pickle(file)

    return tokenize(df, lang)


def load_iliad():
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-eng3"
    file = Path("../tei/tlg0012.tlg001.perseus-eng3.pickle")

    df = None
    if file.exists():
        df = pd.read_pickle(file)
    else:
        data = prepare_data("../tei/tlg0012.tlg001.perseus-eng3.xml", urn)
        df = pd.DataFrame(data)
        df.to_pickle(file)
    
    return tokenize(df, "eng")

def get_book(df: pd.DataFrame, n: int | str):
    return df[df["refs"].str.startswith(f"{n}")]


def prepare_data(filepath, urn):
    with open(filepath) as f:
        text = CapitainsCtsText(urn=urn, resource=f)

    refs = []
    urns = []
    raw_xmls = []
    unannotated_strings = []

    for ref in text.getReffs(level=len(text.citation)):
        urn = f"{text.urn}:{ref}"
        node = text.getTextualNode(ref)
        raw_xml = node.export(Mimetypes.XML.TEI)
        tree = node.export(Mimetypes.PYTHON.ETREE)
        s = etree.tostring(tree, encoding="unicode", method="text")

        refs.append(ref[0])
        urns.append(urn)
        raw_xmls.append(raw_xml)
        unannotated_strings.append(s)

    return {
        "refs": refs,
        "urn": pd.Series(urns, dtype="string"),
        "raw_xml": raw_xmls,
        "unannotated_strings": pd.Series(unannotated_strings, dtype="string"),
    }


def tokenize(df: pd.DataFrame, lang: str = "grc"):
    model = "grc_proiel_trf" if lang == "grc" else "en_core_web_sm"

    nlp = spacy.load(model, disable=["ner"])

    df["tokens"] = df["unannotated_strings"].apply(nlp.tokenizer)

    raw_texts = [t for t in df["unannotated_strings"]]
    annotated_texts = nlp.pipe(raw_texts, batch_size=100)

    df["nlp_docs"] = list(annotated_texts)

    return df
