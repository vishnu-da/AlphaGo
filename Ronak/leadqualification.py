from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client, Client
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

app = FastAPI()

# Enable CORS for local dev and HF/Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY (or SERVICE) must be set in env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Define the blueprint for APIs
class Customer(BaseModel):
    customer_id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

# 2. Create the API endpoint
TABLE_NAME = "customers"

# Create
@app.post("/customers", response_model=Customer)
def create_customer_api(customer: Customer):
    # Insert into Supabase
    data = {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
    }
    res = supabase.table(TABLE_NAME).insert(data).execute()
    if res.error:
        raise HTTPException(status_code=400, detail=str(res.error))
    return customer

# Read
@app.get("/customers", response_model=List[Customer])
def get_customers_api():
    res = supabase.table(TABLE_NAME).select("customer_id, name, email, phone, address").order("customer_id").execute()
    if res.error:
        raise HTTPException(status_code=400, detail=str(res.error))
    return res.data or []

# Update
@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer_api(customer_id: int, customer: Customer):
    res = (
        supabase.table(TABLE_NAME)
        .update({
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
        })
        .eq("customer_id", customer_id)
        .execute()
    )
    if res.error:
        raise HTTPException(status_code=400, detail=str(res.error))
    if not res.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
    

# Delete
@app.delete("/customers/{customer_id}")
def delete_customer_api(customer_id: int):
    res = supabase.table(TABLE_NAME).delete().eq("customer_id", customer_id).execute()
    if res.error:
        raise HTTPException(status_code=400, detail=str(res.error))
    if not res.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"deleted": True, "customer_id": customer_id}
    
