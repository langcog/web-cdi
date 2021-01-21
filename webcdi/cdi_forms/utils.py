import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__)) # Declare project file directory

def get_demographic_filename(std):
    try:
        return os.path.realpath(PROJECT_ROOT + std.demographic.path)
    except:
        return ''