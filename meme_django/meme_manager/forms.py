from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Meme, MemeCategory, ModelConfiguration

class MemeCategoryForm(forms.ModelForm):
    class Meta:
        model = MemeCategory
        fields = ['name', 'description']
        
class MemeForm(forms.ModelForm):
    class Meta:
        model = Meme
        fields = ['title', 'image', 'category', 'keywords']
        
    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords')
        if keywords:
            # 確保關鍵字以逗號分隔
            keywords = ','.join([k.strip() for k in keywords.split(',') if k.strip()])
        return keywords

class ModelConfigurationForm(forms.ModelForm):
    class Meta:
        model = ModelConfiguration
        fields = ['name', 'nlp_model_path', 'cv_model_path', 'active']
        
    def clean(self):
        cleaned_data = super().clean()
        nlp_model_path = cleaned_data.get('nlp_model_path')
        cv_model_path = cleaned_data.get('cv_model_path')
        
        if not nlp_model_path and not cv_model_path:
            raise forms.ValidationError(_("至少需要提供一個模型路徑。"))
            
        return cleaned_data