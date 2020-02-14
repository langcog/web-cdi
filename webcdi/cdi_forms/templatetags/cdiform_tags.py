from django.template.defaulttags import register

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_item_perc(dictionary, key):
    return str(float(float(dictionary.get(key))/float(dictionary.get('count')))*100)