from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.ollama_agent import warehouse_agent, store_agent, exec_agent
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Union
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class QueryInput(BaseModel):
    question: str



class QueryResponse(BaseModel):
    response: Union[str, dict]  # Accept both plain strings and structured JSON
    status: str = "success"
    agent_used: str

# Thread pool for agent execution
executor = ThreadPoolExecutor(max_workers=3)

def run_agent_query(agent_fn, question: str, agent_name: str):
    try:
        result = agent_fn(question)

        # If response is already structured, pass it as-is
        if isinstance(result["response"], dict):
            return {
                "response": result["response"],
                "status": result.get("status", "success"),
                "agent_used": agent_name
            }
        else:
            # Fallback to string
            return {
                "response": str(result["response"]),
                "status": result.get("status", "success"),
                "agent_used": agent_name
            }

    except Exception as e:
        logger.error(f"Error in {agent_name}: {str(e)}")
        return {
            "response": f"Error processing query: {str(e)}",
            "status": "error",
            "agent_used": agent_name
        }

@router.post("/warehouse", response_model=QueryResponse)
async def query_warehouse(input: QueryInput):
    logger.info(f"Processing warehouse query: {input.question}")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_agent_query,
            warehouse_agent,
            input.question,
            "WarehouseAgent"
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.critical(f"Critical error in warehouse endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical error: {str(e)}")

@router.post("/store", response_model=QueryResponse)
async def query_store(input: QueryInput):
    logger.info(f"Processing store query: {input.question}")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_agent_query,
            store_agent,
            input.question,
            "StoreAgent"
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.critical(f"Critical error in store endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical error: {str(e)}")

@router.post("/executive", response_model=QueryResponse)
async def query_exec(input: QueryInput):
    logger.info(f"Processing executive query: {input.question}")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_agent_query,
            exec_agent,
            input.question,
            "ExecutiveAgent"
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.critical(f"Critical error in executive endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical error: {str(e)}")

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": {
            "warehouse": "ready",
            "store": "ready",
            "executive": "ready"
        }
    }
