"""
OWL Ontology for Ancient Sri Lanka (Anuradhapura Period)
Uses RDFLib to represent concepts and relationships
"""

from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef

# Define namespaces
SL = Namespace("http://sinhalascore.ai/ontology/anuradhapura#")
DC = Namespace("http://purl.org/dc/elements/1.1/")

def build_ontology() -> Graph:
    g = Graph()
    g.bind("sl", SL)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)

    # ---- Classes ----
    classes = [
        ("King", "රජකු - Ancient Sri Lankan monarch"),
        ("Reservoir", "ජලාශය - Water storage structure"),
        ("Stupa", "ස්තූපය - Buddhist monument"),
        ("Period", "යුගය - Historical time period"),
        ("Religion", "ආගම - Religious tradition"),
        ("WaterSystem", "ජල ව්‍යාපෘතිය - Irrigation/water management"),
        ("Dynasty", "රාජ වංශය - Royal lineage"),
        ("Monument", "ස්මාරකය - Historical monument"),
        ("TradeRoute", "වෙළඳ මාර්ගය - Trade connection"),
        ("Army", "හේවාය - Military force"),
        ("Temple", "විහාරය - Buddhist temple"),
    ]
    for cls_name, label in classes:
        cls_uri = SL[cls_name]
        g.add((cls_uri, RDF.type, OWL.Class))
        g.add((cls_uri, RDFS.label, Literal(label, lang="en")))

    # ---- Properties ----
    props = [
        ("builtBy", "ඉදිකළේ", "King", "Monument"),
        ("ruledDuring", "ශාසනය කළේ", "King", "Period"),
        ("hasCapital", "රාජධානිය", "Dynasty", "Monument"),
        ("isPartOf", "කොටසකි", "WaterSystem", "WaterSystem"),
        ("tradedWith", "වෙළඳ කළේ", "King", "TradeRoute"),
        ("patronized", "ආරාධනා කළේ", "King", "Religion"),
        ("defeated", "පරාජය කළේ", "King", "King"),
    ]
    for prop_name, label, domain, range_ in props:
        prop_uri = SL[prop_name]
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.label, Literal(label)))
        g.add((prop_uri, RDFS.domain, SL[domain]))
        g.add((prop_uri, RDFS.range, SL[range_]))

    # ---- Individual Kings ----
    kings = [
        ("Devanampiyatissa", "දේවානම්පියතිස්ස", "ක්‍රි.පූ. 247-207"),
        ("Dutugamunu", "දුටුගැමුණු", "ක්‍රි.පූ. 161-137"),
        ("Valagamba", "වළගම්බා", "ක්‍රි.පූ. 89-77"),
        ("Mahasena", "මහසෙන්", "ක්‍රි.ව. 274-301"),
        ("Vasabha", "වසබ", "ක්‍රි.ව. 67-111"),
        ("Dhatusena", "ධාතුසේන", "ක්‍රි.ව. 459-477"),
        ("Elara", "ඇළාර", "ක්‍රි.පූ. 205-161"),
    ]
    for king_id, sinhala_name, period in kings:
        king_uri = SL[king_id]
        g.add((king_uri, RDF.type, SL.King))
        g.add((king_uri, RDFS.label, Literal(sinhala_name, lang="si")))
        g.add((king_uri, SL.period, Literal(period)))

    # ---- Individual Reservoirs ----
    reservoirs = [
        ("KalaWewa", "කළාවැව", "Vasabha"),
        ("NuwaraWewa", "නුවරවැව", "Vasabha"),
        ("JayaGanga", "ජයගංගා", "Dhatusena"),
        ("MinipeCanel", "මිනිපේ ඇළ", "Dhatusena"),
        ("ParakramaVapi", "පරාක්‍රම සමුද්‍රය", "Parakramabahu"),
    ]
    for res_id, label, builder_id in reservoirs:
        res_uri = SL[res_id]
        g.add((res_uri, RDF.type, SL.Reservoir))
        g.add((res_uri, RDFS.label, Literal(label, lang="si")))
        g.add((res_uri, SL.builtBy, SL[builder_id]))

    # ---- Individual Stupas ----
    stupas = [
        ("Thuparama", "ථූපාරාම", "Devanampiyatissa"),
        ("RuwanweliseyaStupa", "රුවන්වැලිසෑය", "Dutugamunu"),
        ("JetavanaStupa", "ජේතවනාරාම සෑය", "Mahasena"),
        ("AbhayagiriStupa", "අභයගිරි සෑය", "Valagamba"),
        ("MirisavatiStupa", "මිරිසවැටිය", "Dutugamunu"),
    ]
    for stupa_id, label, builder_id in stupas:
        stupa_uri = SL[stupa_id]
        g.add((stupa_uri, RDF.type, SL.Stupa))
        g.add((stupa_uri, RDFS.label, Literal(label, lang="si")))
        g.add((stupa_uri, SL.builtBy, SL[builder_id]))

    # ---- Key relationships ----
    g.add((SL.Dutugamunu, SL.defeated, SL.Elara))
    g.add((SL.Valagamba, SL.patronized, SL.Buddhism))
    g.add((SL.Devanampiyatissa, SL.patronized, SL.Buddhism))
    g.add((SL.Mahasena, SL.builtBy, SL.JetavanaStupa))

    return g


