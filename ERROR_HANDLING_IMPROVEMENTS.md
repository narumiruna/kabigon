# Error Handling and Logging Improvements

This document describes the error handling and logging improvements made to the Kabigon project.

## Overview

Enhanced error handling and logging across all loaders to provide:
- Better error diagnostics
- More informative error messages
- Actionable suggestions for users
- Detailed logging for debugging

## New Exception Classes

Three new custom exception classes in `kabigon.core.exception`:

### 1. `LoaderNotApplicableError`
- **Purpose**: Indicates that a URL doesn't match a loader's expected format
- **Attributes**: `loader_name`, `url`, `reason`
- **Usage**: Raised when a loader cannot handle a specific URL type
- **Example**: 
  ```python
  raise LoaderNotApplicableError(
      "YoutubeLoader",
      url,
      "Not a YouTube domain"
  )
  ```

### 2. `LoaderTimeoutError`
- **Purpose**: Indicates that a loader operation timed out
- **Attributes**: `loader_name`, `url`, `timeout`, `suggestion`
- **Usage**: Raised when page loading or content fetching exceeds timeout
- **Example**:
  ```python
  raise LoaderTimeoutError(
      "PlaywrightLoader",
      url,
      30.0,
      "Try increasing the timeout or check your network connection."
  )
  ```

### 3. `LoaderContentError`
- **Purpose**: Indicates that content extraction failed
- **Attributes**: `loader_name`, `url`, `reason`, `suggestion`
- **Usage**: Raised when a loader successfully accessed the URL but failed to extract content
- **Example**:
  ```python
  raise LoaderContentError(
      "PDFLoader",
      url,
      "Failed to parse PDF",
      "The PDF may be corrupted or use unsupported features."
  )
  ```

## Enhanced Loaders

### Compose Loader
**Key Improvements:**
- Tracks all loader failures with specific error types
- Generates detailed error summary showing:
  - Which loaders were tried
  - Why each loader failed
  - The specific error for each loader
- Differentiates between expected failures (LoaderNotApplicableError) and unexpected errors

**Example Output:**
```
Failed to load URL: https://example.com/test

Attempted loaders:
  - YoutubeLoader: Not applicable (unsupported URL netloc: example.com)
  - TwitterLoader: Not applicable (Not a Twitter/X URL)
  - RedditLoader: Not applicable (Not a Reddit URL)
```

### Individual Loaders

All loaders now include:

1. **Debug Logging**: Logs start of processing with URL
2. **Success Logging**: Logs successful completion with content size
3. **Error Logging**: Logs failures with reasons
4. **Custom Exceptions**: Use appropriate exception types with helpful messages

**Enhanced Loaders:**
- `YoutubeLoader`: URL validation, transcript fetching, empty content handling
- `TwitterLoader`: Page loading, timeout handling, content extraction
- `PlaywrightLoader`: Generic web page loading with timeout handling
- `PDFLoader`: Local/remote file handling, content-type validation
- `RedditLoader`: URL conversion, networkidle wait, timeout handling
- `TruthSocialLoader`: Long timeout handling for JS-heavy pages
- `HttpxLoader`: HTTP error handling
- `PttLoader`: Taiwan PTT forum URL validation

## Logging Levels

### DEBUG
- URL being processed
- Extracted identifiers (e.g., video IDs)
- Processing steps
- Success messages with content size

### INFO
- Successful loader completion (in Compose)
- Empty results

### WARNING
- Timeout errors
- Content extraction failures
- HTTP errors

### ERROR
- Final failure when all loaders fail (in Compose)
- Critical errors

## Example Usage

### Basic Usage with Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

import kabigon

try:
    content = kabigon.load_url_sync("https://example.com")
except kabigon.LoaderError as e:
    print(f"Failed to load: {e}")
```

### Handling Specific Errors

```python
from kabigon import Compose, YoutubeLoader, LoaderNotApplicableError, LoaderTimeoutError

loader = Compose([YoutubeLoader()])

try:
    content = await loader.load(url)
except LoaderNotApplicableError as e:
    print(f"URL not supported: {e.reason}")
except LoaderTimeoutError as e:
    print(f"Timeout after {e.timeout}s: {e.suggestion}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

New test file `tests/test_exceptions.py` includes:
- Exception instantiation tests
- Error message format tests
- Inheritance tests
- 7 tests covering all new exception types

All existing tests updated to work with new exception types.

## Benefits

1. **Better Debugging**: Debug logs show exactly what each loader is doing
2. **Clearer Errors**: Users know which loader failed and why
3. **Actionable Feedback**: Suggestions help users resolve issues
4. **Specific Error Types**: Can catch and handle different error scenarios
5. **Error Aggregation**: Compose shows all attempted loaders and their failures

## Backwards Compatibility

- Existing code continues to work
- Old exception types (`InvalidURLError`) still used where appropriate
- New exceptions inherit from `KabigonError` for generic catching
- LoaderError behavior unchanged for end users
