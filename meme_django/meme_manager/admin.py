from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import MemeCategory, Meme, UserInteraction, ModelConfiguration
from .forms import MemeForm

@admin.register(MemeCategory)
class MemeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)

@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    form = MemeForm
    list_display = ('title', 'category', 'keywords', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'keywords')
    ordering = ('-created_at',)
    readonly_fields = ('embedding', 'image_features')
    
    def save_model(self, request, obj, form, change):
        # 儲存物件
        super().save_model(request, obj, form, change)
        
        # 觸發嵌入向量生成
        from .tasks import generate_embeddings
        generate_embeddings(obj.id)

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'input_text', 'input_image', 'recommended_meme', 'interaction_time')
    list_filter = ('input_image', 'interaction_time')
    search_fields = ('user_id', 'input_text')
    ordering = ('-interaction_time',)
    readonly_fields = ('user_id', 'input_text', 'input_image', 'recommended_meme', 'interaction_time')

@admin.register(ModelConfiguration)
class ModelConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'nlp_model_path', 'cv_model_path', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        if obj.active:
            # 確保只有一個啟用的設定
            self.model.objects.exclude(pk=obj.pk).update(active=False)
        super().save_model(request, obj, form, change)
        
        # 如果啟用狀態改變，重新載入模型
        if 'active' in form.changed_data and obj.active:
            from .tasks import reload_models
            reload_models()