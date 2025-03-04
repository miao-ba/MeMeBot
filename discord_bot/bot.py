import os
import sys
import discord
from discord.ext import commands
import asyncio
import tempfile
import aiohttp
import random

# 添加專案路徑，以便匯入其他模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bot.config import (
    DISCORD_TOKEN, DISCORD_PREFIX, MAX_RESULTS, TEXT_WEIGHT, IMAGE_WEIGHT,
    HELP_MESSAGE, NO_MEMES_FOUND, ERROR_MESSAGE, LOADING_MESSAGE, CATEGORIES_HEADER
)

from discord_bot.utils import (
    fetch_memes, fetch_categories, get_meme_by_id, save_discord_attachment,
    record_interaction, create_embeds_from_memes, create_paginated_embed
)

from models.similarity import recommend_memes

# 設置意圖
intents = discord.Intents.default()
intents.message_content = True

# 創建機器人
# 創建機器人
bot = commands.Bot(command_prefix=DISCORD_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    """機器人啟動時的事件處理"""
    print(f"機器人已登入：{bot.user.name} ({bot.user.id})")
    print(f"使用前綴：{DISCORD_PREFIX}")
    
    # 設置機器人活動狀態
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{DISCORD_PREFIX}help 來獲得幫助"
    ))
    
    # 預熱快取
    try:
        print("正在預熱梗圖快取...")
        await fetch_memes(force_refresh=True)
        await fetch_categories(force_refresh=True)
        print("快取預熱完成")
    except Exception as e:
        print(f"快取預熱出錯: {str(e)}")
        
    # 設定定期更新快取的任務
    bot.loop.create_task(refresh_cache_periodically())
    
