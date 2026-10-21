import json

from cdi_forms.utils import get_demographic_filename

# Asked only by particular studies' background forms (e.g. Argentine Spanish,
# English Centiment); listed in downloads only when the study's form has them.
STUDY_SPECIFIC_FIELDS = [
    "children_comforted",
    "show_respect",
    "close_bonds",
    "parents_help_learn",
    "play_learning",
    "explore_experiment",
    "do_as_told",
    "read_at_home",
    "teach_alphbet",
    "rhyming_games",
    "read_for_pleasure",
    "child_asks_for_reading",
    "child_self_reads",
    "child_asks_words_say",
    "place_of_residence",
    "primary_caregiver_occupation",
    "primary_caregiver_occupation_description",
    "secondary_caregiver_occupation",
    "secondary_caregiver_occupation_description",
    "kindergarten_since_when",
    "kindergarten_hpd",
    "kindergarten_dpw",
]


def form_fields(study_obj):
    """Field names in the study's background form, or None if it can't be read."""
    try:
        with open(get_demographic_filename(study_obj), encoding="utf-8") as f:
            pages = json.load(f)
    except (OSError, ValueError):
        return None
    found = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("field"), str):
                found.add(node["field"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(pages)
    return found


def get_background_header(study_obj):
    # Fetch background data variables
    background_header = [
        "source_id",
        "event_id",
        "age",
        "sex",
        "country",
        "zip_code",
        "birth_order",
        "birth_weight_lb",
        "birth_weight_confirmation_lb",
        "birth_weight_kg",
        "birth_weight_confirmation_kg",
        "multi_birth_boolean",
        "multi_birth",
        "sibling_boolean",
        "sibling_count",
        "sibling_data",
        "born_on_due_date",
        "early_or_late",
        "due_date_diff",
        "form_filler",
        "form_filler_other",
        "primary_caregiver",
        "primary_caregiver_other",
        "mother_yob",
        "mother_yob_confirmation",
        "mother_education",
        "secondary_caregiver",
        "secondary_caregiver_other",
        "father_yob",
        "father_education",
        "annual_income",
        "child_hispanic_latino",
        "child_ethnicity",
        "caregiver_info",
        "caregiver_other",
        "other_languages_boolean",
        "other_languages",
        "language_from",
        "language_days_per_week",
        "language_hours_per_day",
        "ear_infections_boolean",
        "ear_infections",
        "hearing_loss_boolean",
        "hearing_loss",
        "vision_problems_boolean",
        "vision_problems",
        "illnesses_boolean",
        "illnesses",
        "services_boolean",
        "services",
        "worried_boolean",
        "worried",
        "learning_disability_boolean",
        "learning_disability",
        "children_comforted",
        "show_respect",
        "close_bonds",
        "parents_help_learn",
        "play_learning",
        "explore_experiment",
        "do_as_told",
        "read_at_home",
        "teach_alphbet",
        "rhyming_games",
        "read_for_pleasure",
        "child_asks_for_reading",
        "child_self_reads",
        "child_asks_words_say",
        "place_of_residence",
        "primary_caregiver_occupation",
        "primary_caregiver_occupation_description",
        "secondary_caregiver_occupation",
        "secondary_caregiver_occupation_description",
        "kindergarten_since_when",
        "kindergarten_hpd",
        "kindergarten_dpw",
    ]
    fields = form_fields(study_obj)
    if fields is not None:
        background_header = [
            h for h in background_header if h not in STUDY_SPECIFIC_FIELDS or h in fields
        ]
    if not study_obj.confirmation_questions:
        background_header.remove("birth_weight_confirmation_lb")
        background_header.remove("birth_weight_confirmation_kg")
        background_header.remove("mother_yob_confirmation")
    if not study_obj.participant_source_boolean:
        background_header.remove("source_id")
    return background_header
