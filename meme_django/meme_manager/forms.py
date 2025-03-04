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
# 簡化的批量上傳表單
class BatchUploadForm(forms.Form):
    """批量上傳梗圖表單"""
    category = forms.ModelChoiceField(
        queryset=MemeCategory.objects.all(),
        label=_("類別"),
        help_text=_("選擇所有上傳梗圖的類別")
    )
    
    # 使用普通FileField，但前端將使用JavaScript處理多文件上傳
    images = forms.FileField(
        label=_("選擇圖片"),
        help_text=_("可選擇多個圖片檔案（jpg, png, gif）"),
        required=True
    )
    
    auto_generate_tags = forms.BooleanField(
        required=False,
        initial=True,
        label=_("自動生成標籤"),
        help_text=_("使用AI為上傳的圖片自動生成標籤")
    )
    
    extract_text = forms.BooleanField(
        required=False,
        initial=True,
        label=_("提取圖片文字"),
        help_text=_("從圖片中提取文字內容並加入標籤")
    )
    
    extract_filename_tags = forms.BooleanField(
        required=False,
        initial=True,
        label=_("從檔名提取標籤"),
        help_text=_("從檔名格式「【SS0008】你什麼時候才要離開你的幻想小世界啊」中提取文字作為標籤")
    )