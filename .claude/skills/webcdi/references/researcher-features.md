# Researcher-facing features

User-facing names changed in the 2026 redesign; code names didn't.

| UI (now) | Code / DB / old docs |
|---|---|
| Administration group | `Study` / "study" |
| Add administrations | Add participants / `admin_new_fun` |
| Group settings (incl. delete-group danger zone) | Update Study / `StudyCreateView`, `study_form.html` |
| Download ▾ (scoped: selected rows or all) | Download Data / Download Selected Data |
| Status badge | completed / bg-info / survey / expired columns |
| Instruments page | My CDI Forms |

Henry's wiki "Researcher Manual" describes the **pre-2026 UI** (dropdowns,
modals, webcdi.stanford.edu); its feature descriptions are still accurate.
The in-app `/documentation/` page is current.

## Group (Study) options worth knowing

Waiver/consent text (`waiver`, Markdown, sanitized), age range, expiry days
(`test_period`), birthweight units, minimum completion minutes (`timing`),
longitudinal prefill (`prefilled_data`), payment (`allow_payment` + gift
codes), anonymous collection with a cap (`anon_collection`, `subject_cap`),
end-of-form confirmation (`confirm_completion`, `confirmation_questions`),
results graphs (`show_feedback`), redirect on completion (`redirect_boolean`,
`redirect_url`, custom button, `json_redirect`), participant-source IDs
(Prolific etc.: `participant_source_boolean`, `source_id_url_parameter_key`,
`append_source_id_to_redirect`), print-my-answers PDF, end message (Markdown),
background questionnaire choice (`demographic`, `no_demographic_boolean`,
`demographic_opt_out`), sharing opt-out, single reusable link, completion
callback (`send_completion_flag_url`).

## Adding administrations (dialog tabs are template-only)

`researcher_UI/templates/researcher_UI/administer_new_modal.html`; the backend
`admin_new_fun` dispatches on which fields are filled — keep POST field names.
Methods: typed IDs, autogenerate N, CSV upload (first column used, others
ignored; header row lets you name the ID column), single reusable link,
Prolific link, and **Import completed responses** (2018-era importer of
Brookes-PDF CSVs; two end-to-end tests check counts, not values).

## Downloads (`researcher_UI/utils/console_helper/post_helper.py` → `utils/download/`)

POST names: `download-study-csv`, `download-study-csv-adjusted`,
`download-summary-csv`, `download-selected`, `download-selected-adjusted`,
`download-selected-summary`, `download-links`, `download-dictionary`; JS in
`interface.html` swaps `data-all`/`data-selected` names by selection state.
Known issues: posting a `-selected` action with no rows → 500; pandas-3
silent no-ops in `download_data.py`/`download_summary.py`; #649 CDI-format
crash; #640 API export crash; #569 subject-ID types.

## Brookes Publishing licensing (`brookes/`)

English and Spanish **Long** and **CAT** families (ids 1, 3, 5, 7) require a
`BrookesCode` per researcher (one year). `Study.valid_code(user)` gates
adding/re-administering; `no_brookes_code.html` explains and links to the
Brookes product pages (`brookes/utils.py:purchase_url_for`). Brookes is
notified via `BROOKES_EMAIL`.

## Payments (Amazon gift cards)

`PaymentCode` model; codes entered in Group settings (format
`XXXX-XXXXXX-XXXX`), one per completed administration; when codes run out,
participants can still finish but get none — cap the group size. To add a
payment type: `PaymentCode.PAYMENT_TYPE_CHOICES`, validation in
`researcher_UI/utils/raw_gift_codes.get_gift_card_regex`, URLs in
`cdi_forms/views/administration_views.AdministrationSummaryView`, copy in
`cdi_forms/templates/cdi_forms/administration_summary.html`.

## Hard-coded special cases

- **Wordful study** (REDCap-driven, Stanford): the group must be named exactly
  `"Wordful Study (Official)"`; code in `cdi_forms/views/views.py` and
  `administration_views.py` pays $5 for the first CDI and $25 for the second.
  REDCap emails link to `/interface/<researcher>/<study>/new_participant` with
  record ID (+ `final_cdi=true` for the follow-up); `administer_new_participant`
  in `researcher_UI/views` handles 0/1/2+ existing administrations and pings
  Wordful. REDCap timing/links are edited in REDCap (Edit Instruments →
  Automated Invitations). `update_redcap` management command exists.
- Korean PDF views redirect to the HTML view (WeasyPrint font workaround).
- Henry's 2026 PRs (#586–#652) have **no descriptions**; titles like
  "Loris", "Lockit", "English99" name the requesting project, not the feature
  (e.g. "Lockit" = `required_source_id` + Japanese CAT benchmarks). Read the
  diff before assuming what one did.

## Researcher accounts

Registration at `/accounts/register/`; access to instruments is per
instrument family (admin → Researcher). Logout is POST.
django-axes is installed but disabled. A 403 right after login is usually a
stale CSRF token from a double submit — the user is in fact logged in.
