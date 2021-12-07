from django.apps import AppConfig

#from django.utils.translation import ugettext_lazy as _

class ResearcherUIAppConfig(AppConfig):
    name = 'researcher_UI'

    def ready(self):
        import researcher_UI.signals