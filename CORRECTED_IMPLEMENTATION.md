# Data Acquisition Integration - CORRECTED Implementation

## Changes Made Based on Feedback

### ✅ Fixed Issues:
1. **Same Theme & Background**: Using existing chatbot.html with same background and conversation UI
2. **Chat-Based Interface**: No separate pages - everything in one conversation flow like preprocessing
3. **Two Buttons**: Added "Create" (🤖) and "Search" (🔍) buttons side-by-side instead of single "Send"
4. **Python File Paths**: Fixed to use correct paths: `C:\Users\nihca\OneDrive\Documents\vscode\Dataset_Manager\simulator_main.py` and `searcher_main.py`

## Implementation Details

### 1. Backend (app.py)
**Modified `data_acquisition` section in `/submit/<process_name>` route:**
- Added `action` parameter to distinguish between "create" and "search"
- Python files path fixed: `os.path.join(main_project_dir, "simulator_main.py")` where `main_project_dir` = `C:\Users\nihca\OneDrive\Documents\vscode\Dataset_Manager`
- Create action calls `simulator_main.py`
- Search action calls `searcher_main.py`
- Both add conversation messages to track interaction
- Results displayed in same chatbot interface

**Input Format for Create:**
- `"domain | rows"` → e.g., "E-commerce sales | 100"
- `"domain | columns | rows"` → e.g., "Healthcare records | name,age,diagnosis | 200"
- Parses input and passes to simulator_main.py

**Input Format for Search:**
- Simple query string → e.g., "housing prices dataset"
- Passes directly to searcher_main.py

### 2. Frontend (chatbot.html)
**Input Section for Data Acquisition:**
```html
<input type="text" name="user_input" placeholder="...">
<input type="hidden" name="action" id="actionInput">
<button onclick="submitWithAction('create')">🤖 Create</button>
<button onclick="submitWithAction('search')">🔍 Search</button>
```

**JavaScript Functions:**
- `submitWithAction(action)` - Sets action field and submits form
- Shows loading spinner during processing
- Validates input before submission

**Results Display:**
- Generator: Shows file path, rows, domain, download link
- Searcher: Shows top 5 datasets with ML scores, links, descriptions
- Both use success/error message styling from existing theme

### 3. Styling (style.css)
**Added Styles:**
- `.create-btn` - Green button (#4CAF50)
- `.search-btn` - Blue button (#2196F3)
- `.dataset-result` - Card for each search result
- `.ml-score-badge` - Color-coded ML scores (high/medium/low)
- `.download-link` - Green download button
- `.input-group` - Flex layout for input + two buttons

## User Flow

1. User clicks "Data Acquisition" on home page
2. Chatbot opens with greeting and format examples
3. User enters requirements in text box
4. User clicks either:
   - **🤖 Create** - Generate synthetic dataset
   - **🔍 Search** - Find existing datasets
5. Loading spinner shows "Processing..."
6. Results appear in conversation:
   - Create: File path, download link
   - Search: Top 5 datasets with scores
7. User can start new process or go home

## Example Inputs

### Create Dataset:
- `"E-commerce sales | 100"` - 100 rows, auto columns
- `"Student grades | name,subject,score,grade | 50"` - 50 rows, specific columns
- `"Healthcare records | 200"` - 200 rows, auto columns

### Search Dataset:
- `"housing prices california"`
- `"customer churn telecom"`
- `"sentiment analysis twitter"`

## Technical Notes

### Python File Paths:
✅ CORRECT:
```python
main_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Result: C:\Users\nihca\OneDrive\Documents\vscode\Dataset_Manager
simulator_path = os.path.join(main_project_dir, "simulator_main.py")
# Result: C:\Users\nihca\OneDrive\Documents\vscode\Dataset_Manager\simulator_main.py
```

### Subprocess Calls:
- Uses `sys.executable` for correct Python interpreter
- `cwd=main_project_dir` sets working directory
- 5-minute timeout for generator
- 10-minute timeout for searcher
- Captures stdout/stderr for output display

### Result Parsing:
**Generator:**
- Regex: `r"saved as '([^']+)'"` to extract CSV path
- Regex: `r"with (\d+) rows"` to extract row count

**Searcher:**
- Reads JSON from `results/ml_datasets_*.json`
- Gets most recent file by mtime
- Extracts top 5 datasets

## Files Modified

1. ✅ `app.py` - Updated data_acquisition handling with two actions
2. ✅ `chatbot.html` - Added two buttons and updated results display
3. ✅ `style.css` - Added button and result card styling
4. ❌ `data_acquisition.html` - No longer needed (removed/ignored)
5. ❌ `dataset_generator.html` - No longer needed (removed/ignored)
6. ❌ `dataset_searcher.html` - No longer needed (removed/ignored)

## Status
✅ Correct chatbot theme with same background
✅ Two buttons (Create & Search) in same interface
✅ Python file paths fixed
✅ Conversation-based flow maintained
✅ Results display integrated in chatbot
✅ No separate pages - all in one chat
✅ Ready to test!

## Testing Checklist
- [ ] Click "Data Acquisition" from home
- [ ] See chatbot with correct background
- [ ] See two buttons (Create & Search)
- [ ] Test Create: Enter "test dataset | 50" and click Create
- [ ] Verify loading spinner shows
- [ ] Check results show file path and download link
- [ ] Test Search: Enter "housing prices" and click Search
- [ ] Verify top 5 results show with ML scores
- [ ] Confirm conversation history preserved
