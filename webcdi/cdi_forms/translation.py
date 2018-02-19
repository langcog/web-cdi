from modeltranslation.translator import register, TranslationOptions
from .models import Choices

@register(Choices)
class ChoicesTranslationOptions(TranslationOptions):
    fields = ('choice_set',)
