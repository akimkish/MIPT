import uvicorn
from fastapi import FastAPI, HTTPException, Query
import re


app = FastAPI()

@app.get("/add")
def add(a: float, b: float):
    return {"sum": a + b}

@app.get("/substract")
def substract(a: float, b: float):
    return {"diff": a - b}

@app.get("/multiply")
def multiply(a: float, b: float):
    return {"product": a * b}

@app.get("/divide")
def divide(a: float, b: float):
    if b == 0:
        raise HTTPException(status_code=400, detail="Division by zero!")
    else:
        return  {"quotient": a / b}
    
@app.post("/create_expression")
def create_expression(created_expression: str):
    global expression
    if not re.match(r'^[0-9+\-*/().]+$', created_expression):
    # if operation not in ["+", "-", "*", "/"]:
        raise HTTPException(status_code=400, detail="Invalid operation!")
    else:
        expression = created_expression
        return  {"Created expression": expression}

@app.get("/current_expression")
def current_expression():
    return {"Current expression": expression}

@app.get("/evaluate_expression")
def evaluate_expression():
    try:
        result = eval(expression)
        return {"Calculation result": result}
    except Exception:
        raise HTTPException(status_code=400, detail="Calculation error!")


if __name__ == "__main__":
    uvicorn.run(    
        "calculator:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    