async def refresh_cache_periodically():
    """定期更新快取的任務"""
    while True:
        try:
            # 每60秒重新整理一次快取
            await asyncio.sleep(60)
            await fetch_memes(force_refresh=True)
            await fetch_categories(force_refresh=True)
            print("快取已重新整理")
        except Exception as e:
            print(f"定期重新整理快取時出錯: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    """指令錯誤處理"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    error_message = f"執行指令時出錯: {str(error)}"
    print(error_message)
    
    await ctx.send(ERROR_MESSAGE)

@bot.command(name="help")
async def help_command(ctx):
    """顯示幫助訊息"""
    help_text = HELP_MESSAGE.format(prefix=DISCORD_PREFIX)
    await ctx.send(help_text)

@bot.command(name="meme")
async def meme_command(ctx, *, query=None):
    """推薦海綿寶寶梗圖
    
    使用方式:
        !meme <文字描述> - 透過文字找尋相關梗圖
        !meme (附加圖片) - 透過圖片找尋相似梗圖
        !meme <文字描述> (附加圖片) - 同時使用文字和圖片搜尋
    """
    # 發送載入訊息
    loading_message = await ctx.send(LOADING_MESSAGE)
    
    try:
        # 檢查是否有圖片附件
        image_file = None
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.content_type.startswith('image/'):
                    image_file = await save_discord_attachment(attachment)
                    break
        
        # 獲取梗圖列表 - 使用force_refresh確保獲取最新資料
        memes = await fetch_memes(force_refresh=True)
        
        # 如果沒有梗圖，返回錯誤
        if not memes:
            await loading_message.edit(content=ERROR_MESSAGE)
            return
        
        # 推薦梗圖 (依照查詢或隨機選擇)
        if query or image_file:
            # 獲取推薦梗圖ID列表
            recommended_ids = recommend_memes(
                query_text=query,
                query_image=image_file,
                memes=memes,
                top_k=1,  # 只取最相似的1個結果
                weight_text=TEXT_WEIGHT
            )
            
            # 獲取推薦梗圖詳細資訊
            if recommended_ids:
                recommended_meme = await get_meme_by_id(recommended_ids[0])
                if not recommended_meme:
                    await loading_message.edit(content=NO_MEMES_FOUND)
                    return
                
                # 處理並發送梗圖
                await send_meme_image(ctx, loading_message, recommended_meme)
                
                # 記錄互動
                await record_interaction(
                    ctx.author.id,
                    query,
                    image_file is not None,
                    recommended_meme.get('id')
                )
            else:
                await loading_message.edit(content=NO_MEMES_FOUND)
        else:
            # 如果沒有查詢條件，隨機推薦一張
            import random
            recommended_meme = random.choice(memes)
            
            # 處理並發送梗圖
            await send_meme_image(ctx, loading_message, recommended_meme)
    
    except Exception as e:
        error_message = f"處理梗圖請求時出錯: {str(e)}"
        print(error_message)
        await loading_message.edit(content=ERROR_MESSAGE)
    
    finally:
        # 清理臨時文件
        if image_file and os.path.exists(image_file):
            try:
                os.unlink(image_file)
            except:
                pass
@bot.command(name="categories")
async def categories_command(ctx):
    """列出所有梗圖類別"""
    try:
        # 獲取類別列表
        categories = await fetch_categories()
        
        if not categories:
            await ctx.send("目前沒有任何梗圖類別。")
            return
        
        # 創建分頁嵌入消息
        embed, page, pages = create_paginated_embed(
            categories,
            CATEGORIES_HEADER.strip(),
            page=0,
            entries_per_page=10
        )
        
        # 如果只有一頁，直接發送
        if pages == 1:
            await ctx.send(embed=embed)
            return
        
        # 創建分頁控制按鈕
        class CategoryView(discord.ui.View):
            def __init__(self, entries, title, timeout=60):
                super().__init__(timeout=timeout)
                self.entries = entries
                self.title = title
                self.page = 0
                self.entries_per_page = 10
                self.pages = pages
            
            @discord.ui.button(label="上一頁", style=discord.ButtonStyle.secondary)
            async def previous_button(self, interaction, button):
                self.page = (self.page - 1) % self.pages
                embed, _, _ = create_paginated_embed(
                    self.entries,
                    self.title,
                    page=self.page,
                    entries_per_page=self.entries_per_page
                )
                await interaction.response.edit_message(embed=embed)
            
            @discord.ui.button(label="下一頁", style=discord.ButtonStyle.primary)
            async def next_button(self, interaction, button):
                self.page = (self.page + 1) % self.pages
                embed, _, _ = create_paginated_embed(
                    self.entries,
                    self.title,
                    page=self.page,
                    entries_per_page=self.entries_per_page
                )
                await interaction.response.edit_message(embed=embed)
            
            async def on_timeout(self):
                # 停用所有按鈕
                for item in self.children:
                    item.disabled = True
                
                # 更新訊息
                message = self.message
                if message:
                    await message.edit(view=self)
        
        # 創建視圖
        view = CategoryView(categories, CATEGORIES_HEADER.strip())
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    except Exception as e:
        error_message = f"獲取類別列表時出錯: {str(e)}"
        print(error_message)
        await ctx.send(ERROR_MESSAGE)

@bot.command(name="browse")
async def browse_command(ctx, *, category=None):
    """瀏覽特定類別的梗圖
    
    使用方式:
        !browse <類別名稱> - 瀏覽指定類別的梗圖
    """
    # 發送載入訊息
    loading_message = await ctx.send(LOADING_MESSAGE)
    
    try:
        if not category:
            await loading_message.edit(content="請指定要瀏覽的類別，使用 `!categories` 查看所有類別。")
            return
        
        # 獲取指定類別的梗圖
        memes = await fetch_memes(category=category, force_refresh=True)
        
        if not memes:
            await loading_message.edit(content=f"找不到類別 '{category}' 的梗圖。")
            return
        
        # 隨機選擇一個梗圖顯示
        recommended_meme = random.choice(memes)
        
        # 處理並發送梗圖
        await send_meme_image(ctx, loading_message, recommended_meme)
        
    except Exception as e:
        error_message = f"瀏覽類別時出錯: {str(e)}"
        print(error_message)
        await loading_message.edit(content=ERROR_MESSAGE)
async def send_meme_image(ctx, loading_message, meme):
    """處理並發送梗圖圖片
    
    Args:
        ctx: Discord命令上下文
        loading_message: 載入中訊息
        meme: 梗圖資訊字典
    """
    image_url = meme.get('image_url')
    if not image_url:
        await loading_message.edit(content=f"找到梗圖但沒有圖片URL: {meme.get('title', '未知')}")
        return
    
    # 確保URL是完整的
    if not image_url.startswith('http'):
        # 假設是相對URL，轉換為絕對URL
        image_url = f"http://127.0.0.1:8000{image_url}"
    
    # 創建臨時檔案來保存圖片
    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_image.close()
    
    try:
        # 直接使用aiohttp下載圖片
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    with open(temp_image.name, 'wb') as f:
                        f.write(await response.read())
                    
                    # 準備發送的訊息文字
                    message_text = f"**{meme.get('title', '')}**"
                    if meme.get('category'):
                        message_text += f"\n分類: {meme.get('category')}"
                    
                    # 發送圖片和訊息
                    await loading_message.delete()
                    await ctx.send(content=message_text, file=discord.File(temp_image.name))
                else:
                    print(f"下載圖片失敗，狀態碼: {response.status}，URL: {image_url}")
                    await loading_message.edit(content=f"無法下載圖片 (HTTP {response.status})")
    except Exception as e:
        print(f"處理圖片時出錯: {str(e)}，URL: {image_url}")
        await loading_message.edit(content=f"處理圖片時出錯: {str(e)[:100]}")
    finally:
        # 清理臨時檔案
        if os.path.exists(temp_image.name):
            os.unlink(temp_image.name)
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
    
    # 確保URL是完整的
    if not url.startswith('http'):
        url = f"http://127.0.0.1:8000{url}"
    
    print(f"正在下載圖片: {url}")
    
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
                    print(f"下載圖片失敗: HTTP {response.status}")
                    return None
    except Exception as e:
        print(f"下載圖片出錯: {str(e)}")
        return None
def run_bot():
    """運行Discord機器人"""
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    run_bot()