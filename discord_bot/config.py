import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Discord相關設定
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
DISCORD_PREFIX = os.getenv('DISCORD_PREFIX', '!')

# API設定
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
API_MEMES_ENDPOINT = f"{API_BASE_URL}/api/memes/"
API_INTERACTION_ENDPOINT = f"{API_BASE_URL}/api/interactions/"

# 文件存儲路徑
TEMP_DIR = os.getenv('TEMP_DIR', 'temp')

# 確保臨時目錄存在
os.makedirs(TEMP_DIR, exist_ok=True)

# 機器人設定
MAX_RESULTS = int(os.getenv('MAX_RESULTS', '5'))
TEXT_WEIGHT = float(os.getenv('TEXT_WEIGHT', '0.6'))
IMAGE_WEIGHT = float(os.getenv('IMAGE_WEIGHT', '0.4'))

# 快取設定
CACHE_DURATION = int(os.getenv('CACHE_DURATION', '3600'))  # 快取持續時間（秒）

# Discord訊息設定
HELP_MESSAGE = """
**海綿寶寶梗圖推薦機器人**

可用指令:
🔸 `{prefix}meme <文字描述>` - 透過文字找尋相關梗圖
🔸 `{prefix}meme` (附加圖片) - 透過圖片找尋相似梗圖
🔸 `{prefix}meme <文字描述>` (附加圖片) - 同時使用文字和圖片搜尋
🔸 `{prefix}categories` - 列出所有可用的梗圖類別
🔸 `{prefix}browse <類別>` - 瀏覽特定類別的梗圖
🔸 `{prefix}help` - 顯示此幫助訊息

範例:
🔹 `{prefix}meme 我很慌張`
🔹 `{prefix}browse 驚訝表情`
"""

NO_MEMES_FOUND = "抱歉，找不到相關的梗圖 😢"
ERROR_MESSAGE = "處理請求時發生錯誤 🔧"
LOADING_MESSAGE = "正在尋找最佳的海綿寶寶梗圖，請稍候... 🔍"
CATEGORIES_HEADER = "**可用的梗圖類別:**\n"