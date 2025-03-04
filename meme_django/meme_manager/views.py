from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
import json
from .models import MemeCategory, Meme, UserInteraction, ModelConfiguration
from .forms import MemeCategoryForm, MemeForm, ModelConfigurationForm
from .tasks import generate_embeddings, generate_embeddings_for_all, reload_models
from django.views.decorators.csrf import csrf_exempt
@login_required
def dashboard(request):
    total_memes = Meme.objects.count()
    total_categories = MemeCategory.objects.count()
    recent_interactions = UserInteraction.objects.order_by('-interaction_time')[:10]
    
    context = {
        'total_memes': total_memes,
        'total_categories': total_categories,
        'recent_interactions': recent_interactions,
    }
    
    return render(request, 'meme_manager/dashboard.html', context)

@login_required
def meme_list(request):
    memes = Meme.objects.all().order_by('-created_at')
    categories = MemeCategory.objects.all()
    
    # 依類別篩選
    category_id = request.GET.get('category')
    if category_id:
        memes = memes.filter(category_id=category_id)
    
    context = {
        'memes': memes,
        'categories': categories,
        'selected_category': category_id,
    }
    
    return render(request, 'meme_manager/meme_list.html', context)

@login_required
def add_meme(request):
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save()
            messages.success(request, _("梗圖已成功新增。"))
            
            # 在背景產生嵌入向量
            generate_embeddings(meme.id)
            
            # 清除API快取
            clear_bot_cache()
            
            return redirect('meme_list')
    else:
        form = MemeForm()
    
    context = {
        'form': form,
        'title': _('新增梗圖'),
    }
    
    return render(request, 'meme_manager/meme_form.html', context)

@login_required
def edit_meme(request, meme_id):
    meme = get_object_or_404(Meme, id=meme_id)
    
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES, instance=meme)
        if form.is_valid():
            meme = form.save()
            messages.success(request, _("梗圖已成功更新。"))
            
            # 如需要重新產生嵌入向量
            if 'keywords' in form.changed_data or 'image' in form.changed_data:
                generate_embeddings(meme.id)
                
            # 清除API快取
            clear_bot_cache()
                
            return redirect('meme_list')
    else:
        form = MemeForm(instance=meme)
    
    context = {
        'form': form,
        'title': _('編輯梗圖'),
        'meme': meme,
    }
    
    return render(request, 'meme_manager/meme_form.html', context)
def clear_bot_cache():
    """清除機器人的梗圖快取"""
    try:
        # 嘗試向機器人的API發送清除快取請求
        # 實際上我們使用的是強制重新整理，所以不需要額外的API
        pass
    except Exception as e:
        print(f"清除機器人快取出錯: {str(e)}")
@login_required
def delete_meme(request, meme_id):
    meme = get_object_or_404(Meme, id=meme_id)
    
    if request.method == 'POST':
        meme.delete()
        messages.success(request, _("梗圖已成功刪除。"))
        return redirect('meme_list')
    
    context = {
        'meme': meme,
    }
    
    return render(request, 'meme_manager/meme_confirm_delete.html', context)

@login_required
def category_list(request):
    categories = MemeCategory.objects.all().order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'meme_manager/category_list.html', context)

@login_required
def add_category(request):
    if request.method == 'POST':
        form = MemeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("類別已成功新增。"))
            return redirect('category_list')
    else:
        form = MemeCategoryForm()
    
    context = {
        'form': form,
        'title': _('新增類別'),
    }
    
    return render(request, 'meme_manager/category_form.html', context)

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(MemeCategory, id=category_id)
    
    if request.method == 'POST':
        form = MemeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("類別已成功更新。"))
            return redirect('category_list')
    else:
        form = MemeCategoryForm(instance=category)
    
    context = {
        'form': form,
        'title': _('編輯類別'),
        'category': category,
    }
    
    return render(request, 'meme_manager/category_form.html', context)

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(MemeCategory, id=category_id)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, _("類別已成功刪除。"))
        return redirect('category_list')
    
    context = {
        'category': category,
    }
    
    return render(request, 'meme_manager/category_confirm_delete.html', context)

@login_required
def model_configuration(request):
    configs = ModelConfiguration.objects.all().order_by('-created_at')
    active_config = ModelConfiguration.objects.filter(active=True).first()
    
    if request.method == 'POST':
        form = ModelConfigurationForm(request.POST)
        if form.is_valid():
            config = form.save()
            messages.success(request, _("模型設定已成功儲存。"))
            
            # 如果是啟用的設定，重新載入模型
            if config.active:
                reload_models()
                
            return redirect('model_configuration')
    else:
        form = ModelConfigurationForm()
    
    context = {
        'form': form,
        'configs': configs,
        'active_config': active_config,
    }
    
    return render(request, 'meme_manager/model_configuration.html', context)

@login_required
def activate_config(request, config_id):
    config = get_object_or_404(ModelConfiguration, id=config_id)
    
    # 停用所有其他設定
    ModelConfiguration.objects.all().update(active=False)
    
    # 啟用選定的設定
    config.active = True
    config.save()
    
    # 重新載入模型
    reload_models()
    
    messages.success(request, _("模型設定已成功啟用。"))
    return redirect('model_configuration')

@login_required
def regenerate_all_embeddings(request):
    if request.method == 'POST':
        # 啟動重新產生嵌入向量的任務
        generate_embeddings_for_all()
        messages.success(request, _("所有梗圖的嵌入向量重新生成任務已啟動。"))
    
    return redirect('dashboard')

@login_required
def interaction_history(request):
    interactions = UserInteraction.objects.all().order_by('-interaction_time')
    
    context = {
        'interactions': interactions,
    }
    
    return render(request, 'meme_manager/interaction_history.html', context)

def api_get_memes(request):
    """Discord機器人獲取梗圖的API端點"""
    category_id = request.GET.get('category')
    
    if category_id:
        memes = Meme.objects.filter(category_id=category_id)
    else:
        memes = Meme.objects.all()
    
    data = [{
        'id': meme.id,
        'title': meme.title,
        'image_url': request.build_absolute_uri(meme.image.url),
        'category': meme.category.name,
        'keywords': meme.keywords,
        'embedding': meme.embedding,
        'image_features': meme.image_features
    } for meme in memes]
    
    return JsonResponse({'memes': data})
@csrf_exempt
def api_record_interaction(request):
    """Discord機器人記錄使用者互動的API端點"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            input_text = data.get('input_text')
            input_image = data.get('input_image', False)
            recommended_meme_id = data.get('recommended_meme_id')
            
            # 建立互動記錄
            interaction = UserInteraction(
                user_id=user_id,
                input_text=input_text,
                input_image=input_image
            )
            
            if recommended_meme_id:
                try:
                    meme = Meme.objects.get(id=recommended_meme_id)
                    interaction.recommended_meme = meme
                except Meme.DoesNotExist:
                    pass
                
            interaction.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})