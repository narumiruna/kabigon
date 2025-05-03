# kabigon

## Installation

```shell
pip install kabigon[all]
playwright install chromium
```

## Usage

```shell
kabigon <url>
```

or

```python
import kabigon

url = "https://www.google.com.tw"

content = kabigon.Compose(
    [
        kabigon.YoutubeLoader(),
        kabigon.ReelLoader(),
        kabigon.YtdlpLoader(),
        kabigon.PDFLoader(),
        # kabigon.HttpxLoader(),
        kabigon.PlaywrightLoader(),
    ]
).load(url)
print(content)
```
