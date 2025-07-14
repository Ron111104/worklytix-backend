from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_ollama import OllamaLLM
import logging
import re

logger = logging.getLogger(__name__)

# Initialize the LLM
fix_llm = OllamaLLM(model="mistral", temperature=0)

# Updated strict prompt
code_fix_prompt = PromptTemplate(
    input_variables=["code"],
    template="""
You are a strict Python code rewriting assistant.

The code below is INVALID Python or does not meet the rules.

Fix the code according to these rules:
- Only use valid Python syntax.
- Assign the **final output** to a variable called `result`.
- NEVER use `print()`, `return`, or ellipses `...`.
- Do not use undefined variables or functions.
- Use only valid pandas/numpy syntax and built-in Python functions.
- The dataframe is called `df` and is already defined.
- Output only the fixed Python code. No explanation.

Broken code:
{code}
"""
)

code_fixer_chain: RunnableSequence = code_fix_prompt | fix_llm

def fix_invalid_code(code: str) -> str:
    logger.info("🛠 Fixing invalid Python code via code_fixer_agent...")
    try:
        fixed_code = code_fixer_chain.invoke({"code": code}).strip()

        # Auto-fix if LLM still returned print(...) instead of result = ...
        if "print(" in fixed_code:
            print_matches = re.findall(r"print\s*\(\s*(.*)\s*\)", fixed_code)
            if print_matches:
                logger.warning("⚠️ Detected print() in LLM-fixed code. Rewriting as assignment to `result`.")
                return f"result = {print_matches[-1]}"

        return fixed_code

    except Exception as e:
        logger.error(f"❌ Failed to fix code via code_fixer_agent: {e}")
        return code
