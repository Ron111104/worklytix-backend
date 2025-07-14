from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_ollama import OllamaLLM
import json
import logging
import re

logger = logging.getLogger(__name__)

# Load LLM
format_llm = OllamaLLM(model="mistral", temperature=0)

# Strict prompt to enforce output format and avoid escaping issues
format_prompt = PromptTemplate(
    input_variables=["raw_output"],
    template="""
You are a strict JSON formatting assistant.

You will receive a raw LLM output that is **supposed** to be in the following JSON format:

{{
  "answer": "<natural language summary>",
  "code": "<valid Python code that assigns final result to a variable named `result`>"
}}

Your task:
- Fix the formatting while keeping Python code unescaped and clean.
- NEVER escape underscores (`_`) or other characters inside string literals or column names.
- NEVER add markdown or backticks.
- Remove all explanations or trailing comments.
- Ensure the final output is strictly valid JSON.

If the input is too malformed to fix reliably, return:
{{ "error": "invalid" }}

Raw Output:
{raw_output}
"""
)

# Build formatting chain
format_chain: RunnableSequence = format_prompt | format_llm

# Extract the first JSON object from a blob of text
def extract_json_from_text(text: str) -> str:
    match = re.search(r'{[\s\S]*}', text)
    return match.group(0).strip() if match else ""

# Main function to fix and parse LLM output
def fix_llm_output(raw_output: str) -> dict:
    logger.info("Running LLM format enforcement agent...")

    try:
        corrected = format_chain.invoke({"raw_output": raw_output}).strip()
        corrected = corrected.replace("\\_", "_")  # Fix invalid escapes

        logger.info(f"Formatted output:\n{corrected}")

        if '"error": "invalid"' in corrected.lower():
            return {"error": "invalid"}

        cleaned_json_str = extract_json_from_text(corrected)
        if not cleaned_json_str:
            return {"error": "no_json_found"}

        parsed = json.loads(cleaned_json_str)

        # Fallback: try extracting answer if it’s missing
        fallback_answer_match = re.search(r'"answer"\s*:\s*"([^"]*)"', raw_output)
        fallback_answer = fallback_answer_match.group(1).strip() if fallback_answer_match else ""

        if "answer" not in parsed or not parsed.get("answer"):
            parsed["answer"] = fallback_answer

        if "answer" not in parsed or "code" not in parsed:
            return {"error": "missing_keys"}

        return parsed

    except Exception as e:
        logger.error(f"FormatAgent failed to parse corrected output: {e}")
        return {"error": "parsing_failed"}
