import datetime

def try_parsing_date_fun(text):
    date_formats = (
        "%Y.%m.%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m.%d.%Y",
        "%m-%d-%Y",
        "%m/%d/%Y",
    )
    for fmt in date_formats:
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError("no valid date format found")