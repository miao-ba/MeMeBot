import os
import numpy as np
import sys
from django.conf import settings

# 添加models目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def generate_embeddings(meme_id):
    """為單一梗圖生成嵌入向量"""
    try:
        from meme_manager.models import Meme, ModelConfiguration
        from models.nlp_model import get_text_embedding
        from models.cv_model import get_image_features
        
        meme = Meme.objects.get(id=meme_id)
        
        # 獲取啟用的模型設定
        config = ModelConfiguration.objects.filter(active=True).first()
        if not config:
            return
        
        # 生成文字嵌入向量
        if config.nlp_model_path:
            keywords = meme.keywords
            embedding = get_text_embedding(keywords, model_path=config.nlp_model_path)
            meme.embedding = embedding.tolist() if embedding is not None else None
        
        # 生成圖片特徵向量
        if config.cv_model_path:
            image_path = os.path.join(settings.MEDIA_ROOT, meme.image.name)
            features = get_image_features(image_path, model_path=config.cv_model_path)
            meme.image_features = features.tolist() if features is not None else None
        
        meme.save()
    except Exception as e:
        print(f"為梗圖 {meme_id} 生成嵌入向量時出錯: {str(e)}")

def generate_embeddings_for_all():
    """為所有梗圖生成嵌入向量"""
    from meme_manager.models import Meme
    memes = Meme.objects.all()
    for meme in memes:
        generate_embeddings(meme.id)

def reload_models():
    """根據啟用的設定重新載入NLP和CV模型"""
    try:
        from models.nlp_model import load_model as load_nlp_model
        from models.cv_model import load_model as load_cv_model
        from meme_manager.models import ModelConfiguration
        
        config = ModelConfiguration.objects.filter(active=True).first()
        if config:
            if config.nlp_model_path:
                load_nlp_model(config.nlp_model_path)
            if config.cv_model_path:
                load_cv_model(config.cv_model_path)
    except Exception as e:
        print(f"重新載入模型時出錯: {str(e)}")