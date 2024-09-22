def load_pausanias(lang: str = 'grc'):
    from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText
    from MyCapytain.common.constants import Mimetypes
    from lxml import etree

    import pandas as pd

    with open(f"../tei/tlg0525.tlg001.perseus-{lang}2.xml") as f:
        text = CapitainsCtsText(urn=f"urn:cts:greekLit:tlg0525.tlg001.perseus-{lang}2", resource=f)

    urns = []
    raw_xmls = []
    unannotated_strings = []

    for ref in text.getReffs(level=len(text.citation)):
        urn = f"{text.urn}:{ref}"
        node = text.getTextualNode(ref)
        raw_xml = node.export(Mimetypes.XML.TEI)
        tree = node.export(Mimetypes.PYTHON.ETREE)
        s = etree.tostring(tree, encoding="unicode", method="text")

        urns.append(urn)
        raw_xmls.append(raw_xml)
        unannotated_strings.append(s)


    d = {
        "urn": pd.Series(urns, dtype="string"),
        "raw_xml": raw_xmls,
        "unannotated_strings": pd.Series(unannotated_strings, dtype="string")
    }
    pausanias_df = pd.DataFrame(d)
    
    return tokenize(pausanias_df, lang)

def tokenize(df, lang: str = 'grc'):
    import spacy

    model = "grc_proiel_sm" if lang == 'grc' else "en_core_web_sm"

    nlp = spacy.load(model, disable=["ner"])

    df['tokens'] = df['unannotated_strings'].apply(nlp.tokenizer)

    raw_texts = [t for t in df['unannotated_strings']]
    annotated_texts = nlp.pipe(raw_texts, batch_size=100)

    df['nlp_docs'] = list(annotated_texts)

    return df
