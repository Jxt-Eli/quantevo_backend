import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field#, EmailStr
import httpx
import time
from sqlalchemy.ext.asyncio import AsyncSession
from  fastapi import Depends
from database import get_db
from sqlalchemy import select, or_
from models import User
from models import Transaction

# mock data for now, Ive not learnt DB yet
fake_users = {
    123: {"name": "Alice", "balance": 5000},
    456: {"name": "Bob", "balance": 3500},
    789: {"name": "Charlie", "balance": 10000},
    901033019: {"name": "James", "balance": 900000},
    937: {"name": "Ananga", "balance": 945677745},
    1937: {'name': 'Ela', "balance": 0}
}

app = FastAPI()

# ==============check app status and platform name ================
@app.get("/")
def get_status():
    return {
        "name": "Quantevo Ledgers",
        "status": "operational",
        "version": "0.1.0"
    }
@app.get("/health")
def health_check():
    return {"status": "healthy"}


'''=====================check user balance with user id==========================='''
# fetch information about a user from the fake_users using the user_id 
@app.get("/balance/{user_id}")
async def get_user_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
        
    if not user:
        raise HTTPException(status_code = 404, detail = "user not found")
    
    return{
        "name": user.full_name, 
        "balance": user.balance, 
        "currency": user.currency, 
    }






# =====================transfer endpoint===========================

class TransferRequest(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    transaction_id: int
    currency: str

@app.post("/transfer")
async def create_transfer(transfer: TransferRequest, db: AsyncSession = Depends(get_db)):
    sender_result = await db.execute(select(User).where(User.user_id == transfer.sender_id))    # check the models in the User class and compare their id to the one in the transaction table
    sender = sender_result.scalar_one_or_none()

    if not sender:
        raise HTTPException(status_code=404, detail="user not found")
    if transfer.amount > sender.balance:
        raise HTTPException(status_code=400, detail= "Insufficient balance")    

    receiver_result = await db.execute(select(User).where(User.user_id == transfer.receiver_id)) 
    receiver = receiver_result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=404, detail= 'receipient not found')
    
    initial_sender_balance  = sender.balance
    initial_receiver_balance = receiver.balance

    # update balances
    sender.balance -= transfer.amount
    receiver.balance += transfer.amount

    # create transaction record

    new_transaction = Transaction(
        sender_id = transfer.sender_id, 
        receiver_id = transfer.receiver_id, 
        amount = transfer.amount,
        currency = transfer.currency, 
        transaction_id = transfer.transaction_id, 
        initial_balance = initial_sender_balance,  
        remaining_balance = sender.balance, 
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh()

    return {
        "transaction":
        {
        "transaction_id": new_transaction.transaction_id,
        "sender_id": transfer.sender_id,
        "receiver_id": transfer.receiver_id,
        "amount": transfer.amount,
        "currency": transfer.currency, 
        "status": "pending"
        },
        "sender": {'name': sender.full_name, 'initial_balance': initial_sender_balance, 'remaining_balance': sender.balance }, 
        "receiver": {'name': receiver.full_name, 'initial balance': initial_receiver_balance, 'remaining_balance': receiver.balance}
        
    }
        

        
# =========================get card info endpoint (using user id) ================================
# ---------TODO: ASK CLAUDE WHETHER WE SHOULD CREATE ANOTHER TABLE PURPOSELY FOR CARD TRANSFERS -----------      

class CardInfo(BaseModel):
    account_number: int
    card_type: str
    balance: float
    holder_name: str
    currency: str

@app.get("/card/{user_id}", response_model=CardInfo)
def get_card_info(user_id: int, db: AsyncSession = Depends(get_db)):
    if user_id == 123:
        return CardInfo(
            account_number="901033019",
            balance=50000.00,
            currency="USD",
            card_type="Virtual Card",
            holder_name="Alice Johnson"
        )
    else:
        raise HTTPException(status_code=404, detail="User not found")
    

    
# ==================get user transactions====================

@app.get("/transactions")
def get_transactions(limit: int = 10, offset: int = 0, user_id: int = None, db: AsyncSession = Depends(get_db)):
    return{
        'limit': limit,
        'offset': offset,
        'user_id': user_id,
        'message': f"Fetching {limit} transactions starting from {offset}"
    }




''' ============================================ create new user endpoint ============================================='''
# ---------POST ENDPOINT----------
# add user to database (not too complete I'll improve it over time since we'll later deal with fetching and adding information to the DB instead of adding it to some mockup inside the codebase (which is making it more complicated))
class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    initial_deposit: float = Field(gt=0, description="Must be greater than 0")
    phone: str

@app.post("/users", status_code=201)
async def create_user(new_user: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(
        select(User).where(
            or_(
                User.email == new_user.email, 
                User.phone == new_user.phone, 
            )
        )
    )
    user_exists = exists.scalar_one_or_none()
    if user_exists:
        raise HTTPException(status_code=400, detail='User exists already or details are being used for an existing account ')
    else:
        save_info = User(
            email = new_user.email, 
            balance = new_user.initial_deposit, 
            phone = new_user.phone, 
            full_name = new_user.full_name, 
        )
        db.add(save_info)
        await db.commit()
        await db.refresh(save_info)
    return {
        "message": "user created successfully",
        "email": new_user.email,
        "full_name": new_user.full_name,
        "phone": new_user.phone,
        "balance": new_user.initial_deposit
    }


''' ===========currency conversion (probably temporary) =============='''
@app.get("/convert/{amount}")
async def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "GHS"):
    # Call a real exchange rate API
    async with httpx.AsyncClient() as client:
        start = time.time()
        response = await client.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        )
        data = response.json()
        end = time.time
        ()
    
    # Get the conversion rate
    rate = data["rates"][to_currency]
    converted_amount = amount * rate
    time_taken =  (f" total time taken: {end - start:.2f}s")
    print(time_taken)
    return {
        "original_amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "exchange_rate": rate,
        "converted_amount": converted_amount,
    }


'''========================================= verification and kyc end point ================================================='''
# -----------POST ENDPOINT--------------
class VerifyPayments(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float = Field(gt=0, description="must be greater than 0")
    sender_currency: str
    receiver_currency: str

@app.post("/verify_payment")
async def verify_payment(detail: VerifyPayments, db: AsyncSession = Depends(get_db)):

    async def verify_kyc_status():
        if (detail.sender_id in fake_users) and (detail.receiver_id in fake_users):
            return {
                "kyc_checks_status": "success"
            }
        else:
            raise HTTPException(status_code=404, detail="user not found in database")
        
    async def check_fraud():
        async with httpx.AsyncClient() as client:
            await client.get("https://jsonplaceholder.typicode.com/posts/1")
            return{"process": "fraud_check", 
                   "status": "safe"}
        
    async def check_exchange_rate():
        async with httpx.AsyncClient() as client:
            response = await client.get(
            f"https://api.exchangerate-api.com/v4/latest/{detail.sender_currency}"
            )
            data = response.json()
        
            # Get the conversion rate
            rate = data["rates"][detail.receiver_currency]
            converted_amount = detail.amount * rate
            return{
                "caution!": f"you'll be sending {converted_amount}{detail.receiver_currency} to user {detail.receiver_id}"
            }
        
    await verify_kyc_status()
                
    results = await asyncio.gather(
        check_fraud(),
        check_exchange_rate(),
        get_user_balance()
    )
    print(results)
    return{
        '1': 'verification complete',
        '2': 'all checks passed',
        '3': 'click next to proceed to final payment',
    }