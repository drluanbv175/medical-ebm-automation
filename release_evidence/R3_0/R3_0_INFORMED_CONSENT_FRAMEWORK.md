# R3.0 Informed Consent Framework

**Document:** R3_0_INFORMED_CONSENT_FRAMEWORK.md  
**Date:** 2026-06-28  
**Phase:** R3.0  
**Status:** FRAMEWORK DESIGN — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define the framework for informed consent in the Medical Research OS. No consent form is to be generated, used, or treated as valid until ethics approval is obtained.

---

## 1. Required ICF elements (per ICH-GCP E6 R2 §4.8 and Declaration of Helsinki)

| Element | ID | Requirement |
|---------|-----|-------------|
| Study purpose | IC-01 | Plain language explanation of research objectives |
| Procedures involved | IC-02 | All study procedures including data collection |
| Foreseeable risks | IC-03 | All reasonably foreseeable risks and discomforts |
| Anticipated benefits | IC-04 | Benefits to participant and/or society |
| Alternatives | IC-05 | Available alternatives to participation |
| Confidentiality | IC-06 | How data will be protected; who has access |
| Compensation | IC-07 | Compensation for injury (if any) |
| Contact persons | IC-08 | For questions and emergency |
| Voluntary participation | IC-09 | Participation is voluntary; withdrawal is without penalty |
| Signature block | IC-10 | Participant + witness; date; copy provided to participant |
| IRB approval reference | IC-11 | Ethics approval number and committee name |
| Right to withdraw | IC-12 | Can withdraw at any time without consequence |
| Data retention | IC-13 | How long data will be kept and in what form |

---

## 2. Vulnerable population protections

| Population | Additional protection |
|-----------|----------------------|
| Minors | Parental/guardian consent + assent where age-appropriate |
| Cognitively impaired | Legally authorized representative consent |
| Prisoners | Additional IRB review; no coercion |
| Pregnant women | Specific risk assessment for fetus |
| Students / employees | No coercive authority relationship |

---

## 3. ICF lifecycle in Research OS (design)

```
Draft ICF → IRB Review → Approved ICF (version + approval ref)
    ↓
Participant enrollment session
    ↓
ICF presented and discussed (no time pressure)
    ↓
Questions answered
    ↓
Signed (paper + digital — electronic consent requires validated system)
    ↓
Copy provided to participant
    ↓
Signed copy stored in ISF (Investigator Site File)
    ↓
Record of consent logged in EDC (consent_obtained: true, date, version)
```

**Electronic consent requirement:** Validated eConsent system required — NOT IMPLEMENTED.

---

## 4. Re-consent triggers

| Trigger | Action |
|---------|--------|
| Protocol amendment affecting participant | Re-consent required |
| New significant risk identified | Re-consent required |
| Consent form version update | Re-consent required |
| Withdrawal of consent | Stop all participant procedures; flag data |

---

## Conclusion

```
Informed consent framework: DESIGN COMPLETE
ICF approved for use: NO — requires ethics approval first
Participant enrollment: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
