import numpy as np
import os
import tempfile
import requests
from PIL import Image
from models.nlp_model import get_text_embedding, search_by_text, cosine_similarity
from models.cv_model import get_image_features, search_by_image

def find_similar_memes_by_text(query_text, memes, top_k=5):
    """基於文字查詢找出最相似的梗圖
    
    Args:
        query_text (str): 查詢文字
        memes (list): 梗圖列表，每個元素是一個包含 'id' 和 'embedding' 的字典
        top_k (int): 返回前k個結果
        
    Returns:
        list: 包含 (meme_id, 相似度分數) 元組的列表，按相似度從高到低排序
    """
    if not query_text or not memes:
        return []
    
    # 過濾掉沒有嵌入向量的梗圖
    valid_memes = [(meme['id'], meme['embedding']) for meme in memes if meme.get('embedding')]
    
    # 使用NLP模型搜尋相似梗圖
    return search_by_text(query_text, valid_memes, top_k=top_k)

def find_similar_memes_by_image(image_data, memes, top_k=5):
    """基於圖片查詢找出最相似的梗圖
    
    Args:
        image_data: 圖片數據，可以是路徑、URL或二進制數據
        memes (list): 梗圖列表，每個元素是一個包含 'id' 和 'image_features' 的字典
        top_k (int): 返回前k個結果
        
    Returns:
        list: 包含 (meme_id, 相似度分數) 元組的列表，按相似度從高到低排序
    """
    if not image_data or not memes:
        return []
    
    # 過濾掉沒有圖片特徵的梗圖
    valid_memes = [(meme['id'], meme['image_features']) for meme in memes if meme.get('image_features')]
    
    # 處理不同類型的圖片數據
    image_path = None
    temp_file = None
    
    try:
        if isinstance(image_data, str):
            if os.path.exists(image_data):
                # 本地文件路徑
                image_path = image_data
            elif image_data.startswith(('http://', 'https://')):
                # 網絡URL
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                response = requests.get(image_data, stream=True)
                if response.status_code == 200:
                    with open(temp_file.name, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    image_path = temp_file.name
        else:
            # 二進制數據
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            with open(temp_file.name, 'wb') as f:
                f.write(image_data)
            image_path = temp_file.name
        
        # 使用CV模型搜尋相似梗圖
        if image_path:
            results = search_by_image(image_path, valid_memes, top_k=top_k)
            return results
        else:
            return []
    
    finally:
        # 清理臨時文件
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def combine_search_results(text_results, image_results, weight_text=0.5, top_k=5):
    """結合文字和圖片搜尋結果
    
    Args:
        text_results (list): 文字搜尋結果
        image_results (list): 圖片搜尋結果
        weight_text (float): 文字搜尋結果的權重 (0~1)
        top_k (int): 返回前k個結果
        
    Returns:
        list: 包含 (meme_id, 相似度分數) 元組的列表，按相似度從高到低排序
    """
    # 如果只有一種結果，直接返回
    if not text_results:
        return image_results[:top_k]
    if not image_results:
        return text_results[:top_k]
    
    # 組合兩種結果
    weight_image = 1 - weight_text
    combined = {}
    
    # 加入文字搜尋結果
    for meme_id, score in text_results:
        combined[meme_id] = weight_text * score
    
    # 加入圖片搜尋結果
    for meme_id, score in image_results:
        if meme_id in combined:
            combined[meme_id] += weight_image * score
        else:
            combined[meme_id] = weight_image * score
    
    # 轉換為列表並排序
    results = [(meme_id, score) for meme_id, score in combined.items()]
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]

def recommend_memes(query_text=None, query_image=None, memes=None, top_k=5, weight_text=0.5):
    """推薦梗圖
    
    Args:
        query_text (str, optional): 查詢文字
        query_image: 查詢圖片
        memes (list): 梗圖列表
        top_k (int): 返回前k個結果
        weight_text (float): 文字搜尋結果的權重 (0~1)
        
    Returns:
        list: 推薦梗圖ID列表
    """
    if not memes:
        return []
    
    text_results = []
    image_results = []
    
    # 文字搜尋
    if query_text:
        text_results = find_similar_memes_by_text(query_text, memes, top_k=top_k)
    
    # 圖片搜尋
    if query_image:
        image_results = find_similar_memes_by_image(query_image, memes, top_k=top_k)
    
    # 組合結果
    if query_text and query_image:
        results = combine_search_results(text_results, image_results, weight_text=weight_text, top_k=top_k)
    elif query_text:
        results = text_results
    elif query_image:
        results = image_results
    else:
        return []
    
    # 返回梗圖ID列表
    return [meme_id for meme_id, _ in results]