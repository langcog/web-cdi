from .administration_views import AddNewParent  # noqa
from .administration_views import EditAdministrationView  # noqa
from .ajax_views import AjaxChargeStatus, AjaxDemographicForms  # noqa
from .download_data_views import PDFAdministrationDetailView  # noqa
from .instrument_views import AddInstruments  # noqa
from .profile import ChangePasswordView, ProfileView  # noqa
from .study_edit_data_views import ImportData  # noqa
from .study_settings_views import (AddStudy,  # noqa
                                   UpdateStudyView)
from .views import *  # noqa
from .paired_studies import AddPairedStudy  # noqa