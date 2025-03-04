import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer

# 預設模型
DEFAULT_MODEL_NAME = "distilbert-base-multilingual-cased"
nlp_model = None
tokenizer = None

def load_model(model_path=None):
    """載入NLP模型
    
    Args:
        model_path (str, optional): 模型的路徑或名稱，如果為None則使用預設模型
        
    Returns:
        tuple: (模型, tokenizer) 元組
    """
    global nlp_model, tokenizer
    
    try:
        if model_path and os.path.exists(model_path):
            # 載入自定義模型
            print(f"載入自定義NLP模型: {model_path}")
            nlp_model = SentenceTransformer(model_path)
            tokenizer = None  # SentenceTransformer 處理自己的 tokenization
        else:
            # 載入預設模型
            model_name = model_path if model_path else DEFAULT_MODEL_NAME
            print(f"載入預設NLP模型: {model_name}")
            
            try:
                # 嘗試載入為 SentenceTransformer
                nlp_model = SentenceTransformer(model_name)
                tokenizer = None
            except:
                # 回退到 Hugging Face 模型
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                nlp_model = AutoModel.from_pretrained(model_name)
        
        return nlp_model, tokenizer
    except Exception as e:
        print(f"載入NLP模型時出錯: {str(e)}")
        return None, None

def get_text_embedding(text, model_path=None):
    """獲取文字的嵌入向量
    
    Args:
        text (str): 輸入文字
        model_path (str, optional): 模型路徑，用於首次載入
        
    Returns:
        np.ndarray: 嵌入向量
    """
    global nlp_model, tokenizer
    
    if not nlp_model:
        nlp_model, tokenizer = load_model(model_path)
    
    if not nlp_model:
        print("未載入NLP模型，無法生成嵌入向量")
        return None
    
    try:
        # 確保文字不為空
        if not text or text.strip() == "":
            return np.zeros(768)  # 使用全零向量表示空文字
        
        # 判斷模型類型
        if isinstance(nlp_model, SentenceTransformer):
            # 對於 SentenceTransformer 模型
            embedding = nlp_model.encode(text, convert_to_numpy=True)
            return embedding
        else:
            # 對於 Hugging Face 模型
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = nlp_model(**inputs)
                
            # 取最後一層隱藏狀態的平均值作為嵌入向量
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            return embedding
    except Exception as e:
        print(f"生成文字嵌入向量時出錯: {str(e)}")
        return None

def search_by_text(query, memes_embeddings, top_k=5):
    """基於文字搜尋最相似的梗圖
    
    Args:
        query (str): 查詢文字
        memes_embeddings (list): 梗圖嵌入向量列表，每個元素是 (meme_id, embedding) 元組
        top_k (int): 返回前 k 個結果
        
    Returns:
        list: 包含 (meme_id, 相似度分數) 元組的列表，按相似度從高到低排序
    """
    if not query or not memes_embeddings:
        return []
    
    query_embedding = get_text_embedding(query)
    if query_embedding is None:
        return []
    
    results = []
    for meme_id, embedding in memes_embeddings:
        if embedding is None:
            continue
            
        # 計算餘弦相似度
        similarity = cosine_similarity(query_embedding, np.array(embedding))
        results.append((meme_id, float(similarity)))
    
    # 依相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]

def cosine_similarity(v1, v2):
    """計算兩個向量的餘弦相似度
    
    Args:
        v1 (np.ndarray): 向量1
        v2 (np.ndarray): 向量2
        
    Returns:
        float: 餘弦相似度，範圍 [-1, 1]
    """
    if len(v1.shape) > 1:
        v1 = v1.squeeze()
    if len(v2.shape) > 1:
        v2 = v2.squeeze()
        
    v1_norm = np.linalg.norm(v1)
    v2_norm = np.linalg.norm(v2)
    
    if v1_norm == 0 or v2_norm == 0:
        return 0.0
        
    return np.dot(v1, v2) / (v1_norm * v2_norm)