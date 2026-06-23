"""
MetaDent classification taxonomy — the 18 intraoral conditions (C1–C18).

Single source of truth: ``prompts/prompts.py`` (``label_desc_en``), reproduced
here as an importable mapping for the QA-pairs pillar. The ``name``/``note``
fields are what each evaluated VLM is shown.
"""

LABELS_EN = {
    "C1": {"name": "Dental caries",
           "note": "Clearly visible dental caries; early white-spot lesions are excluded."},
    "C2": {"name": "Non-carious, unrestored tooth defect",
           "note": "Tooth fractures or cervical defects not caused by caries and not yet restored "
                   "(e.g. wedge-shaped defects or notching). Excludes physiological/pathological wear."},
    "C3": {"name": "Tooth wear or erosion",
           "note": "Loss of tooth structure due to physiological/pathological wear, or erosion. "
                   "Defects caused by caries or minor enamel cracks are excluded."},
    "C4": {"name": "Gingival inflammation",
           "note": "Gingival redness/swelling, with or without bleeding, with or without alveolar bone resorption."},
    "C5": {"name": "Gingival recession",
           "note": "Recession of the gingival margin, with root exposure or visible black triangles."},
    "C6": {"name": "Dental plaque or calculus",
           "note": "Visible plaque or calculus accumulation. Excludes occasional food debris."},
    "C7": {"name": "Tooth discoloration",
           "note": "Abnormal colour from staining, fluorosis, pulp necrosis, or enamel demineralization. "
                   "Excludes dark discoloration due to caries."},
    "C8": {"name": "Partial edentulism",
           "note": "One or more missing teeth, no residual roots present, no prosthetic replacement."},
    "C9": {"name": "Residual root",
           "note": "Complete loss of the clinical crown, only the root remaining."},
    "C10": {"name": "Dental filling (direct filling)",
            "note": "Direct restorative materials: composite resin, amalgam, temporary fillings, gutta-percha."},
    "C11": {"name": "Fixed prosthesis",
            "note": "Crowns, bridges, veneers, inlays, and other fixed prostheses."},
    "C12": {"name": "Removable denture",
            "note": "Partial and complete removable dentures."},
    "C13": {"name": "Interdental spacing",
            "note": "Spaces between teeth without missing teeth (diastema/physiological spacing). "
                    "Excludes recession black triangles when adjacent teeth contact."},
    "C14": {"name": "Malocclusion or dental malalignment",
            "note": "Tooth rotation, crowding, or displacement. Orthodontic appliances alone do not imply malalignment."},
    "C15": {"name": "Conventional orthodontic appliance",
            "note": "Brackets, archwires, elastics, and other conventional orthodontic materials."},
    "C16": {"name": "Clear aligner orthodontic appliance",
            "note": "Clear aligners, attachments, retainers, and other invisible-orthodontic components."},
    "C17": {"name": "Oral ulcer",
            "note": "Recurrent aphthous ulcers and traumatic ulcers. Excludes periodontal redness/swelling."},
    "C18": {"name": "Oral wound",
            "note": "Extraction sockets, trauma, or surgical wounds. Excludes gingivitis redness/bleeding."},
}

LABELS = [f"C{i}" for i in range(1, 19)]


def name(code: str) -> str:
    """Human-readable name for a ``Ck`` code."""
    return LABELS_EN[code]["name"]
