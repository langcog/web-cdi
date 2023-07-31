import os

PROJECT_ROOT = os.path.abspath(
    os.path.dirname(__file__)
)  # Declare project file directory


def get_demographic_filename(std):
    if std.demographic_opt_out:
        return os.path.realpath(
            PROJECT_ROOT
            + "/form_data/background_info/"
            + std.instrument.language
            + "_no_demographics.json"
        )
    try:
        return os.path.realpath(PROJECT_ROOT + std.demographic.path)
    except:
        return ""

from itertools import tee, islice, chain

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)