import os
import time
import requests
import json
import tempfile
from io import BytesIO
from PIL import Image
import discord
from discord.ext import commands
import sys
import aiohttp
import asyncio

# 添加專案路徑，以便匯入其他模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config import API_MEMES_ENDPOINT, API_INTERACTION_ENDPOINT, TEMP_DIR

# 全域變數用於快取資料
_memes_cache = None
_categories_cache = None
_last_cache_time = 0
_cache_duration = 3600  # 快取持續時間（秒）

async def fetch_memes(category=None, force_refresh=False):
    """從API獲取梗圖列表
    
    Args:
        category (str, optional): 梗圖類別
        force_refresh (bool): 是否強制重新獲取
        
    Returns:
        list: 梗圖列表
    """
    global _memes_cache, _last_cache_time
    
    # 判斷是否需要重新獲取
    current_time = time.time()
    if not force_refresh and _memes_cache and (current_time - _last_cache_time) < _cache_duration:
        # 使用快取資料
        if category:
            return [meme for meme in _memes_cache if meme.get('category') == category]
        return _memes_cache
    
    # 構建API請求URL
    url = API_MEMES_ENDPOINT
    if category:
        url += f"?category={category}"
    
    print(f"獲取梗圖列表: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    memes = data.get('memes', [])
                    
                    # 打印偵錯訊息
                    print(f"獲取到 {len(memes)} 個梗圖")
                    
                    # 更新快取
                    if not category:
                        _memes_cache = memes
                        _last_cache_time = current_time
                    
                    return memes
                else:
                    print(f"獲取梗圖失敗: HTTP {response.status}")
                    return _memes_cache if _memes_cache else []
    except Exception as e:
        print(f"獲取梗圖出錯: {str(e)}")
        return _memes_cache if _memes_cache else []
async def fetch_categories(force_refresh=False):
    """獲取所有梗圖類別
    
    Args:
        force_refresh (bool): 是否強制重新獲取
        
    Returns:
        list: 類別列表
    """
    global _categories_cache, _last_cache_time
    
    # 判斷是否需要重新獲取
    current_time = time.time()
    if not force_refresh and _categories_cache and (current_time - _last_cache_time) < _cache_duration:
        # 使用快取資料
        return _categories_cache
    
    # 獲取所有梗圖
    memes = await fetch_memes(force_refresh=force_refresh)
    
    # 提取類別
    categories = list(set(meme.get('category') for meme in memes if meme.get('category')))
    categories.sort()
    
    # 更新快取
    _categories_cache = categories
    
    return categories

async def download_image(url, save_path=None):
    """下載圖片
    
    Args:
        url (str): 圖片URL
        save_path (str, optional): 儲存路徑
        
    Returns:
        str: 圖片路徑或二進制數據
    """
    if not url:
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    
                    if save_path:
                        # 確保目錄存在
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        
                        # 寫入文件
                        with open(save_path, 'wb') as f:
                            f.write(data)
                        return save_path
                    else:
                        return data
                else:
                    print(f"下載圖片失敗: {response.status}")
                    return None
    except Exception as e:
        print(f"下載圖片出錯: {str(e)}")
        return None

async def get_meme_by_id(meme_id):
    """根據ID獲取梗圖
    
    Args:
        meme_id (int): 梗圖ID
        
    Returns:
        dict: 梗圖資訊
    """
    memes = await fetch_memes()
    for meme in memes:
        if meme.get('id') == meme_id:
            return meme
    return None

async def save_discord_attachment(attachment):
    """將Discord附件保存為臨時文件
    
    Args:
        attachment (discord.Attachment): Discord附件
        
    Returns:
        str: 保存的臨時文件路徑
    """
    if not attachment:
        return None
    
    try:
        # 建立臨時文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', dir=TEMP_DIR)
        temp_path = temp_file.name
        temp_file.close()
        
        # 下載附件
        await attachment.save(temp_path)
        
        return temp_path
    except Exception as e:
        print(f"保存附件出錯: {str(e)}")
        return None

async def record_interaction(user_id, input_text, input_image, recommended_meme_id):
    """記錄使用者互動
    
    Args:
        user_id (str): 使用者ID
        input_text (str): 輸入文字
        input_image (bool): 是否有輸入圖片
        recommended_meme_id (int): 推薦的梗圖ID
    """
    try:
        payload = {
            'user_id': str(user_id),
            'input_text': input_text,
            'input_image': input_image,
            'recommended_meme_id': recommended_meme_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(API_INTERACTION_ENDPOINT, json=payload) as response:
                if response.status != 200:
                    print(f"記錄互動失敗: {response.status}")
    except Exception as e:
        print(f"記錄互動出錯: {str(e)}")

async def create_embeds_from_memes(memes, title="推薦梗圖", color=0x00BFFF):
    """從梗圖列表創建Discord嵌入消息
    
    Args:
        memes (list): 梗圖列表
        title (str): 嵌入標題
        color (int): 嵌入顏色
        
    Returns:
        list: Discord嵌入消息列表
    """
    embeds = []
    
    for i, meme in enumerate(memes):
        embed = discord.Embed(
            title=f"{title} {i+1}/{len(memes)}",
            description=meme.get('title', ''),
            color=color
        )
        
        # 添加分類資訊
        if meme.get('category'):
            embed.add_field(name="分類", value=meme.get('category'), inline=True)
        
        # 添加關鍵字資訊
        if meme.get('keywords'):
            embed.add_field(name="關鍵字", value=meme.get('keywords'), inline=True)
        
        # 設置圖片
        if meme.get('image_url'):
            embed.set_image(url=meme.get('image_url'))
        
        # 添加頁腳
        embed.set_footer(text=f"梗圖ID: {meme.get('id')}")
        
        embeds.append(embed)
    
    return embeds

def create_paginated_embed(entries, title, page=0, entries_per_page=10, color=0x00BFFF):
    """創建分頁嵌入訊息
    
    Args:
        entries (list): 項目列表
        title (str): 嵌入標題
        page (int): 當前頁碼
        entries_per_page (int): 每頁項目數
        color (int): 嵌入顏色
        
    Returns:
        discord.Embed: Discord嵌入消息
    """
    # 計算總頁數
    pages = max(1, (len(entries) + entries_per_page - 1) // entries_per_page)
    page = min(max(0, page), pages - 1)
    
    # 獲取當前頁的項目
    start_idx = page * entries_per_page
    end_idx = min(start_idx + entries_per_page, len(entries))
    current_entries = entries[start_idx:end_idx]
    
    # 創建嵌入消息
    embed = discord.Embed(
        title=title,
        description="\n".join([f"{idx+1}. {entry}" for idx, entry in enumerate(current_entries, start=start_idx)]),
        color=color
    )
    
    # 添加頁腳
    embed.set_footer(text=f"第 {page+1} 頁，共 {pages} 頁")
    
    return embed, page, pages
async def download_image(url, save_path=None):
    """下載圖片
    
    Args:
        url (str): 圖片URL
        save_path (str, optional): 儲存路徑
        
    Returns:
        bytes或str: 圖片二進制數據或保存路徑
    """
    if not url:
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    
                    if save_path:
                        # 確保目錄存在
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        
                        # 寫入文件
                        with open(save_path, 'wb') as f:
                            f.write(data)
                        return save_path
                    else:
                        return data
                else:
                    print(f"下載圖片失敗: {response.status}")
                    return None
    except Exception as e:
        print(f"下載圖片出錯: {str(e)}")
        return None