# Kabigon 改進建議

最後更新：2026-01-04

## 🎉 重大進展

**測試覆蓋率從 38% 提升到 69%！** (+31 個百分點)

主要成就:
- ✅ 新增 37 個測試，全部通過
- ✅ RedditLoader 已整合到 CLI 預設鏈
- ✅ TruthSocialLoader 完整實作並整合
- ✅ 新增 CLAUDE.md 改善 AI 協作
- ✅ 7 個使用範例檔案

## 📊 現況

- **測試覆蓋率**: 69% (359 statements, 113 missing) ⬆️ 從 38% 大幅提升
- **Python 版本**: 3.12+
- **測試檔案**: 3 個 (test_truthsocial.py, test_youtube.py, test_load_url.py)
- **測試數量**: 37 個測試全部通過 ✅
- **範例檔案**: 7 個 (async_usage.py, fetch_billgertz_tweet.py, ptt.py, read_reddit.py, simple_usage.py, twitter.py, truthsocial.py)
- **文檔**: README.md ✅, CLAUDE.md ✅

## 🎯 下一步優先事項

### 高優先度 🔴
1. **CLI 測試** - 目前 0% 覆蓋率，應優先補上
2. **Utils 測試** - 僅 32% 覆蓋率，html_to_markdown 是核心功能
3. **覆蓋率目標** - 從 69% 提升到 75%+

### 中優先度 🟡
4. **PDF/Ytdlp/Firecrawl 測試** - 提升到 60%+ 覆蓋率
5. **Troubleshooting 文檔** - 新增常見問題解決方案
6. **錯誤處理改進** - 更詳細的錯誤訊息和自訂例外

### 低優先度 🟢
7. **CLI 功能擴充** - 批次處理、輸出格式選擇
8. **效能優化** - Playwright 瀏覽器重用、並行處理
9. **Optional dependencies** - 輕量版安裝選項

## 🧪 測試改進 (優先度：高)

### 覆蓋率不足的模組

| 模組 | 覆蓋率 | 缺失行數 | 優先度 | 狀態 |
|------|--------|----------|--------|------|
| cli.py | 0% | 8 | 🔴 高 | 未測試 |
| utils.py | 32% | 13 | 🔴 高 | 待改進 |
| firecrawl.py | 40% | 9 | 🟡 中 | 待改進 |
| ytdlp.py | 41% | 20 | 🟡 中 | 待改進 |
| pdf.py | 55% | 14 | 🟡 中 | 已改善 |
| reddit.py | 61% | 11 | 🟢 低 | 已改善 |
| httpx.py | 64% | 4 | 🟢 低 | 良好 |
| truthsocial.py | 65% | 8 | 🟢 低 | 良好 |
| compose.py | 71% | 5 | 🟢 低 | 良好 |
| api.py | 78% | 2 | ✅ 優秀 | - |
| reel.py | 80% | 3 | ✅ 優秀 | - |
| twitter.py | 82% | 3 | ✅ 優秀 | - |
| playwright.py | 83% | 4 | ✅ 優秀 | - |
| youtube.py | 88% | 7 | ✅ 優秀 | - |
| youtube_ytdlp.py | 89% | 1 | ✅ 優秀 | - |
| ptt.py | 92% | 1 | ✅ 優秀 | - |

**已達到 100% 覆蓋率的模組**:
- ✅ `__init__.py`
- ✅ `core/__init__.py`
- ✅ `core/exception.py`
- ✅ `core/loader.py`
- ✅ `loaders/__init__.py`

### 具體測試項目

#### 1. CLI 測試 (tests/test_cli.py) - 0% 覆蓋率 🔴
```python
# 需要測試的項目:
- [ ] CLI 參數解析
- [ ] 預設 loader 鏈是否正確
- [ ] 錯誤處理 (無效 URL、網路錯誤等)
- [ ] 輸出格式
```

#### 2. ✅ YouTube 測試 (tests/loaders/test_youtube.py) - 已完成
- ✅ 26 個測試全部通過
- ✅ URL 解析與驗證
- ✅ Video ID 提取
- ✅ 各種 YouTube URL 格式支援

#### 3. ✅ TruthSocial 測試 (tests/loaders/test_truthsocial.py) - 已完成
- ✅ 7 個測試全部通過
- ✅ URL 驗證
- ✅ Domain 檢查

#### 4. ✅ 整合測試 (tests/test_load_url.py) - 已完成
- ✅ 4 個測試全部通過
- ✅ load_url 和 load_url_sync API 測試

#### 5. Utils 測試 (tests/loaders/test_utils.py) - 32% 覆蓋率 🔴
```python
# 需要測試的項目:
- [ ] html_to_markdown 轉換
- [ ] 各種 HTML 元素處理
- [ ] 邊界情況處理
```

