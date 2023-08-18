# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def get_meta_header():  # Returns a list of variables for administration objects
    return [
        "study",
        "subject_id",
        "administration_number",
        "link",
        "completed",
        "completedBackgroundInfo",
        "expiration_date",
        "last_modified",
    ]


def get_background_header():  # Returns a list of variables for backgroundinfo objects
    return [
        "id",
        "age",
        "sex",
        "birth_order",
        "birth_weight_lb",
        "birth_weight_kg",
        "early_or_late",
        "due_date_diff",
        "mother_yob",
        "mother_education",
        "father_yob",
        "father_education",
        "annual_income",
        "child_hispanic_latino",
        "caregiver_info",
        "other_languages_boolean",
        "language_from",
        "language_days_per_week",
        "language_hours_per_day",
        "ear_infections_boolean",
        "ear_infections",
        "hearing_loss_boolean",
        "hearing_loss",
        "vision_problems_boolean",
        "vision_problems",
    ]
