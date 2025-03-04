import os
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

# 預設模型
DEFAULT_MODEL_NAME = "resnet50"
cv_model = None
transform = None

def load_model(model_path=None):
    """載入CV模型
    
    Args:
        model_path (str, optional): 模型的路徑或名稱，如果為None則使用預設模型
        
    Returns:
        torch.nn.Module: 載入的模型
    """
    global cv_model, transform
    
    try:
        if model_path and os.path.exists(model_path):
            # 載入自定義模型
            print(f"載入自定義CV模型: {model_path}")
            cv_model = torch.load(model_path)
        else:
            # 載入預設模型
            model_name = model_path if model_path else DEFAULT_MODEL_NAME
            print(f"載入預設CV模型: {model_name}")
            
            if model_name == "resnet50":
                cv_model = models.resnet50(pretrained=True)
                # 移除最後的全連接層，只使用特徵提取部分
                cv_model = torch.nn.Sequential(*list(cv_model.children())[:-1])
            elif model_name == "resnet18":
                cv_model = models.resnet18(pretrained=True)
                cv_model = torch.nn.Sequential(*list(cv_model.children())[:-1])
            else:
                # 預設使用 ResNet50
                cv_model = models.resnet50(pretrained=True)
                cv_model = torch.nn.Sequential(*list(cv_model.children())[:-1])
        
        # 設定為評估模式
        cv_model.eval()
        
        # 設定圖像轉換
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        return cv_model
    except Exception as e:
        print(f"載入CV模型時出錯: {str(e)}")
        return None

def get_image_features(image_path, model_path=None):
    """提取圖片特徵
    
    Args:
        image_path (str): 圖片路徑
        model_path (str, optional): 模型路徑，用於首次載入
        
    Returns:
        np.ndarray: 圖片特徵向量
    """
    global cv_model, transform
    
    if not cv_model:
        cv_model = load_model(model_path)
    
    if not cv_model:
        print("未載入CV模型，無法提取圖片特徵")
        return None
    
    try:
        # 確保圖片存在
        if not os.path.exists(image_path):
            print(f"圖片不存在: {image_path}")
            return None
            
        # 載入並處理圖片
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)  # 增加批次維度
        
        # 提取特徵
        with torch.no_grad():
            features = cv_model(image_tensor)
            
        # 轉換為NumPy並扁平化
        features = features.squeeze().flatten().numpy()
        
        return features
    except Exception as e:
        print(f"提取圖片特徵時出錯: {str(e)}")
        return None
    
def search_by_image(image_path, memes_image_features, top_k=5):
    """基於圖片搜尋最相似的梗圖
    
    Args:
        image_path (str): 查詢圖片的路徑
        memes_image_features (list): 梗圖圖片特徵列表，每個元素是 (meme_id, image_features) 元組
        top_k (int): 返回前 k 個結果
        
    Returns:
        list: 包含 (meme_id, 相似度分數) 元組的列表，按相似度從高到低排序
    """
    if not image_path or not memes_image_features:
        return []
    
    query_features = get_image_features(image_path)
    if query_features is None:
        return []
    
    results = []
    for meme_id, features in memes_image_features:
        if features is None:
            continue
            
        # 計算餘弦相似度
        similarity = cosine_similarity(query_features, np.array(features))
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