def get_ontology_concepts_for_answer(answer_text: str) -> list[dict]:
    """
    Check which ontology concepts appear in the student's answer.
    Returns matched concepts with their relationships.
    """
    g = build_ontology()

    # Map of Sinhala keywords to ontology URIs
    concept_map = {
        "දේවානම්පියතිස්ස": SL.Devanampiyatissa,
        "දුටුගැමුණු": SL.Dutugamunu,
        "වළගම්බා": SL.Valagamba,
        "මහසෙන්": SL.Mahasena,
        "වසබ": SL.Vasabha,
        "ධාතුසේන": SL.Dhatusena,
        "ඇළාර": SL.Elara,
        "කළාවැව": SL.KalaWewa,
        "නුවරවැව": SL.NuwaraWewa,
        "ජයගංගා": SL.JayaGanga,
        "ථූපාරාම": SL.Thuparama,
        "රුවන්වැලිසෑය": SL.RuwanweliseyaStupa,
        "ජේතවනාරාම": SL.JetavanaStupa,
        "අභයගිරි": SL.AbhayagiriStupa,
        "මිරිසවැටිය": SL.MirisavatiStupa,
    }

    matched = []
    for keyword, uri in concept_map.items():
        if keyword in answer_text:
            label = g.value(uri, RDFS.label, default=keyword)
            rdf_type = g.value(uri, RDF.type)
            type_label = str(rdf_type).split("#")[-1] if rdf_type else "Concept"
            matched.append({
                "keyword": keyword,
                "uri": str(uri),
                "type": type_label,
                "label": str(label)
            })

    return matched


def get_related_concepts(concept_keyword: str) -> list[str]:
    """Get concepts related to a given keyword from the ontology."""
    g = build_ontology()
    related = []
    for s, p, o in g:
        s_label = g.value(s, RDFS.label, default=str(s))
        o_label = g.value(o, RDFS.label, default=str(o)) if isinstance(o, URIRef) else str(o)
        if concept_keyword in str(s_label) or concept_keyword in str(o_label):
            p_label = str(p).split("#")[-1]
            related.append(f"{s_label} --[{p_label}]--> {o_label}")
    return related[:10]


if __name__ == "__main__":
    g = build_ontology()
    print(f"Ontology built with {len(g)} triples")
    # Test
    matched = get_ontology_concepts_for_answer("දුටුගැමුණු රජ රුවන්වැලිසෑය ඉදිකළේය")
    print("Matched concepts:", matched)
