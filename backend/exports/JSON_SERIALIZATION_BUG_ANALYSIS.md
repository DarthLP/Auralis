# JSON Serialization Bug Analysis

## Error Description

**Error Message**: `"Object of type datetime is not JSON serializable"`

**Location**: Extraction pipeline during entity data processing

**Impact**: All 42 pages failed during extraction phase

## Technical Facts

### Error Occurrence
- **Stage**: Extraction pipeline (after successful crawling and fingerprinting)
- **Frequency**: 100% failure rate (42/42 pages failed)
- **First Occurrence**: Extraction Session ID 1
- **Persistent**: Error repeated in Extraction Session ID 2

### Error Details from Logs
```
TypeError: Object of type datetime is not JSON serializable
```

### Code Locations
The error occurs when Python's `json.dumps()` function encounters `datetime` objects that haven't been properly serialized to strings.

**Primary Location**: `/backend/app/services/normalize.py` line 337
```python
data_json = json.dumps(data, sort_keys=True, default=json_serial)
```

**Fix Applied**: Added custom serialization function `json_serial()` that converts datetime objects to ISO format strings.

### Data Flow
1. **Crawling**: ✅ Successfully collected 62 pages
2. **Fingerprinting**: ✅ Successfully processed 42 pages with text extraction
3. **Extraction**: ❌ Failed when converting entity data to JSON

### Root Cause Analysis
The extraction pipeline creates entity objects (companies, products, capabilities, etc.) that contain datetime fields such as:
- `extracted_at`: Current timestamp when data was processed
- `created_at`: Entity creation timestamp
- `updated_at`: Last modification timestamp

These datetime objects are Python `datetime.datetime` instances, which are not natively JSON serializable.

### Fix Status
**Attempted Fix**: Added `json_serial()` function to handle datetime serialization in `normalize.py`

**Current Status**: Fix applied but error persists, indicating the datetime objects may be introduced at a different stage in the pipeline or the fix is not being used in all serialization calls.

### Additional Investigation Needed
The error may be occurring in:
1. Entity data creation before normalization
2. Database model relationships that include datetime fields
3. Other JSON serialization calls not using the custom serializer

### Database Impact
- No data corruption
- Crawling and fingerprinting data intact
- Extraction sessions logged but no extracted entities created

### Performance Impact
- No performance degradation
- Background processing stops cleanly on error
- No memory leaks or hanging processes

## Next Steps for Resolution
1. Locate all `json.dumps()` calls in the extraction pipeline
2. Ensure all use the custom `json_serial` function
3. Verify datetime objects are properly handled at entity creation
4. Test with a single page to isolate the exact failure point
