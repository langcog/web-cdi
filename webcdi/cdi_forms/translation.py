from modeltranslation.translator import TranslationOptions, register

from .models import Choices


@register(Choices)
class ChoicesTranslationOptions(TranslationOptions):
    fields = ("choice_set",)
