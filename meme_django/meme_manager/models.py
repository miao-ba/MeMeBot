from django.db import models
from django.utils.translation import gettext_lazy as _

class MemeCategory(models.Model):
    name = models.CharField(_("類別名稱"), max_length=100)
    description = models.TextField(_("類別描述"), blank=True, null=True)
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("梗圖類別")
        verbose_name_plural = _("梗圖類別")

class Meme(models.Model):
    title = models.CharField(_("標題"), max_length=200)
    image = models.ImageField(_("圖片"), upload_to="memes/")
    category = models.ForeignKey(MemeCategory, on_delete=models.CASCADE, related_name="memes", verbose_name=_("類別"))
    keywords = models.TextField(_("關鍵字"), help_text=_("請使用逗號分隔關鍵字"))
    embedding = models.JSONField(_("文字嵌入向量"), blank=True, null=True)
    image_features = models.JSONField(_("圖片特徵向量"), blank=True, null=True)
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("梗圖")
        verbose_name_plural = _("梗圖")
        
class UserInteraction(models.Model):
    user_id = models.CharField(_("使用者ID"), max_length=100)
    input_text = models.TextField(_("輸入文字"), blank=True, null=True)
    input_image = models.BooleanField(_("是否有輸入圖片"), default=False)
    recommended_meme = models.ForeignKey(Meme, on_delete=models.SET_NULL, null=True, related_name="recommendations", verbose_name=_("推薦梗圖"))
    interaction_time = models.DateTimeField(_("互動時間"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.user_id} - {self.interaction_time}"
    
    class Meta:
        verbose_name = _("使用者互動")
        verbose_name_plural = _("使用者互動")

class ModelConfiguration(models.Model):
    name = models.CharField(_("設定名稱"), max_length=100)
    nlp_model_path = models.CharField(_("NLP模型路徑"), max_length=255, blank=True, null=True)
    cv_model_path = models.CharField(_("CV模型路徑"), max_length=255, blank=True, null=True)
    active = models.BooleanField(_("是否啟用"), default=False)
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("模型設定")
        verbose_name_plural = _("模型設定")
        
    def save(self, *args, **kwargs):
        if self.active:
            # 停用其他設定
            ModelConfiguration.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)