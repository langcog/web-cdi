# web-cdi

web-cdi [webcdi.stanford.edu](http://webcdi.stanford.edu) is a project for the web-based administration of the [MacArthur-Bates Communicative Development Inventory](mb-cdi.stanford.edu), a checklist instrument for measuring children's early language development via parent report.

# Using the system

web-cdi is currently in an alpha pilot, and is available for testing by researchers. Please contact [webcdi-contact.stanford.edu](mailto://webcdi-contact@stanford.edu).  

# Codebase documentation

## Adding new forms

+ Forms are stored in CSV format in web-cdi/webcdi/cdi_form_csv
  + JSON objects with other information are in web-cdi/webcdi/cdi_forms/form_data/
+ Demographics are in webcdi/cdi_forms/forms.py
##
