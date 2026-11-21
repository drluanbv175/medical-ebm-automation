"""Nguyên văn mục STROBE 2007 và RECORD 2015.

SINH TỰ ĐỘNG bởi tools/sinh_chuan_bao_cao_items.py — KHÔNG sửa tay.

Nguồn (CC BY): STROBE E&E PLoS Med 2007;4(10):e297 (PMID 17941715; PMC2020496) · RECORD PLoS Med 2015;12(10):
e1001885 (PMID 26440803; PMC4595218). Lấy qua Europe PMC fullTextXML ngày 21/11/2026.
"""

# (mã, thiết kế: chung|cat_ngang|thuan_tap|benh_chung, chủ đề, nguyên văn)
STROBE_2007_ITEMS = (
    ('1a', 'chung', 'Title and abstract', "Indicate the study's design with a commonly used term in the title or the abstract."),
    ('1b', 'chung', 'Title and abstract', 'Provide in the abstract an informative and balanced summary of what was done and what was found.'),
    ('2', 'chung', 'Background/rationale', 'Explain the scientific background and rationale for the investigation being reported.'),
    ('3', 'chung', 'Objectives', 'State specific objectives, including any prespecified hypotheses.'),
    ('4', 'chung', 'Study design', 'Present key elements of study design early in the paper.'),
    ('5', 'chung', 'Setting', 'Describe the setting, locations, and relevant dates, including periods of recruitment, exposure, follow-up, and data collection.'),
    ('6a', 'thuan_tap', 'Participants', 'Give the eligibility criteria, and the sources and methods of selection of participants. Describe methods of follow-up.'),
    ('6a', 'benh_chung', 'Participants', 'Give the eligibility criteria, and the sources and methods of case ascertainment and control selection. Give the rationale for the choice of cases and controls.'),
    ('6a', 'cat_ngang', 'Participants', 'Give the eligibility criteria, and the sources and methods of selection of participants.'),
    ('6b', 'thuan_tap', 'Participants', 'For matched studies, give matching criteria and number of exposed and unexposed.'),
    ('6b', 'benh_chung', 'Participants', 'For matched studies, give matching criteria and the number of controls per case.'),
    ('7', 'chung', 'Variables', 'Clearly define all outcomes, exposures, predictors, potential confounders, and effect modifiers. Give diagnostic criteria, if applicable.'),
    ('8', 'chung', 'Data sources/measurement', 'For each variable of interest give sources of data and details of methods of assessment (measurement). Describe comparability of assessment methods if there is more than one group.'),
    ('9', 'chung', 'Bias', 'Describe any efforts to address potential sources of bias.'),
    ('10', 'chung', 'Study size', 'Explain how the study size was arrived at.'),
    ('11', 'chung', 'Quantitative variables', 'Explain how quantitative variables were handled in the analyses. If applicable, describe which groupings were chosen, and why.'),
    ('12a', 'chung', 'Statistical methods', 'Describe all statistical methods, including those used to control for confounding.'),
    ('12b', 'chung', 'Statistical methods', 'Describe any methods used to examine subgroups and interactions.'),
    ('12c', 'chung', 'Statistical methods', 'Explain how missing data were addressed.'),
    ('12d', 'thuan_tap', 'Statistical methods', 'If applicable, describe how loss to follow-up was addressed.'),
    ('12d', 'benh_chung', 'Statistical methods', 'If applicable, explain how matching of cases and controls was addressed.'),
    ('12d', 'cat_ngang', 'Statistical methods', 'If applicable, describe analytical methods taking account of sampling strategy.'),
    ('12e', 'chung', 'Statistical methods', 'Describe any sensitivity analyses.'),
    ('13a', 'chung', 'Participants', 'Report the numbers of individuals at each stage of the study—e.g., numbers potentially eligible, examined for eligibility, confirmed eligible, included in the study, completing follow-up, and analysed.'),
    ('13b', 'chung', 'Participants', 'Give reasons for non-participation at each stage.'),
    ('13c', 'chung', 'Participants', 'Consider use of a flow diagram.'),
    ('14a', 'chung', 'Descriptive data', 'Give characteristics of study participants (e.g., demographic, clinical, social) and information on exposures and potential confounders.'),
    ('14b', 'chung', 'Descriptive data', 'Indicate the number of participants with missing data for each variable of interest.'),
    ('14c', 'thuan_tap', 'Descriptive data', 'Summarise follow-up time—e.g., average and total amount.'),
    ('15', 'thuan_tap', 'Outcome data', 'Report numbers of outcome events or summary measures over time.'),
    ('15', 'benh_chung', 'Outcome data', 'Report numbers in each exposure category, or summary measures of exposure.'),
    ('15', 'cat_ngang', 'Outcome data', 'Report numbers of outcome events or summary measures.'),
    ('16a', 'chung', 'Main results', 'Give unadjusted estimates and, if applicable, confounder-adjusted estimates and their precision (e.g., 95% confidence intervals). Make clear which confounders were adjusted for and why they were included.'),
    ('16b', 'chung', 'Main results', 'Report category boundaries when continuous variables were categorised.'),
    ('16c', 'chung', 'Main results', 'If relevant, consider translating estimates of relative risk into absolute risk for a meaningful time period.'),
    ('17', 'chung', 'Other analyses', 'Report other analyses done—e.g., analyses of subgroups and interactions, and sensitivity analyses.'),
    ('18', 'chung', 'Key results', 'Summarise key results with reference to study objectives.'),
    ('19', 'chung', 'Limitations', 'Discuss limitations of the study, taking into account sources of potential bias or imprecision. Discuss both direction and magnitude of any potential bias.'),
    ('20', 'chung', 'Interpretation', 'Give a cautious overall interpretation considering objectives, limitations, multiplicity of analyses, results from similar studies, and other relevant evidence.'),
    ('21', 'chung', 'Generalisability', 'Discuss the generalisability (external validity) of the study results.'),
    ('22', 'chung', 'Funding', 'Give the source of funding and the role of the funders for the present study and, if applicable, for the original study on which the present article is based.'),
)

