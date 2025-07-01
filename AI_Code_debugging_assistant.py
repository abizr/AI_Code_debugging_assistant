import os
import ast
import streamlit as st
import openai
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from datetime import datetime
import base64

# --- CONFIGURATION ---
# Demo password for authentication (replace with secure method in production)
APP_PASSWORD = os.getenv("DEBUG_ASSISTANT_PASSWORD", "hailetmein")

# Sample buggy code snippets for quick testing
SAMPLE_CODES = {
    "Simple Syntax Error": "def foo()\n    print('Hello')",
    "Division by Zero": "x = 1\ny = 0\nprint(x / y)",
    "Uninitialized Variable": "def bar():\n    print(a)",
    "Debug Print": "def test():\n    print('debug')\n    return 42",
}

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def analyze_code_with_ast(code):
    """Perform basic static analysis using Python's ast module"""
    try:
        tree = ast.parse(code)
        issues = []
        
        # Check for common issues
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id == 'print' and not any(isinstance(parent, ast.Call) for parent in ast.walk(node)):
                    issues.append(f"Potential debug print statement found at line {node.lineno}")
            if isinstance(node, ast.For):
                if not isinstance(node.target, ast.Name):
                    issues.append(f"Unusual for-loop target at line {node.lineno}")
        return issues if issues else ["No obvious issues found via static analysis"]
    except SyntaxError as e:
        return [f"Syntax error found: {e.msg} at line {e.lineno}"]
    except Exception as e:
        return [f"Error during static analysis: {str(e)}"]

def format_code_with_syntax_highlighting(code, theme='colorful'):
    """Apply syntax highlighting to code using Pygments"""
    formatter = HtmlFormatter(style=theme)
    return highlight(code, PythonLexer(), formatter)

def query_llm_for_debugging(code, error_msg=""):
    """Query OpenAI API for debugging help"""
    try:
        # Use API key from session state
        openai.api_key = st.session_state.get("openai_api_key", None)
        if not openai.api_key:
            return {"error": "No OpenAI API key provided. Please enter your API key in the sidebar."}
        prompt = f"""
You are an expert Python debugging assistant. Analyze this code and any error messages.
Provide:
1. Clear explanation of issues (in markdown)
2. Suggested fixes (as Python code blocks)
3. Any relevant tips

Code:
{code}

Error message:
{error_msg}

Format your response with clear sections:
### Explanation
[your explanation here]

### Suggested Fix
```python
[fixed code here]
```

### Tips
[any additional tips]
"""
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3,
        )
        return parse_llm_response(response.choices[0].message.content)
    except Exception as e:
        return {"error": f"Failed to query LLM: {str(e)}"}

def parse_llm_response(response):
    """Parse LLM response into structured sections"""
    result = {
        "explanation": "",
        "suggested_fix": "",
        "tips": ""
    }
    
    sections = response.split("### ")
    for section in sections:
        if section.startswith("Explanation"):
            result["explanation"] = section.replace("Explanation\n", "").strip()
        elif section.startswith("Suggested Fix"):
            code_start = section.find("```python")
            if code_start != -1:
                code_end = section.find("```", code_start + 9)
                result["suggested_fix"] = section[code_start+9:code_end].strip()
        elif section.startswith("Tips"):
            result["tips"] = section.replace("Tips\n", "").strip()
    
    return result

def markdown_report(code, error, analysis, llm_response):
    """Generate a markdown report for download"""
    report = f"""# AI Code Debugging Report\n\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n## Submitted Code\n```python\n{code}\n```\n\n## Error Message\n{error if error else 'N/A'}\n\n---\n\n## Static Analysis\n"""
    for issue in analysis:
        report += f"- {issue}\n"
    report += "\n---\n\n## AI Explanation\n" + (llm_response.get("explanation", "") or "N/A")
    report += "\n\n## Suggested Fix\n"
    if llm_response.get("suggested_fix"):
        report += f"```python\n{llm_response['suggested_fix']}\n```\n"
    else:
        report += "N/A\n"
    report += "\n## Additional Tips\n" + (llm_response.get("tips", "") or "N/A")
    return report

def set_theme(theme):
    if theme == "Dark":
        st.markdown(
            """
            <style>
            body, .stApp { background-color: #222 !important; color: #eee !important; }
            .stTextArea textarea { background: #222; color: #eee; }
            .stButton>button { background: #444; color: #fff; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            body, .stApp { background-color: #fafafa !important; color: #222 !important; }
            .stTextArea textarea { background: #fff; color: #222; }
            .stButton>button { background: #e0e0e0; color: #222; }
            </style>
            """,
            unsafe_allow_html=True,
        )

