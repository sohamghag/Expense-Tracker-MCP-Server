from fastmcp import FastMCP
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
import json
from fastmcp.server.dependencies import get_http_headers, get_http_request


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CATEGORY_PATH = BASE_DIR / "categories.json"

load_dotenv()

SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_URL=os.getenv("SUPABASE_URL")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

def current_user_id() -> str:
    """Resolve the caller's user_id from header, falling back to the URL query."""
    uid = get_http_headers().get("x-user-id")
    if not uid:
        try:
            uid = get_http_request().query_params.get("user_id")
        except RuntimeError:
            uid = None
    if not uid:
        raise ValueError("No user identity: send X-User-ID or ?user_id= in the MCP URL")
    return uid

mcp = FastMCP(name="Expense-Server")

@mcp.tool
def add_transactions(transaction_name: str,
    date: str,
    note: str,
    category: str,
    amount: float,
    receiver_account_name:str,
    payment_mode: str):
    """Add a new expense transaction to the database."""
    try:

        
        user_id = current_user_id()
        
        if not user_id:
            raise ValueError("Missing X-User-ID header")
            

        response = supabase.table("transactions").insert({
        "transaction_name": transaction_name,
        "receiver_account_name": receiver_account_name,
        "date": date,
        "note": note,
        "category": category,
        "amount": amount,
        "payment_mode": payment_mode,
        "user_id":user_id
        }).execute()    

        return response.data

    except Exception as e:
        print(f"Add_Transaction Error ${e}")
        raise

@mcp.tool
def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None
):
    """List expense transactions. Optionally filter by a start and end date."""

    user_id = current_user_id()

    if not user_id:
            raise ValueError("Missing X-User-ID header")
    
    try:
        query = (
            supabase
            .table("transactions")
            .select("*")
            .eq("user_id", user_id)
        )

        if start_date:
            query = query.gte("date", start_date)

        if end_date:
            query = query.lte("date", end_date)

        response = query.execute()

        return response.data

    except Exception as e:
        print(f"List_Transactions Error: {e}")
        raise

@mcp.resource("categories://all") #The categories:// part is simply a URI scheme we're using to organize/identify our resources.
def get_categories():
    with open(CATEGORY_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)
    return json.dumps(categories)

@mcp.tool
def update_transaction(
    transaction_id: int,
    transaction_name: str,
    receiver_account_name: str,
    date: str,
    note: str,
    category: str,
    amount: float,
    payment_mode: str
):
    """Update an existing expense transaction using its transaction ID."""
    try:
        user_id = current_user_id()
            
        if not user_id:
            raise ValueError("Missing X-User-ID header")
    
        response = (
            supabase
            .table("transactions")
            .update({
                "transaction_name": transaction_name,
                "receiver_account_name": receiver_account_name,
                "date": date,
                "note": note,
                "category": category,
                "amount": amount,
                "payment_mode": payment_mode
            })
            .eq("id", transaction_id)   
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    except Exception as e:
        print(f"Update_Transaction Error: {e}")
        raise

@mcp.tool
def delete_transaction( 
    transaction_id: int):
    """Delete an expense transaction using its transaction ID."""
    try:
        user_id = current_user_id()
                    
        if not user_id:
            raise ValueError("Missing X-User-ID header")
        
        response = (
            supabase
            .table("transactions")
            .delete()
            .eq("id", transaction_id)
            .eq("user_id", user_id)   
            .execute()
        )

        return response.data

    except Exception as e:
        print(f"Delete_Transaction Error :{e}")
        raise

@mcp.tool
def get_transaction_summary(
    start_date: str | None = None,
    end_date: str | None = None
):
    """Get an expense summary for an optional date range, including total spending,
    transaction count, spending by category, and spending by payment mode.
    """
    try:
        user_id = current_user_id()

        if not user_id:
            raise ValueError("Missing X-User-ID header")

        response = supabase.rpc(
            "get_transaction_summary",
            {
                "user_id_param": user_id,
                "start_date_param": start_date,
                "end_date_param": end_date
            }
        ).execute()

        return response.data

    except Exception as e:
        print(f"Transaction_Summary Error: {e}")
        raise


# if __name__ == '__main__':
#     # mcp.run() # this is for local MCP Server
#     mcp.run(transport='http',host="0.0.0.0",port=8000) # this is for making it Remote Server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )