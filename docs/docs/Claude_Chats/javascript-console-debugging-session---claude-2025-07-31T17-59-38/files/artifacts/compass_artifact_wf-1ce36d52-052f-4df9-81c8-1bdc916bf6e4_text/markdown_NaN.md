# HTML Input Element Syntax Analysis for training_orchestrator.py

I cannot access your specific `training_orchestrator.py` file directly to provide exact line numbers, but based on the symptoms you've described (onchange attributes displaying as visible text), I can identify the most likely HTML syntax errors and provide corrected syntax for your three file upload elements.

## Common malformed HTML patterns causing onchange-as-text issues

The issue where onchange attributes appear as visible text instead of functioning HTML attributes typically occurs due to these specific syntax errors:

### Pattern 1: Missing closing angle bracket
**Malformed syntax (most common cause):**
```html
<input type="file" id="image-files" name="image-files" onchange="handleFileChange()"
<input type="file" id="prediction-files" name="prediction-files" onchange="processFiles(this)"
<input type="file" id="label-files" name="label-files" onchange="validateFiles()"
```

**Corrected syntax:**
```html
<input type="file" id="image-files" name="image-files" onchange="handleFileChange()">
<input type="file" id="prediction-files" name="prediction-files" onchange="processFiles(this)">
<input type="file" id="label-files" name="label-files" onchange="validateFiles()">
```

### Pattern 2: Improper string concatenation in Python
**Malformed Python code:**
```python
html_content = '<input type="file" id="image-files"' + 
               'onchange="handleFileChange()">'  # Missing space before onchange
```

**Corrected Python code:**
```python
html_content = '<input type="file" id="image-files" ' + 
               'onchange="handleFileChange()">'  # Added space before onchange
```

### Pattern 3: Quote escaping issues in Python strings
**Malformed syntax:**
```python
html = '<input type="file" id="prediction-files" onchange="alert("Processing")">'  # Improper quote nesting
```

**Corrected syntax:**
```python
html = '<input type="file" id="prediction-files" onchange="alert(\'Processing\')">'  # Escaped inner quotes
```

## How to locate and fix the errors in your file

1. **Search for the input elements** in your `training_orchestrator.py` file:
   ```bash
   grep -n "image-files\|prediction-files\|label-files" training_orchestrator.py
   ```

2. **Look for these specific patterns around those lines:**
   - Missing `>` character at the end of input tags
   - Incorrect quote escaping in Python string literals
   - Missing spaces between HTML attributes

3. **Check the HTML output** by viewing the page source in your browser to see exactly how the malformed HTML is being rendered.

## Complete corrected HTML syntax for your three elements

**Properly formatted file upload inputs with onchange handlers:**
```html
<div>
    <label for="image-files">Image Files:</label>
    <input type="file" id="image-files" name="image-files" 
           onchange="handleImageFiles(this)" multiple accept="image/*">
</div>
<div>
    <label for="prediction-files">Prediction Files:</label>
    <input type="file" id="prediction-files" name="prediction-files"
           onchange="handlePredictionFiles(this)" accept=".csv,.json">
</div>
<div>
    <label for="label-files">Label Files:</label>
    <input type="file" id="label-files" name="label-files"
           onchange="handleLabelFiles(this)" accept=".txt,.csv">
</div>
```

To identify the exact line numbers in your file, search for each of the three input element IDs and examine the HTML syntax around those lines for missing closing brackets or improper quote escaping. The most common issue is simply a missing `>` character at the end of the input tag, which causes everything after the last attribute to render as visible text content.