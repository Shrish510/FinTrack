from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import uuid

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Transaction(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float
    description: str
    date: str
    category: str
    type: str  # "expense" or "income"
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None

# Routes
@app.get("/")
async def root():
    return {"message": "Finance Tracker API"}

@app.get("/api/transactions")
async def get_transactions():
    try:
        transactions = list(db.transactions.find({}, {"_id": 0}))
        # Sort by date descending (newest first)
        transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        return {"transactions": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transactions")
async def create_transaction(transaction: Transaction):
    try:
        transaction_dict = transaction.dict()
        db.transactions.insert_one(transaction_dict)
        return {"message": "Transaction created successfully", "transaction": transaction_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    try:
        transaction = db.transactions.find_one({"id": transaction_id}, {"_id": 0})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, transaction_update: TransactionUpdate):
    try:
        update_data = {k: v for k, v in transaction_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.transactions.update_one(
            {"id": transaction_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        updated_transaction = db.transactions.find_one({"id": transaction_id}, {"_id": 0})
        return {"message": "Transaction updated successfully", "transaction": updated_transaction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    try:
        result = db.transactions.delete_one({"id": transaction_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summary")
async def get_summary():
    try:
        transactions = list(db.transactions.find({}, {"_id": 0}))
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        balance = total_income - total_expenses
        
        # Category-wise breakdown
        category_breakdown = {}
        for transaction in transactions:
            category = transaction['category']
            if category not in category_breakdown:
                category_breakdown[category] = {'income': 0, 'expense': 0}
            category_breakdown[category][transaction['type']] += transaction['amount']
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "category_breakdown": category_breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)