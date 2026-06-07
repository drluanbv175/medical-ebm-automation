"""Test trích nguyên văn từ abstract: chỉ trích, không bịa; mỗi câu 1 nhóm."""
from app.services.extraction import extract_clinical_points, ordered_categories

ABS = ("This trial enrolled 6609 patients with chronic kidney disease. "
       "Empagliflozin reduced the risk of the primary outcome (hazard ratio 0.72; "
       "95% CI 0.64 to 0.82; p<0.001). "
       "The risk of bleeding was higher with the adverse event of hypoglycemia. "
       "Dose adjustment is recommended in severe hepatic impairment.")


def test_extracts_categories():
    pts = extract_clinical_points(ABS)
    assert "doi_tuong" in pts and "6609 patients" in pts["doi_tuong"][0]
    assert "ket_qua" in pts and "hazard ratio" in pts["ket_qua"][0].lower()
    assert "khuyen_cao" in pts  # 'recommended'
    assert "an_toan" in pts     # 'adverse event'/'bleeding'


def test_quotes_are_verbatim_from_source():
    # Mọi câu trích PHẢI là chuỗi con của abstract gốc (không bịa/không diễn giải).
    pts = extract_clinical_points(ABS)
    for cat in pts:
        for sentence in pts[cat]:
            assert sentence in ABS, f"Câu trích không khớp nguồn: {sentence}"


def test_each_sentence_one_category():
    pts = extract_clinical_points(ABS)
    seen = []
    for cat in ordered_categories():
        for s in pts.get(cat, []):
            assert s not in seen, "Một câu bị lặp ở nhiều nhóm"
            seen.append(s)


def test_empty_abstract_returns_empty():
    assert extract_clinical_points("") == {}
    assert extract_clinical_points(None) == {}


def test_conclusion_from_structured_abstract():
    from app.services.extraction import extract_conclusion
    a = ("Background:\nDrug X was studied.\n\nResults:\nASAS20 51.2% vs 48.8%.\n\n"
         "Conclusion:\nMK2 inhibition was insufficient to provide clinical benefit in AS.")
    concl = extract_conclusion(a)
    assert concl and "insufficient" in concl[0].lower()
    import re
    norm = re.sub(r"\s+", " ", a)
    for s in concl:
        assert re.sub(r"\s+", " ", s) in norm  # nguyên văn (không bịa)


def test_conclusion_from_cue_sentence():
    from app.services.extraction import extract_conclusion
    a = ("This trial enrolled 600 patients. We conclude that early therapy "
         "reduces hospitalization and should be considered in high-risk patients.")
    concl = extract_conclusion(a)
    assert concl and "we conclude" in concl[0].lower()


def test_conclusion_empty():
    from app.services.extraction import extract_conclusion
    assert extract_conclusion("") == []
    assert extract_conclusion(None) == []


def test_pico_extraction():
    from app.services.extraction import extract_pico
    a = ("This trial enrolled 6609 patients with chronic kidney disease. "
         "Patients were randomized to empagliflozin 10 mg daily or placebo. "
         "Compared with placebo, empagliflozin reduced the risk of the primary outcome "
         "(hazard ratio 0.72; 95% CI 0.64 to 0.82; p<0.001).")
    pico = extract_pico(a)
    assert "P" in pico and "6609 patients" in pico["P"][0]
    assert "I" in pico and "empagliflozin" in pico["I"][0]
    assert "O" in pico
    # Mọi câu PICO phải là nguyên văn từ nguồn (không bịa)
    for cat in pico:
        for s in pico[cat]:
            assert s in a
