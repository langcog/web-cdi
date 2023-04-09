from django.contrib.admin.filters import AllValuesFieldListFilter


class DropdownFilter(AllValuesFieldListFilter):
    template = "admin/filter/dropdown-filter.html"
