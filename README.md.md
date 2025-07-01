# AI Code Debugging Assistant

## Description
A Streamlit-based web application that provides AI-powered debugging assistance for Python code. The tool performs static code analysis and uses OpenAI's API to provide explanations, suggested fixes, and tips for debugging Python code.

## Features
- Static code analysis using Python's AST module
- AI-powered debugging suggestions via OpenAI API
- Syntax highlighting for code readability
- Sample buggy code snippets for quick testing
- Session history tracking
- Light/dark theme support
- Report generation in Markdown format

## Usage Instructions
1. Install dependencies (see requirements.txt)
2. Set up environment variables:
   - DEBUG_ASSISTANT_PASSWORD: App access password (default: "hailetmein")
   - OPENAI_API_KEY: Your OpenAI API key (required for AI features)
3. Run the app: `streamlit run AI_Code_debugging_assistant.py`
4. Enter the password to access the app
5. Paste your Python code or select a sample
6. Click "Analyze & Debug" to get suggestions
7. Download the report if needed

## Configuration
Environment variables:
- `DEBUG_ASSISTANT_PASSWORD`: Password for app access (default: "hailetmein")
- `OPENAI_API_KEY`: Your OpenAI API key (required for AI features)
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-3.5-turbo")

## Dependencies
- streamlit
- openai
- pygments
- python-dotenv (recommended for environment variables)

## Connect, Support & Collaborate
[![LinkedIn icon. Blue and white LinkedIn logo with rounded edges, conveying a professional and inviting tone.](https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg)](https://www.linkedin.com/in/abizar-al-gifari/)  
Connect with me on LinkedIn