from django import template

register = template.Library()


@register.simple_tag
def instrument_filter(field):
    if len(field) % 3 != 0:
        res = round(len(field) / 3)
        _first_end = res + 1
        _second_start = _first_end
        _third_start = _second_start + res
    else:
        res = round(len(field) / 3)
        _first_end = res
        _second_start = _first_end
        _third_start = _second_start + res

    return field[:_first_end], field[_second_start:_third_start], field[_third_start:]