def main():
    # --- Authentication ---
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔒 AI Code Debugging Assistant")
        st.markdown("Please enter the password to access the app.")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == APP_PASSWORD:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.stop()

    # --- Theme Switcher ---
    st.sidebar.title("⚙️ Settings")
    # --- API Key Input ---
    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = ''
    st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        key="openai_api_key",
        help="Enter your OpenAI API key. It is stored only in your session.",
    )
    if not st.session_state['openai_api_key']:
        st.sidebar.warning("Please enter your OpenAI API key to use AI features.")
    theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=0)
    set_theme(theme)

    # --- Session History ---
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 Session History")
    if st.session_state['history']:
        for i, item in enumerate(reversed(st.session_state['history'])):
            st.sidebar.markdown(f"**{item['timestamp']}**\n- {item['summary']}")
    else:
        st.sidebar.info("No analyses yet.")

    st.set_page_config(page_title="AI Code Debugger", layout="wide")
    st.title("🛠️ AI-Based Code Debugging Assistant")
    st.markdown(
        "<span style='font-size:1.1em'>Paste your Python code and get AI-powered debugging help</span>",
        unsafe_allow_html=True)

    with st.expander("How to use", expanded=False):
        st.markdown("""
        1. Paste your Python code in the input box or select a sample
        2. Optionally add any error messages
        3. Click "Analyze & Debug" button
        4. Review the explanations and suggested fixes
        5. Download the report if needed
        """)

    # --- Interactive Code Examples ---
    st.markdown("---")
    st.subheader("Paste your code or try a sample:")
    colA, colB = st.columns([2,1])
    with colB:
        sample_choice = st.selectbox("Or select a sample:", ["(None)"] + list(SAMPLE_CODES.keys()))
    with colA:
        code_input = st.text_area("Your Python Code:", height=250, 
                                placeholder="Paste your code here...")
    if sample_choice != "(None)":
        code_input = SAMPLE_CODES[sample_choice]
        st.info(f"Loaded sample: {sample_choice}")

    error_input = st.text_area("Error Message (optional):", height=80,
                                 placeholder="Paste any error messages here...")

    # --- Theme for code highlighting ---
    pygments_theme = 'monokai' if theme == 'Dark' else 'colorful'

    # --- Analyze & Debug Button ---
    if st.button("Analyze & Debug", type="primary"):
        if not code_input.strip():
            st.warning("Please enter some code to analyze")
        else:
            with st.spinner("Analyzing your code..."):
                # Static analysis
                static_analysis = analyze_code_with_ast(code_input)
                # LLM analysis
                llm_response = query_llm_for_debugging(code_input, error_input)
                # Save to session history
                summary = llm_response.get("explanation", "")[:60].replace("\n", " ")
                st.session_state['history'].append({
                    "timestamp": datetime.now().strftime('%H:%M:%S'),
                    "summary": summary,
                    "code": code_input,
                    "error": error_input,
                    "analysis": static_analysis,
                    "llm": llm_response
                })
                # --- Results Layout ---
                st.markdown("---")
                st.subheader("Analysis Results")
                col1, col2 = st.columns([1,2])
                with col1:
                    st.markdown("**Static Analysis**")
                    for issue in static_analysis:
                        st.warning(issue)
                with col2:
                    if "error" in llm_response:
                        st.error(llm_response["error"])
                    else:
                        with st.expander("AI Explanation", expanded=True):
                            st.markdown(llm_response["explanation"])
                        if llm_response["suggested_fix"]:
                            with st.expander("Suggested Fix", expanded=True):
                                st.markdown(format_code_with_syntax_highlighting(
                                    llm_response["suggested_fix"], pygments_theme), 
                                    unsafe_allow_html=True)
                        if llm_response["tips"]:
                            with st.expander("Additional Tips"):
                                st.markdown(llm_response["tips"])
                # --- Downloadable Report ---
                report = markdown_report(code_input, error_input, static_analysis, llm_response)
                b64 = base64.b64encode(report.encode()).decode()
                href = f'<a href="data:text/markdown;base64,{b64}" download="debug_report.md">📥 Download Report</a>'
                st.markdown(href, unsafe_allow_html=True)

# --- Footer ---
    st.markdown("---")
    st.markdown(
        "<span style='font-size:0.8em'>Made with ❤️ by AI Debugging Assistant</span>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<span style='font-size:0.8em'>Developed by Abizar Al Gifari Rahman😎 <a href='https://openai.com'>OpenAI</a></span>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()