from fastmcp import FastMCP
from fastmcp.server.dependencies import (
    get_http_headers,
    get_http_request,
)
from supabase import acreate_client, AsyncClient
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import json
import os


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

CATEGORY_PATH = BASE_DIR / "categories.json"


# Environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing")

if not SUPABASE_SECRET_KEY:
    raise ValueError("SUPABASE_SECRET_KEY is missing")


# FastMCP
mcp = FastMCP(name="Expense-Server")


# Async Supabase client
supabase: AsyncClient | None = None

_supabase_lock = asyncio.Lock()

async def get_supabase() -> AsyncClient:
    """
    Create the async Supabase client once and reuse it.
    """
    global supabase

    if supabase is None:
        async with _supabase_lock:
            # Another coroutine may have initialized it
            # while we were waiting for the lock.
            if supabase is None:
                supabase = await acreate_client(
                    SUPABASE_URL,
                    SUPABASE_SECRET_KEY,
                )
    return supabase


# --------------------------------------------------
# Current authenticated user

def current_user_id() -> str:
    """
    Resolve the caller's user_id from the X-User-ID header.

    Falls back to ?user_id= in the MCP URL if the header
    is not present.
    """

    headers = get_http_headers()

    user_id = headers.get("x-user-id")

    if not user_id:
        try:
            request = get_http_request()
            user_id = request.query_params.get("user_id")
        except RuntimeError:
            user_id = None

    if not user_id:
        raise ValueError(
            "No user identity. "
            "Send X-User-ID or ?user_id= in the MCP URL."
        )

    return user_id


# ADD TRANSACTION
@mcp.tool
async def add_transactions(
    transaction_name: str,
    date: str,
    note: str,
    category: str,
    amount: float,
    receiver_account_name: str,
    payment_mode: str,
):
    """Add a new expense transaction for the authenticated user."""

    try:

        user_id = current_user_id()

        db = await get_supabase()

        response = await (
            db
            .table("transactions")
            .insert({
                "transaction_name": transaction_name,
                "receiver_account_name": receiver_account_name,
                "date": date,
                "note": note,
                "category": category,
                "amount": amount,
                "payment_mode": payment_mode,
                "user_id": user_id,
            })
            .execute()
        )

        return response.data

    except Exception as e:

        print(f"Add_Transaction Error: {e}")

        raise


# LIST TRANSACTIONS
@mcp.tool
async def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
):
    """List expense transactions for the authenticated user."""

    try:

        user_id = current_user_id()

        db = await get_supabase()

        query = (
            db
            .table("transactions")
            .select("*")
            .eq("user_id", user_id)
        )

        if start_date:
            query = query.gte("date", start_date)

        if end_date:
            query = query.lte("date", end_date)

        response = await query.execute()

        return response.data

    except Exception as e:

        print(f"List_Transactions Error: {e}")

        raise


# GET CATEGORIES

@mcp.tool
def get_categories():
    """Get the list of valid expense categories."""

    try:

        with open(
            CATEGORY_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            categories = json.load(f)

        return json.dumps(categories)

    except Exception as e:

        print(f"Get_Categories Error: {e}")

        raise


# UPDATE TRANSACTION
@mcp.tool
async def update_transaction(
    transaction_id: int,
    transaction_name: str,
    receiver_account_name: str,
    date: str,
    note: str,
    category: str,
    amount: float,
    payment_mode: str,
):
    """Update an existing expense transaction belonging to the authenticated user."""

    try:

        user_id = current_user_id()

        db = await get_supabase()

        response = await (
            db
            .table("transactions")
            .update({
                "transaction_name": transaction_name,
                "receiver_account_name": receiver_account_name,
                "date": date,
                "note": note,
                "category": category,
                "amount": amount,
                "payment_mode": payment_mode,
            })
            .eq("id", transaction_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    except Exception as e:

        print(f"Update_Transaction Error: {e}")

        raise


# DELETE TRANSACTION
@mcp.tool
async def delete_transaction(
    transaction_id: int,
):
    """Delete an expense transaction belonging to the authenticated user."""

    try:

        user_id = current_user_id()

        db = await get_supabase()

        response = await (
            db
            .table("transactions")
            .delete()
            .eq("id", transaction_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    except Exception as e:

        print(f"Delete_Transaction Error: {e}")

        raise


# TRANSACTION SUMMARY
@mcp.tool
async def get_transaction_summary(
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get an expense summary for the authenticated user,
    optionally filtered by a date range.
    """

    try:

        user_id = current_user_id()

        db = await get_supabase()

        response = await (
            db
            .rpc(
                "get_transaction_summary",
                {
                    "user_id_param": user_id,
                    "start_date_param": start_date,
                    "end_date_param": end_date,
                },
            )
            .execute()
        )

        return response.data

    except Exception as e:

        print(f"Transaction_Summary Error: {e}")

        raise


# RUN SERVER
if __name__ == "__main__":

    port = int(
        os.getenv("PORT", 8000)
    )

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )