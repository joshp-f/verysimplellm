from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import litellm
import json
app = FastAPI(title="Simple LLM JSON API", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    with open("index.html", "r") as f:
        return f.read()

class JSONRequest(BaseModel):
    model: str = Field(..., description="The model to use for the LLM call")
    prompt: str = Field(..., description="The user prompt")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    json_schema: Dict[str, Any] = Field(..., description="JSON schema for structured output")

class JSONResponse(BaseModel):
    json: Dict[str, Any] = Field(..., description="The structured JSON response from the LLM")

@app.post("/json", response_model=JSONResponse)
async def generate_json(
    request: JSONRequest,
    authorization: str = Header(..., description="Authorization header")
):
    try:
        messages = []
        
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": request.prompt
        })
        print(request) 
        response = litellm.completion(
            model=request.model,
            messages=messages,
            api_key=authorization,
            response_format={
                "type": "json_schema",
                "json_schema":{"schema":request.json_schema},
                "strict":True
            }
        )
        
        response_content = response.choices[0].message.content
        parsed_json = json.loads(response_content)
        
        return JSONResponse(json=parsed_json)
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response as JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM call failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)