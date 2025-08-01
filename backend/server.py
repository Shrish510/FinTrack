from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import uuid
import re
from typing import Dict, Any

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

class SMSData(BaseModel):
    message: str
    sender: Optional[str] = None
    timestamp: Optional[str] = None

class WebhookData(BaseModel):
    service: str  # "swiggy", "zomato", "gpay"
    transaction_id: str
    amount: float
    merchant: str
    timestamp: str
    additional_data: Optional[Dict[str, Any]] = None

# Payment service configurations
PAYMENT_SERVICES = {
    "swiggy": {
        "name": "Swiggy",
        "category": "Food",
        "url": "https://www.swiggy.com",
        "color": "#fc8019"
    },
    "zomato": {
        "name": "Zomato",
        "category": "Food",
        "url": "https://www.zomato.com",
        "color": "#e23744"
    },
    "gpay": {
        "name": "Google Pay",
        "category": "Transfer",
        "url": "https://pay.google.com",
        "color": "#4285f4"
    }
}

# SMS parsing patterns for different banks
SMS_PATTERNS = {
    "sbi": r"Rs\.(\d+(?:\.\d{2})?).+?(?:spent|debited).+?(?:at|on)\s+(.+?)(?:\s+on|\s+UPI|\s+Card|\.|$)",
    "hdfc": r"Rs\s*(\d+(?:\.\d{2})?).+?(?:spent|debited).+?(?:at|on)\s+(.+?)(?:\s+on|\s+UPI|\s+Card|\.|$)",
    "icici": r"Rs\.(\d+(?:\.\d{2})?).+?(?:spent|debited).+?(?:at|on)\s+(.+?)(?:\s+on|\s+UPI|\s+Card|\.|$)",
    "axis": r"INR\s*(\d+(?:\.\d{2})?).+?(?:spent|debited).+?(?:at|on)\s+(.+?)(?:\s+on|\s+UPI|\s+Card|\.|$)",
    "generic": r"(?:Rs\.?|INR)\s*(\d+(?:\.\d{2})?).+?(?:spent|debited|paid).+?(?:at|on|to)\s+(.+?)(?:\s+on|\s+UPI|\s+Card|\.|$)"
}

def parse_sms_transaction(sms_text: str, sender: str = None) -> Optional[Dict[str, Any]]:
    """Parse SMS text to extract transaction details"""
    try:
        # Clean the SMS text
        sms_text = sms_text.strip()
        
        # Try different patterns based on sender or use generic
        patterns_to_try = []
        if sender:
            sender_lower = sender.lower()
            for bank, pattern in SMS_PATTERNS.items():
                if bank in sender_lower:
                    patterns_to_try.append(pattern)
        
        # Add generic pattern as fallback
        patterns_to_try.append(SMS_PATTERNS["generic"])
        
        for pattern in patterns_to_try:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                merchant = match.group(2).strip()
                
                # Clean merchant name
                merchant = re.sub(r'\s+', ' ', merchant)
                merchant = merchant.replace('*', '').strip()
                
                # Auto-categorize based on merchant
                category = auto_categorize_transaction(merchant)
                
                return {
                    "amount": amount,
                    "description": f"Payment to {merchant}",
                    "merchant": merchant,
                    "category": category,
                    "type": "expense",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "sms"
                }
        
        return None
    except Exception as e:
        print(f"Error parsing SMS: {e}")
        return None

def auto_categorize_transaction(merchant: str) -> str:
    """Auto-categorize transaction based on merchant name"""
    merchant_lower = merchant.lower()
    
    # Food delivery and restaurants
    if any(keyword in merchant_lower for keyword in ['swiggy', 'zomato', 'uber eats', 'dominos', 'pizza', 'restaurant', 'cafe', 'food', 'kitchen', 'biryani']):
        return "Food"
    
    # Transportation
    elif any(keyword in merchant_lower for keyword in ['uber', 'ola', 'rapido', 'metro', 'bus', 'taxi', 'petrol', 'fuel']):
        return "Transport"
    
    # Shopping
    elif any(keyword in merchant_lower for keyword in ['amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'mall', 'store']):
        return "Shopping"
    
    # Bills and utilities
    elif any(keyword in merchant_lower for keyword in ['electricity', 'water', 'gas', 'internet', 'mobile', 'recharge', 'bill']):
        return "Bills"
    
    # Default category
    else:
        return "Others"

# Routes
@app.get("/")
async def root():
    return {"message": "Finance Tracker API"}

@app.get("/api/payment-services")
async def get_payment_services():
    """Get available payment services for integration"""
    return {"services": PAYMENT_SERVICES}

@app.post("/api/parse-sms")
async def parse_sms(sms_data: SMSData):
    """Parse SMS to extract transaction details"""
    try:
        parsed_data = parse_sms_transaction(sms_data.message, sms_data.sender)
        
        if parsed_data:
            # Create transaction automatically
            transaction = Transaction(
                amount=parsed_data["amount"],
                description=parsed_data["description"],
                date=parsed_data["date"],
                category=parsed_data["category"],
                type=parsed_data["type"]
            )
            
            transaction_dict = transaction.dict()
            db.transactions.insert_one(transaction_dict)
            
            created_transaction = db.transactions.find_one({"id": transaction_dict["id"]}, {"_id": 0})
            
            return {
                "success": True,
                "message": "Transaction created from SMS",
                "transaction": created_transaction,
                "parsed_data": parsed_data
            }
        else:
            return {
                "success": False,
                "message": "Could not parse transaction from SMS",
                "parsed_data": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/{service}")
async def payment_webhook(service: str, webhook_data: WebhookData):
    """Webhook endpoint for payment service integrations"""
    try:
        if service not in PAYMENT_SERVICES:
            raise HTTPException(status_code=400, detail="Unsupported payment service")
        
        service_config = PAYMENT_SERVICES[service]
        
        # Create transaction from webhook data
        transaction = Transaction(
            amount=webhook_data.amount,
            description=f"{service_config['name']} payment to {webhook_data.merchant}",
            date=datetime.now().strftime("%Y-%m-%d"),
            category=service_config["category"],
            type="expense"
        )
        
        transaction_dict = transaction.dict()
        # Add webhook metadata
        transaction_dict["webhook_data"] = {
            "service": service,
            "transaction_id": webhook_data.transaction_id,
            "merchant": webhook_data.merchant,
            "timestamp": webhook_data.timestamp
        }
        
        db.transactions.insert_one(transaction_dict)
        created_transaction = db.transactions.find_one({"id": transaction_dict["id"]}, {"_id": 0})
        
        return {
            "success": True,
            "message": f"Transaction created from {service_config['name']} webhook",
            "transaction": created_transaction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-payments")
async def sync_payments():
    """Endpoint to trigger manual payment sync (placeholder for future implementation)"""
    try:
        # This would integrate with actual payment service APIs
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "Payment sync initiated",
            "synced_transactions": 0,
            "note": "Automatic sync requires API integration with payment services"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        # Return the transaction without MongoDB's _id field
        created_transaction = db.transactions.find_one({"id": transaction_dict["id"]}, {"_id": 0})
        return {"message": "Transaction created successfully", "transaction": created_transaction}
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