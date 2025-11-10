# OpenRouter API Key Setup Guide

## The Problem
The simulator_main.py needs a valid OpenRouter API key to generate datasets using LLM. The current hardcoded key is invalid.

## Solution: Get Your Own Free API Key

### Step 1: Get OpenRouter API Key
1. Visit: https://openrouter.ai/keys
2. Sign up for a free account (using GitHub or email)
3. Go to "Keys" section
4. Click "Create Key"
5. Copy your API key (starts with `sk-or-v1-...`)

### Step 2: Set the API Key (Choose ONE method)

#### Method A: Environment Variable (Recommended)
In PowerShell:
```powershell
$env:OPENROUTER_API_KEY="your-key-here"
```

To make it permanent, add to your PowerShell profile:
```powershell
notepad $PROFILE
# Add this line:
$env:OPENROUTER_API_KEY="your-key-here"
```

#### Method B: Enter When Prompted
The updated simulator_main.py will now prompt you to enter the key if it's not found:
```
Enter your OpenRouter API key (or press Enter to skip): sk-or-v1-your-key-here
```

#### Method C: Hardcode (Not Recommended)
Edit `ayesha/simulator_main.py` line 8:
```python
OPENROUTER_API_KEY = "sk-or-v1-your-actual-key-here"
```

## What Was Fixed

### 1. Better Error Handling
- API key validation before use
- Prompts user to enter key if missing
- Clear error messages with instructions

### 2. Fallback Mechanism
- If LLM fails to generate columns, uses default generic columns
- If batch generation fails, continues to next batch

### 3. Environment Variable Support
- Checks `OPENROUTER_API_KEY` environment variable first
- Falls back to hardcoded value only if env var not set

## Testing

After setting your API key, test the generator:

### From Command Line:
```powershell
cd C:\Users\nihca\OneDrive\Documents\vscode\Dataset_Manager\ayesha
python simulator_main.py
```

### From Flask App:
1. Start Flask: `python flask-master/flask-master/app.py`
2. Go to http://localhost:5000
3. Click "Data Acquisition"
4. Type: `test domain | 50`
5. Click "🤖 Create"

## Free Tier Limits
- OpenRouter's free tier includes access to several free models
- Current model: `google/gemma-3n-e4b-it:free`
- Generous limits for testing and development

## Alternative: Use Local LLM
If you don't want to use OpenRouter, you could modify the code to use:
- Ollama (local, free)
- Hugging Face models (free API)
- Azure OpenAI (requires account)

Would you like me to modify the code to support local Ollama instead?
