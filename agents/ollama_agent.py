import pandas as pd
import json
import re
import ast
import logging
from difflib import get_close_matches

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from agents.format_agent import fix_llm_output
from agents.code_fixer_agent import fix_invalid_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load datasets
df_warehouse = pd.read_csv("data/warehouse_dataset.csv")
df_store = pd.read_csv("data/store_manager_dataset.csv")
df_exec = pd.read_csv("data/executive_insights_dataset.csv")

# Setup DeepSeek-R1 LLM
llm = OllamaLLM(model="mistral", temperature=0)

# Strict Prompt
df_prompt = PromptTemplate(
    input_variables=["question", "columns"],
    template="""
You are a helpful and accurate Python data analyst working with a Pandas DataFrame called `df`.

## Objective:
Answer the user’s question **strictly using the columns provided below**. Do not use any functions or columns not listed.

## Key Rules:
- If the user uses vague or domain-specific terms (e.g. "inventory turnover", "delivery time"), map them **only** to existing columns if appropriate.
- Never make up columns or functions. Use only what's in the provided list.
- Use only valid Python syntax and built-in `pandas` or `numpy` functions.
- The final output **must assign the answer to a variable named `result`**.
- Do not use `print()`, `where`, `...`, or undefined variables.
- Do not add commentary or explanation.
- ⚠️ If the answer refers to a specific row (e.g. highest ROI), return that full row (or a few selected relevant columns) as a DataFrame.
- Do not return only the computed metric — include associated columns (e.g., 'Product Name', 'Region', 'Warehouse ID') if available so that we can understand the results showcased.

## Response Format:
Return only a JSON object with the following keys:
{{
  "answer": "<brief summary in natural language>",
  "code": "<valid Python code that assigns result to a variable named `result`>"
}}

## Example columns:
{columns}

## User question:
{question}
"""
)

df_chain: RunnableSequence = df_prompt | llm


def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def validate_and_fix_code(code: str) -> str:
    code = re.sub(r"'([^']+)':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])", r"'\1': '\2'\3", code)
    code = re.sub(r"([a-zA-Z_][a-zA-Z0-9_\s\(\)%]*)\s*:\s*'([^']+)'", r"'\1': '\2'", code)
    return code


def columns_used_in_code(code: str) -> list:
    return re.findall(r"df\[['\"]([^'\"]+)['\"]\]", code)


def validate_columns_exist(df: pd.DataFrame, code: str) -> bool:
    used_columns = columns_used_in_code(code)
    return all(col in df.columns for col in used_columns)


def suggest_column_fixes(df, code):
    used = columns_used_in_code(code)
    suggestions = {}
    for col in used:
        if col not in df.columns:
            close = get_close_matches(col, df.columns, n=1)
            if close:
                suggestions[col] = close[0]
    return suggestions


def run_llm_query(df: pd.DataFrame, question: str, agent_name: str):
    try:
        logger.info(f"Processing query with {agent_name}: {question}")

        llm_output = df_chain.invoke({
            "question": question,
            "columns": ", ".join(f"'{col}'" for col in df.columns)
        }).strip()

        logger.info(f"LLM raw output:\n{llm_output}")

        parsed = fix_llm_output(llm_output)
        if "error" in parsed:
            return {
                "response": f"❌ Format Agent failed.\n\nRaw output:\n{llm_output}",
                "status": "error",
                "agent_used": agent_name
            }

        answer_text = parsed.get("answer", "").strip()
        code = parsed.get("code", "").strip()

        if not code or "result" not in code or not is_valid_python(code):
            logger.warning("🔁 Attempting to fix invalid code with LLM...")
            code = fix_invalid_code(code)

        if not code or "result" not in code or not is_valid_python(code):
            return {
                "response": "❌ Even after code fix, the code is invalid or doesn't assign to `result`.",
                "status": "error",
                "agent_used": agent_name
            }

        if not validate_columns_exist(df, code):
            suggestions = suggest_column_fixes(df, code)
            return {
                "response": f"❌ LLM referred to invalid columns: {columns_used_in_code(code)}. Suggestions: {suggestions}",
                "status": "error",
                "agent_used": agent_name
            }

        if "calculate_performance" in code:
            return {
                "response": "❌ Hallucinated function `calculate_performance()` detected.",
                "status": "error",
                "agent_used": agent_name
            }

        logger.info(f"Extracted & validated code:\n{code}")
        code = validate_and_fix_code(code)

        safe_globals = {
            'pd': pd,
            'df': df.copy(),
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float, 'list': list, 'dict': dict,
                'sum': sum, 'min': min, 'max': max, 'round': round, 'abs': abs, 'range': range,
                'enumerate': enumerate, 'zip': zip, 'sorted': sorted, 'reversed': reversed
            }
        }
        local_vars = {}

        exec(code, safe_globals, local_vars)
        result = local_vars.get("result")

        if result is None:
            return {
                "response": "⚠️ Code ran, but no variable named `result` was found.",
                "status": "error",
                "agent_used": agent_name
            }

        if isinstance(result, pd.DataFrame):
            result_data = result.head(10).to_dict(orient="records")
        elif isinstance(result, pd.Series):
            result_data = result.to_dict()
        elif isinstance(result, (list, dict, str, int, float)):
            result_data = result
        else:
            result_data = str(result)

        return {
            "response": {
                "answer": answer_text,
                "result": result_data
            },
            "status": "success",
            "agent_used": agent_name
        }

    except Exception as e:
        logger.error(f"❌ Error in {agent_name}: {str(e)}")
        return {
            "response": f"❌ Error during execution: {str(e)}",
            "status": "error",
            "agent_used": agent_name
        }


def run_simple_query(df: pd.DataFrame, question: str, agent_name: str):
    return {
        "response": "Unable to understand your question clearly. Please rephrase it.",
        "status": "error",
        "agent_used": agent_name + "_simple"
    }


def warehouse_agent(question: str):
    result = run_llm_query(df_warehouse, question, "WarehouseAgent")
    if result["status"] == "error":
        result = run_simple_query(df_warehouse, question, "WarehouseAgent")
    return result


def store_agent(question: str):
    result = run_llm_query(df_store, question, "StoreAgent")
    if result["status"] == "error":
        result = run_simple_query(df_store, question, "StoreAgent")
    return result


def exec_agent(question: str):
    result = run_llm_query(df_exec, question, "ExecutiveAgent")
    if result["status"] == "error":
        result = run_simple_query(df_exec, question, "ExecutiveAgent")
    return result
