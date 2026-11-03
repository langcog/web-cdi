from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_perc(dictionary, key):
    try:
        return str(
            float(float(dictionary.get(key)) / float(dictionary.get("count"))) * 100
        )
    except Exception:
        return 0


@register.filter
def get_item_count(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_usage_perc(count, total):
    return str(float(count / total) * 100)


@register.simple_tag
def to_list(*args):
    return args


@register.simple_tag
def set_true():
    return True


@register.simple_tag
def set_false():
    return False


@register.filter
def get_part_menu_number(part):
    min_page = 99
    for item in part["types"]:
        if "page" in item:
            if item["page"] < min_page:
                min_page = item["page"]
        if "sections" in item:
            for section in item["sections"]:
                if section["page"] < min_page:
                    min_page = section["page"]
    return min_page


@register.filter
def max_page(contents):
    page = 0
    for part in contents:
        for item in part["types"]:
            if "page" in item:
                if item["page"] > page:
                    page = item["page"]
            if "sections" in item:
                for section in item["sections"]:
                    if section["page"] > page:
                        page = section["page"]
    return page