#### 6. Compose 測試 - 71% 覆蓋率 🟢
```python
# 仍需測試的項目:
- [ ] 空 result 處理邏輯 (lines 15-20)
- [ ] 更多錯誤情境
```

#### 7. PDF/Ytdlp/Firecrawl 測試 - 待加強
- PDFLoader: 55% 覆蓋率
- YtdlpLoader: 41% 覆蓋率
- FirecrawlLoader: 40% 覆蓋率

## 📚 文檔改進 (優先度：中)

### README.md 擴充

#### 需要加入的內容:
- [x] **Badges**: PyPI version, Python version, codecov, license
- [x] **功能特色**: 列出支援的平台和特殊功能
- [ ] **安裝選項**: 完整版 vs 輕量版 (如果實作 optional dependencies)
- [x] **詳細使用範例**:
  - [x] 各種 URL 類型範例 (YouTube, Instagram, Reddit, Twitter, PDF) ✅ 已有
  - [x] 自訂 loader 鏈範例 ✅ 已有
  - [x] Async 用法範例 ✅ 已有
  - [x] 批次處理範例 ✅ 已有
- [x] **Loader 說明表格**: 每個 loader 的適用場景 ✅ 已有
- [ ] **Troubleshooting**: 常見問題和解決方案
  - Playwright browser 未安裝
  - FFmpeg 未安裝
  - CAPTCHA 問題
  - Timeout 問題
- [ ] **貢獻指南**: 如何新增 loader、如何測試

### API 文檔

- [ ] **考慮使用 MkDocs 或 Sphinx**
  - 自動從 docstring 生成 API 文檔
  - 部署到 GitHub Pages 或 ReadTheDocs
- [ ] **每個 Loader 的詳細文檔**:
  - 參數說明
  - 返回值格式
  - 使用範例
  - 限制和注意事項

### 更多範例檔案

目前範例 (7 個):
- ✅ `async_usage.py` - Async 使用範例
- ✅ `fetch_billgertz_tweet.py` - 推特爬取範例
- ✅ `ptt.py` - PTT 論壇範例
- ✅ `read_reddit.py` - Reddit 範例
- ✅ `simple_usage.py` - 簡單使用範例
- ✅ `twitter.py` - Twitter 範例
- ✅ `truthsocial.py` - Truth Social 範例

建議新增:
- [ ] `examples/youtube_video.py` - YouTube 影片轉文字
- [ ] `examples/pdf_local.py` - 本地 PDF 處理
- [ ] `examples/pdf_url.py` - 線上 PDF 處理
- [ ] `examples/async_batch.py` - 批次異步處理多個 URL (可能已由 async_usage.py 涵蓋)
- [ ] `examples/custom_loader.py` - 如何自訂 loader
- [ ] `examples/error_handling.py` - 錯誤處理範例

## 🔧 功能改進 (優先度：中-低)

### 1. ✅ RedditLoader 整合到 CLI - 已完成

**現況**: ✅ RedditLoader 已加入 CLI 預設鏈 (src/kabigon/api.py)

**Loader 順序** (api.py:10-23):
1. PttLoader
2. TwitterLoader
3. TruthSocialLoader
4. **RedditLoader** ✅ 已整合
5. YoutubeLoader
6. ReelLoader
7. YoutubeYtdlpLoader
8. PDFLoader
9. PlaywrightLoader (2 個: networkidle + 快速 fallback)

### 2. 錯誤處理改進 (優先度：中)

- [ ] **更詳細的錯誤訊息**:
  - 哪個 loader 失敗了？為什麼失敗？
  - 建議使用者採取的行動
- [ ] **更好的 Logging**:
  - 目前只在 Compose 層記錄失敗
  - 各 loader 應該有更詳細的 debug log
- [ ] **自訂例外類別**:
  - `LoaderNotApplicableError`: URL 不適用此 loader
  - `LoaderTimeoutError`: Timeout
  - `LoaderContentError`: 內容提取失敗

### 3. 快取機制 (優先度：低)

- [ ] **避免重複下載**:
  - 基於 URL hash 的快取
  - 可設定過期時間
  - 可選擇性啟用/停用
- [ ] **實作選項**:
  - 記憶體快取 (functools.lru_cache)
  - 檔案快取 (diskcache)
  - Redis 快取 (進階)

### 4. CLI 功能擴充 (優先度：中)

#### 批次處理
```bash
# 從檔案讀取 URL 列表
kabigon --input urls.txt --output results/

# 從 stdin
cat urls.txt | kabigon --batch
```

#### 輸出格式選擇
```bash
# Markdown (預設)
kabigon <url>

# Plain text
kabigon --format text <url>

# JSON
kabigon --format json <url>

# 儲存到檔案
kabigon --output result.md <url>
```

