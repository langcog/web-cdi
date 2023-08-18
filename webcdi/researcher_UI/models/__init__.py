from .models import *  # noqa
from .instrument_family import InstrumentFamily  # noqa
from .instrument import instrument  # noqa
from .researcher import researcher  # noqa
from .study import study  # noqa
from .benchmark import Benchmark  # noqa
from .administration import administration, administration_data, AdministrationSummary  # noqa
from .demographic import Demographic  # noqa
from .payment_code import payment_code  # noqa
from .ip_address import ip_address  # noqa
from .instrument_score import InstrumentScore  # noqa
from .measure import Measure  # noqa
from .summary_data import SummaryData  # noqa


from django.contrib.auth.models import User

User._meta.get_field("email")._unique = True