# (mã, nguyên văn)
RECORD_2015_ITEMS = (
    ('1.1', 'The type of data used should be specified in the title or abstract. When possible, the name of the databases used should be included.'),
    ('1.2', 'If applicable, the geographic region and time frame within which the study took place should be reported in the title or abstract.'),
    ('1.3', 'If linkage between databases was conducted for the study, this should be clearly stated in the title or abstract.'),
    ('6.1', 'The methods of study population selection (such as codes or algorithms used to identify subjects) should be listed in detail. If this is not possible, an explanation should be provided.'),
    ('6.2', 'Any validation studies of the codes or algorithms used to select the population should be referenced. If validation was conducted for this study and not published elsewhere, detailed methods and results should be provided.'),
    ('6.3', 'If the study involved linkage of databases, consider use of a flow diagram or other graphical display to demonstrate the data linkage process, including the number of individuals with linked data at each stage.'),
    ('7.1', 'A complete list of codes and algorithms used to classify exposures, outcomes, confounders, and effect modifiers should be provided. If these cannot be reported, an explanation should be provided.'),
    ('12.1', 'Authors should describe the extent to which the investigators had access to the database population used to create the study population.'),
    ('12.2', 'Authors should provide information on the data cleaning methods used in the study.'),
    ('12.3', 'State whether the study included person-level, institutional-level, or other data linkage across two or more databases. The methods of linkage and methods of linkage quality evaluation should be provided.'),
    ('13.1', 'Describe in detail the selection of the persons included in the study (i.e., study population selection), including filtering based on data quality, data availability, and linkage. The selection of included persons can be described in the text and/or by means of the study flow diagram.'),
    ('19.1', 'Discuss the implications of using data that were not created or collected to answer the specific research question(s). Include discussion of misclassification bias, unmeasured confounding, missing data, and changing eligibility over time, as they pertain to the study being reported.'),
    ('22.1', 'Authors should provide information on how to access any supplemental information such as the study protocol, raw data, or programming code.'),
)

assert len(STROBE_2007_ITEMS) == 41 and len(RECORD_2015_ITEMS) == 13
