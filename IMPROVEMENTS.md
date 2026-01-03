# Kabigon 改進建議

最後更新：2026-01-03

## 📊 現況

- **測試覆蓋率**: 38% (373 statements, 230 missing)
- **Python 版本**: 3.12+
- **測試檔案**: 2 個 (test_hello.py, test_youtube_ytdlp.py)
- **範例檔案**: 3 個 (ptt.py, twitter.py, read_reddit.py)

## 🧪 測試改進 (優先度：高)

### 覆蓋率不足的模組

| 模組 | 覆蓋率 | 缺失行數 | 優先度 |
|------|--------|----------|--------|
| cli.py | 0% | 15 | 🔴 高 |
| compose.py | 21% | 23 | 🔴 高 |
| playwright.py | 19% | 35 | 🔴 高 |
| reddit.py | 27% | 30 | 🟡 中 |
| ytdlp.py | 29% | 24 | 🟡 中 |
| utils.py | 32% | 13 | 🟡 中 |
| pdf.py | 36% | 25 | 🟡 中 |
| reel.py | 40% | 12 | 🟢 低 |
| firecrawl.py | 41% | 10 | 🟢 低 |

### 具體測試項目

#### 1. CLI 測試 (tests/test_cli.py)
```python
# 需要測試的項目:
- [x] CLI 參數解析
- [ ] 預設 loader 鏈是否正確
- [ ] 錯誤處理 (無效 URL、網路錯誤等)
- [ ] 輸出格式
```

#### 2. Compose 測試 (tests/test_compose.py)
```python
# 需要測試的項目:
- [ ] Loader 鏈按順序嘗試
- [ ] 第一個成功的 loader 返回結果
- [ ] 所有 loader 失敗時拋出例外
- [ ] Logging 是否正確記錄失敗
- [ ] 空 loader 列表處理
```

#### 3. PlaywrightLoader 測試 (tests/test_playwright.py)
```python
# 需要測試的項目:
- [ ] 基本頁面載入
- [ ] Timeout 處理
- [ ] JavaScript 渲染頁面
- [ ] 同步/異步版本一致性
- [ ] User agent 設定
```

#### 4. RedditLoader 測試 (tests/test_reddit.py)
```python
# 需要測試的項目:
- [ ] URL 轉換為 old.reddit.com
- [ ] 域名驗證 (reddit.com, www.reddit.com, old.reddit.com)
- [ ] 非 Reddit URL 拋出 ValueError
- [ ] 同步/異步版本
- [ ] 實際內容提取 (可用 mock)
```

#### 5. 整合測試 (tests/test_integration.py)
```python
# 需要測試的項目:
- [ ] 不同 URL 類型路由到正確的 loader
- [ ] Fallback 機制 (domain-specific -> generic)
- [ ] 並行處理多個 URL
```

## 📚 文檔改進 (優先度：中)

### README.md 擴充

#### 需要加入的內容:
- [ ] **Badges**: PyPI version, CI status, codecov, license
- [ ] **功能特色**: 列出支援的平台和特殊功能
- [ ] **安裝選項**: 完整版 vs 輕量版 (如果實作 optional dependencies)
- [ ] **詳細使用範例**:
  - [ ] 各種 URL 類型範例 (YouTube, Instagram, Reddit, Twitter, PDF)
  - [ ] 自訂 loader 鏈範例
  - [ ] Async 用法範例
  - [ ] 批次處理範例
- [ ] **Loader 說明表格**: 每個 loader 的適用場景和依賴
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

目前範例: ptt.py, twitter.py, read_reddit.py

建議新增:
- [ ] `examples/youtube_video.py` - YouTube 影片轉文字
- [ ] `examples/pdf_local.py` - 本地 PDF 處理
- [ ] `examples/pdf_url.py` - 線上 PDF 處理
- [ ] `examples/async_batch.py` - 批次異步處理多個 URL
- [ ] `examples/custom_loader.py` - 如何自訂 loader
- [ ] `examples/error_handling.py` - 錯誤處理範例

## 🔧 功能改進 (優先度：中-低)

### 1. RedditLoader 整合到 CLI (優先度：中)

**現況**: RedditLoader 已實作但未加入 cli.py 預設鏈

**選項**:
- [ ] A. 加入預設鏈 (需評估位置和效能)
- [ ] B. 維持現狀，僅供程式化使用
- [ ] C. 透過環境變數或 config 讓使用者選擇

**建議**: 先評估效能影響，如果不顯著則加入

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

### Phase 1: 測試基礎建設 (1-2 週)
1. ✅ 補充 Compose 測試
2. ✅ 補充 CLI 測試
3. ✅ 補充 PlaywrightLoader 測試
4. ⏸️ 目標: 覆蓋率達到 60%+

### Phase 2: 文檔完善 (1 週)
1. ⏸️ 擴充 README
2. ⏸️ 新增更多範例
3. ⏸️ 設定 MkDocs (optional)

### Phase 3: 功能增強 (2-3 週)
1. ⏸️ CLI 功能擴充 (批次、輸出格式)
2. ⏸️ 錯誤處理改進
3. ⏸️ RedditLoader 整合評估

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
