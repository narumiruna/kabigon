# Kabigon 改進建議

最後更新：2026-01-21

## 📊 現況

- **測試覆蓋率**: 69% (359 statements, 113 missing)
- **Python 版本**: 3.12+
- **測試檔案**: 3 個 (test_truthsocial.py, test_youtube.py, test_load_url.py)
- **測試數量**: 37 個測試全部通過
- **範例檔案**: 7 個
- **文檔**: README.md, CLAUDE.md

## 🎯 下一步優先事項

### 高優先度 🔴
1. **CLI 測試** - 目前 0% 覆蓋率
2. **Utils 測試** - 僅 32% 覆蓋率，html_to_markdown 是核心功能
3. **覆蓋率目標** - 從 69% 提升到 75%+

### 中優先度 🟡
4. **PDF/Ytdlp/Firecrawl 測試** - 提升到 60%+ 覆蓋率
5. **CLI 功能擴充** - 批次處理、輸出格式選擇

### 低優先度 🟢
6. **效能優化** - Playwright 瀏覽器重用、並行處理
7. **Optional dependencies** - 輕量版安裝選項
8. **快取機制** - 基於 URL hash 的快取

## 🧪 測試改進 (優先度：高)

| 模組 | 覆蓋率 | 缺失行數 | 優先度 | 狀態 |
|------|--------|----------|--------|------|
| cli.py | 0% | 8 | 🔴 高 | 未測試 |
| utils.py | 32% | 13 | 🔴 高 | 待改進 |
| firecrawl.py | 40% | 9 | 🟡 中 | 待改進 |
| ytdlp.py | 41% | 20 | 🟡 中 | 待改進 |
| pdf.py | 55% | 14 | 🟡 中 | 待改進 |

### 1. CLI 測試 (tests/test_cli.py) - 0% 覆蓋率 🔴
```python
# 需要測試的項目:
- [ ] CLI 參數解析
- [ ] 預設 loader 鏈是否正確
- [ ] 錯誤處理 (無效 URL、網路錯誤等)
- [ ] 輸出格式
```

### 2. Utils 測試 (tests/loaders/test_utils.py) - 32% 覆蓋率 🔴
```python
# 需要測試的項目:
- [ ] html_to_markdown 轉換
- [ ] 各種 HTML 元素處理
- [ ] 邊界情況處理
```

### 3. Compose 測試 - 71% 覆蓋率 🟢
```python
# 仍需測試的項目:
- [ ] 空 result 處理邏輯 (lines 15-20)
- [ ] 更多錯誤情境
```

## 📚 文檔改進 (優先度：中)

### README.md
- [ ] **安裝選項**: 完整版 vs 輕量版 (optional dependencies)
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
建議新增:
- [ ] `examples/youtube_video.py` - YouTube 影片轉文字
- [ ] `examples/pdf_local.py` - 本地 PDF 處理
- [ ] `examples/pdf_url.py` - 線上 PDF 處理
- [ ] `examples/async_batch.py` - 批次異步處理多個 URL
- [ ] `examples/custom_loader.py` - 如何自訂 loader
- [ ] `examples/error_handling.py` - 錯誤處理範例

## 🔧 功能改進 (優先度：中-低)

### CLI 功能擴充

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

## 🚀 DevOps 改進 (優先度：低)

### CI/CD 改進
- [ ] **多版本 Python 測試**: 3.12 / 3.13
- [ ] **Coverage 閾值檢查**
- [ ] **效能回歸測試**

### 依賴管理
- [ ] **Optional Dependencies**: full / lite
- [ ] **安裝選項**: `pip install kabigon[full]`

### Release Process
- [ ] **自動化 Release Notes**
- [ ] **Pre-release 版本**

## 🐛 已知問題

### 待確認
- [ ] 是否所有 loader 的 async_load 都正確實作？
- [ ] Playwright browser 關閉是否正確？(resource leak)
- [ ] Windows/macOS 相容性測試
- [ ] 大檔案處理的記憶體使用

### Type Hints
- [ ] ty check 持續保持通過
