from django import template
register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]

@register.filter
def div(numerator, demoninator):
    return int(float(numerator/demoninator)*100)
