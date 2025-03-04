# 海綿寶寶梗圖推薦機器人技術手冊

## 一、專案概述

本專案旨在開發一個基於自然語言處理（NLP）和計算機視覺（CV）的AI聊天機器人，能夠根據使用者輸入的文字或圖片，推薦最相似的海綿寶寶梗圖。系統進行語義分析，並提取圖片特徵，進行高效檢索。精準匹配網路文化中的幽默與情境，提升使用者的互動體驗。系統包含Discord聊天機器人前端和Django管理後台兩大部分。

## 二、系統架構

### 1. 整體架構

```
SpongeBob-Meme-Bot/
├── discord_bot/        # Discord機器人實現
│   ├── bot.py          # 機器人主程式
│   ├── config.py       # 機器人設定
│   └── utils.py        # 工具函數
├── models/             # AI模型
│   ├── nlp_model.py    # 文字分析模型
│   ├── cv_model.py     # 圖片分析模型
│   └── similarity.py   # 相似度計算
├── meme_django/        # Django管理平台
│   ├── manage.py
│   ├── meme_django/    # Django設定
│   └── meme_manager/   # 梗圖管理應用
├── data/               # 資料存放
│   └── memes/          # 梗圖資料夾
└── requirements.txt    # 專案依賴
```

### 2. 核心功能模組

- **Discord機器人**：負責與用戶互動，接收文字/圖片輸入，回傳推薦梗圖
- **Django管理平台**：提供梗圖、類別管理、模型配置與數據分析
- **NLP模型**：處理文字輸入，提取語義特徵
- **CV模型**：處理圖片輸入，提取視覺特徵
- **相似度計算**：融合文字與圖片特徵，推薦最相似梗圖

## 三、安裝與配置

### 1. 系統需求

- Python 3.8+
- SQLite3
- CUDA支援（可選，用於加速模型運算）

### 2. 安裝步驟

1. 克隆代碼庫：

```bash
git clone https://github.com/yourusername/SpongeBob-Meme-Bot.git
cd SpongeBob-Meme-Bot
```

2. 創建並啟用虛擬環境：

```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate
```

3. 安裝依賴：

```bash
pip install -r requirements.txt
```

4. 配置環境變數：
   
創建`.env`文件，填入以下內容：

```
DISCORD_TOKEN=your_discord_bot_token
DISCORD_PREFIX=!
API_BASE_URL=http://localhost:8000
```

5. 初始化Django資料庫：

```bash
cd meme_django
python manage.py migrate
python manage.py createsuperuser
```

6. 運行Django服務：

```bash
python manage.py runserver
```

7. 啟動Discord機器人：

```bash
cd ..
python -m discord_bot.bot
```

## 四、系統組件詳解

### 1. 模型系統

#### NLP模型

採用基於Transformer的BERT變體，支援多語言處理，可從文字輸入中提取語義表示。預設使用`distilbert-base-multilingual-cased`，也支援自定義模型。

主要功能：
- 文字嵌入向量生成
- 基於餘弦相似度的文字搜尋

#### CV模型

採用預訓練的ResNet模型，提取圖片特徵。預設使用`resnet50`，也支援其他預訓練模型或自定義模型。

主要功能：
- 圖片特徵提取
- 基於特徵向量的圖片搜尋

#### 相似度計算

融合NLP與CV模型的輸出，根據配置的權重進行加權組合，找出最相似的梗圖。

### 2. Django管理平台

#### 資料模型

- `MemeCategory`：梗圖類別
- `Meme`：梗圖信息，包含標題、圖片、類別、關鍵字、嵌入向量等
- `UserInteraction`：用戶互動記錄
- `ModelConfiguration`：模型配置

#### 功能模組

- **梗圖管理**：新增、編輯、刪除梗圖，生成嵌入向量
- **類別管理**：管理梗圖分類
- **模型配置**：設置NLP與CV模型參數
- **互動記錄**：查看用戶使用情況
- **API接口**：與Discord機器人通信

### 3. Discord機器人

#### 指令系統

- `!meme <文字描述>`：根據文字找出相似梗圖
- `!meme <附加圖片>`：根據圖片找出相似梗圖
- `!meme <文字描述> <附加圖片>`：同時使用文字和圖片搜尋
- `!categories`：列出所有可用的梗圖類別
- `!browse <類別>`：瀏覽特定類別的梗圖
- `!help`：顯示幫助訊息

#### 流程說明

1. 用戶發送指令與輸入內容
2. 機器人處理輸入，發送至API獲取梗圖資料
3. 使用AI模型計算相似度，找出最匹配梗圖
4. 生成嵌入式訊息回應用戶，記錄互動

## 五、API參考

### Django API接口

1. `GET /api/memes/`：獲取所有梗圖
   - 參數：`category` (可選) - 過濾特定類別的梗圖
   - 返回：梗圖列表，包含ID、標題、URL、向量等

2. `POST /api/interactions/`：記錄用戶互動
   - 參數：
     - `user_id`：用戶ID
     - `input_text`：輸入文字 (可選)
     - `input_image`：是否有圖片輸入
     - `recommended_meme_id`：推薦的梗圖ID

## 六、維護與擴展

### 1. 添加新梗圖

1. 登入Django管理頁面
2. 點擊"梗圖管理"->"新增梗圖"
3. 上傳圖片、填寫標題、選擇類別、添加關鍵字
4. 系統自動生成嵌入向量

### 2. 更新模型

1. 登入Django管理頁面
2. 進入"模型設定"
3. 添加新的模型配置，指定模型路徑
4. 啟用新模型配置
5. 重新生成梗圖嵌入向量

### 3. 自定義標籤和數據分析

1. 使用Django管理平台的"互動記錄"
2. 分析用戶輸入與推薦結果
3. 根據結果優化關鍵字和梗圖描述

## 七、故障排除

### 常見問題

1. **嵌入向量生成失敗**
   - 檢查模型路徑是否正確
   - 確認是否有足夠記憶體運行模型
   - 檢查GPU驅動是否正確安裝

2. **Discord機器人無法連接**
   - 確認TOKEN是否正確
   - 檢查機器人權限設置
   - 確認網絡連接

3. **圖片搜尋效果不佳**
   - 增加更多關鍵字描述
   - 調整NLP與CV權重
   - 考慮使用更高性能的模型

## 八、未來發展方向

1. **模型優化**：針對梗圖特性微調NLP及CV模型
2. **多模態融合**：強化文字與圖片特徵的融合算法
3. **用戶反饋機制**：增加反饋按鈕，優化推薦算法
4. **擴展平台支持**：支援LINE、Telegram等其他平台
5. **自動標籤生成**：自動為梗圖生成描述與關鍵字

## 九、結語

本專案提供了一個完整的海綿寶寶梗圖推薦系統，包含AI模型、管理平台與用戶介面。系統設計注重擴展性與易用性，可輕鬆添加新功能與優化。通過持續更新梗圖庫與調整模型，可為用戶提供日益精準的梗圖推薦服務。