#### Verbose 模式
```bash
# 顯示 loader 嘗試過程
kabigon --verbose <url>

# 範例輸出:
# [INFO] Trying PttLoader... failed (not PTT URL)
# [INFO] Trying TwitterLoader... failed (not Twitter URL)
# [INFO] Trying YoutubeLoader... success!
```

#### 指定 Loader
```bash
# 只使用特定 loader
kabigon --loader youtube <url>

# 使用多個指定 loader
kabigon --loader youtube,playwright <url>
```

### 5. 效能優化 (優先度：低)

- [ ] **並行處理多個 URL**:
  - 使用 asyncio.gather
  - 可設定並行數量上限
- [ ] **Playwright 瀏覽器重用**:
  - 目前每次都啟動新瀏覽器
  - 可考慮 context manager 重用 browser instance
- [ ] **依賴延遲載入**:
  - 只在使用時才 import 重量級依賴 (whisper, playwright)

## 🚀 DevOps 改進 (優先度：低)

### CI/CD 改進

**現況**: 已有 python.yml (lint, type check, test, codecov)

改進項目:
- [ ] **多版本 Python 測試**:
  ```yaml
  strategy:
    matrix:
      python-version: ["3.12", "3.13"]
  ```
- [ ] **Coverage 閾值檢查**:
  - 設定最低覆蓋率要求 (例如 60%)
  - PR 不能降低覆蓋率
- [ ] **效能回歸測試**:
  - Benchmark 主要 loader 的執行時間
  - 偵測效能退化

### 依賴管理

- [ ] **Optional Dependencies**:
  ```toml
  [project.optional-dependencies]
  full = ["openai-whisper>=20250625", "firecrawl-py>=2.4.1"]
  lite = []  # 只有基本依賴
  ```
- [ ] **安裝選項**:
  ```bash
  # 輕量版 (只有 HTTP/Playwright)
  pip install kabigon

  # 完整版 (包含 Whisper, Firecrawl)
  pip install kabigon[full]
  ```

### Release Process

- [ ] **自動化 Release Notes**:
  - 從 commit message 生成 changelog
  - 使用 conventional commits
- [ ] **Pre-release 版本**:
  - Beta/RC 版本測試
  - Versioning 策略

## 🐛 已知問題

### 待確認
- [ ] 是否所有 loader 的 async_load 都正確實作？
- [ ] Playwright browser 關閉是否正確？(有無 resource leak)
- [ ] Windows/macOS 相容性測試
- [ ] 大檔案處理的記憶體使用

### Type Hints
✅ 目前 ty check 通過

## 📋 實作優先順序建議

### Phase 1: 測試基礎建設 ✅ 已大幅完成
1. ✅ 補充 YouTube 測試 (26 個測試)
2. ✅ 補充 TruthSocial 測試 (7 個測試)
3. ✅ 補充整合測試 (4 個測試)
4. ✅ 目標: 覆蓋率達到 60%+ → **實際達到 69%** 🎉
5. 🚧 待完成: CLI 測試 (目前 0%)

**成果**: 覆蓋率從 38% 提升到 69%，增加 31 個百分點！

### Phase 2: 文檔完善 🚧 進行中
1. ✅ 擴充 README (已有詳細範例和使用說明)
2. ✅ 新增更多範例 (7 個範例檔案)
3. ✅ 新增 CLAUDE.md (AI 協作文檔)
4. ⏸️ 設定 MkDocs (optional)
5. ⏸️ 新增 Troubleshooting 章節

### Phase 3: 功能增強 🚧 部分完成
1. ⏸️ CLI 功能擴充 (批次、輸出格式)
2. ⏸️ 錯誤處理改進
3. ✅ RedditLoader 整合 → **已完成並加入預設鏈**
4. ✅ TruthSocialLoader 實作 → **已完成並加入預設鏈**

### Phase 4: 優化與進階功能 (持續)
1. ⏸️ 快取機制
2. ⏸️ 效能優化
3. ⏸️ Optional dependencies

---

## 📝 Notes

- 此文件應定期更新進度
- 完成項目標記 ✅
- 進行中項目標記 🚧
- 每個 Phase 完成後更新版本號

## 📈 改進歷史

### 2026-01-04
- ✅ 測試覆蓋率從 38% 提升到 69%
- ✅ 新增 YouTube 測試套件 (26 個測試)
- ✅ 新增 TruthSocial 測試套件 (7 個測試)
- ✅ 新增整合測試 (4 個測試)
- ✅ RedditLoader 已整合到 CLI 預設鏈
- ✅ TruthSocialLoader 完整實作並整合
- ✅ 新增 CLAUDE.md 文檔

### 2026-01-03
- 📝 初始版本建立
- 📊 基準測試覆蓋率: 38%
