# Web-CDI

[Web-CDI](http://webcdi.stanford.edu) is a project for the web-based administration of the [MacArthur-Bates Communicative Development Inventory](http://mb-cdi.stanford.edu), a checklist instrument for measuring children's early language development via parent report.

# Using the system

Web-CDI is currently in an alpha pilot, and is available for testing by researchers. If you would like to collect data via Web-CDI, please contact [webcdi-contact (at) stanford (dot) edu](mailto://webcdi-contact@stanford.edu) for more information.  

# Codebase documentation

## Adding new forms

+ Forms are stored in CSV format in web-cdi/webcdi/cdi_form_csv
  + JSON objects with other information are in web-cdi/webcdi/cdi_forms/form_data/
+ Demographic form design are in webcdi/cdi_forms/forms.py and webcdi/cdi_forms/models.py
##
