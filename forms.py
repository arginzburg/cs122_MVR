from django import forms
from . import models

# class AgencyForm(Agency):
#     class Meta:
#         model = Agency
#         fields = ['agency']

class KeywordsForm(forms.Form):
    keywords = forms.CharField(label='Keywords', max_length=200)