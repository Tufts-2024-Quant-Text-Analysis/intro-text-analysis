from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText
from MyCapytain.common.constants import Mimetypes
from lxml import etree

import pandas as pd
import spacy

# enable copy-on-write so that we can turn a slice into a new DataFrame
pd.options.mode.copy_on_write = True

class TextStats:

    def __init__(self, filepath: str, urn: str, *args, **kwargs):
        with open(filepath) as f:
            text = CapitainsCtsText(urn=urn, resource=f)

        data = self.prepare_data(text)

        self.df = pd.DataFrame(data, *args, **kwargs)
        self.lang = urn.split("-")[-1][0:-1]

        self.tokenize_df(self.lang)

    def tokenize_df(self, lang: str = 'grc'):
        model = "grc_proiel_sm" if lang == "grc" else "en_core_web_sm"

        nlp = spacy.load(model, disable=["ner"])

        self.df["tokens"] = self.df["unannotated_strings"].apply(nlp.tokenizer)

        raw_texts = [t for t in self.df["unannotated_strings"]]
        annotated_texts = nlp.pipe(raw_texts, batch_size=100)

        self.df["nlp_docs"] = list(annotated_texts)

    def prepare_data(self, text):
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


def load_pausanias(lang: str = "grc"):
    return TextStats(
        filepath=f"../tei/tlg0525.tlg001.perseus-{lang}2.xml",
        urn=f"urn:cts:greekLit:tlg0525.tlg001.perseus-{lang}2",
    )


def get_book(df: pd.DataFrame, n: int | str):
    return df[df["refs"].str.startswith(f"{n}")]


def tokenize(df: pd.DataFrame, lang: str = "grc"):
    model = "grc_proiel_sm" if lang == "grc" else "en_core_web_sm"

    nlp = spacy.load(model, disable=["ner"])

    df["tokens"] = df["unannotated_strings"].apply(nlp.tokenizer)

    raw_texts = [t for t in df["unannotated_strings"]]
    annotated_texts = nlp.pipe(raw_texts, batch_size=100)

    df["nlp_docs"] = list(annotated_texts)

    return df
