"""
FastAPI server for Firstrade API.

This server wraps the firstrade-api library and exposes REST endpoints.
"""

import json
import os
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from firstrade import account, order, symbols


# Global session and account data
class FirstradeState:
    session: Optional[account.FTSession] = None
    account_data: Optional[account.FTAccountData] = None
    order_handler: Optional[order.Order] = None


state = FirstradeState()


def load_config(config_path: str = "/config/config.json") -> dict:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        # Fallback to local config
        config_path = "config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file not found. Please create {config_path}"
        )
    with open(config_path, "r") as f:
        return json.load(f)


def init_session(config: dict) -> tuple:
    """Initialize Firstrade session from config."""
    ft_session = account.FTSession(
        username=config.get("username"),
        password=config.get("password"),
        pin=config.get("pin"),
        email=config.get("email"),
        phone=config.get("phone"),
        mfa_secret=config.get("mfa_secret"),
        profile_path=config.get("profile_path", "/data"),
    )
    need_code = ft_session.login()
    if need_code:
        raise RuntimeError(
            "MFA code required. Please use mfa_secret in config for automated login."
        )
    ft_account_data = account.FTAccountData(ft_session)
    ft_order = order.Order(ft_session)
    return ft_session, ft_account_data, ft_order


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize session on startup."""
    try:
        config = load_config()
        state.session, state.account_data, state.order_handler = init_session(config)
        print(f"Logged in successfully. Accounts: {state.account_data.account_numbers}")
    except Exception as e:
        print(f"Warning: Failed to initialize session: {e}")
        print("Server will start but endpoints may not work until login is successful.")
    yield
    # Cleanup
    if state.session:
        try:
            state.session.delete_cookies()
        except Exception:
            pass


app = FastAPI(
    title="Firstrade API Server",
    description="REST API wrapper for Firstrade trading platform",
    version="1.0.0",
    lifespan=lifespan,
)


def get_session():
    """Dependency to ensure session is initialized."""
    if state.session is None or state.account_data is None:
        raise HTTPException(status_code=503, detail="Session not initialized")
    return state


# Pydantic Models
class LoginRequest(BaseModel):
    code: str = Field(..., description="MFA code from email/phone")


class OrderRequest(BaseModel):
    account: str = Field(..., description="Account number")
    symbol: str = Field(..., description="Stock symbol")
    price_type: str = Field(..., description="Price type: LIMIT, MARKET, STOP, STOP_LIMIT")
    order_type: str = Field(..., description="Order type: BUY, SELL, SELL_SHORT, BUY_TO_COVER")
    duration: str = Field(..., description="Duration: DAY, GT90, PRE_MARKET, AFTER_MARKET")
    quantity: int = Field(0, description="Number of shares")
    price: float = Field(0.0, description="Limit price")
    stop_price: Optional[float] = Field(None, description="Stop price")
    dry_run: bool = Field(True, description="If true, only preview the order")
    notional: bool = Field(False, description="If true, use dollar amount instead of shares")


class OptionOrderRequest(BaseModel):
    account: str = Field(..., description="Account number")
    option_symbol: str = Field(..., description="Option symbol")
    price_type: str = Field(..., description="Price type: LIMIT, MARKET")
    order_type: str = Field(..., description="Order type: BUY_OPTION, SELL_OPTION")
    duration: str = Field(..., description="Duration: DAY, GT90")
    contracts: int = Field(..., description="Number of contracts")
    price: float = Field(0.0, description="Limit price")
    stop_price: Optional[float] = Field(None, description="Stop price")
    dry_run: bool = Field(True, description="If true, only preview the order")


class CancelOrderRequest(BaseModel):
    order_id: str = Field(..., description="Order ID to cancel")


# Helper functions to map string to enums
def get_price_type(value: str) -> order.PriceType:
    mapping = {
        "LIMIT": order.PriceType.LIMIT,
        "MARKET": order.PriceType.MARKET,
        "STOP": order.PriceType.STOP,
        "STOP_LIMIT": order.PriceType.STOP_LIMIT,
        "TRAILING_STOP_DOLLAR": order.PriceType.TRAILING_STOP_DOLLAR,
        "TRAILING_STOP_PERCENT": order.PriceType.TRAILING_STOP_PERCENT,
    }
    if value.upper() not in mapping:
        raise HTTPException(status_code=400, detail=f"Invalid price_type: {value}")
    return mapping[value.upper()]


def get_order_type(value: str) -> order.OrderType:
    mapping = {
        "BUY": order.OrderType.BUY,
        "SELL": order.OrderType.SELL,
        "SELL_SHORT": order.OrderType.SELL_SHORT,
        "BUY_TO_COVER": order.OrderType.BUY_TO_COVER,
        "BUY_OPTION": order.OrderType.BUY_OPTION,
        "SELL_OPTION": order.OrderType.SELL_OPTION,
    }
    if value.upper() not in mapping:
        raise HTTPException(status_code=400, detail=f"Invalid order_type: {value}")
    return mapping[value.upper()]


def get_duration(value: str) -> order.Duration:
    mapping = {
        "DAY": order.Duration.DAY,
        "GT90": order.Duration.GT90,
        "PRE_MARKET": order.Duration.PRE_MARKET,
        "AFTER_MARKET": order.Duration.AFTER_MARKET,
        "DAY_EXT": order.Duration.DAY_EXT,
    }
    if value.upper() not in mapping:
        raise HTTPException(status_code=400, detail=f"Invalid duration: {value}")
    return mapping[value.upper()]


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "session_active": state.session is not None,
        "accounts_loaded": state.account_data is not None,
    }


@app.post("/login/mfa")
async def login_with_mfa(request: LoginRequest):
    """Complete MFA login with code from email/phone."""
    if state.session is None:
        raise HTTPException(status_code=400, detail="Session not initialized")
    try:
        state.session.login_two(request.code)
        state.account_data = account.FTAccountData(state.session)
        state.order_handler = order.Order(state.session)
        return {"status": "success", "accounts": state.account_data.account_numbers}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts")
async def get_accounts(s: FirstradeState = Depends(get_session)):
    """Get all account numbers and balances."""
    return {
        "account_numbers": s.account_data.account_numbers,
        "account_balances": s.account_data.account_balances,
    }


@app.get("/accounts/{account_id}/balances")
async def get_account_balances(account_id: str, s: FirstradeState = Depends(get_session)):
    """Get detailed balances for a specific account."""
    try:
        balances = s.account_data.get_account_balances(account_id)
        return balances
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts/{account_id}/positions")
async def get_positions(account_id: str, s: FirstradeState = Depends(get_session)):
    """Get positions for a specific account."""
    try:
        positions = s.account_data.get_positions(account_id)
        return positions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts/{account_id}/orders")
async def get_orders(account_id: str, s: FirstradeState = Depends(get_session)):
    """Get orders for a specific account."""
    try:
        orders = s.account_data.get_orders(account_id)
        return orders
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts/{account_id}/history")
async def get_account_history(
    account_id: str,
    date_range: str = "ytd",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    s: FirstradeState = Depends(get_session),
):
    """
    Get account history.

    Args:
        account_id: Account number
        date_range: One of: today, 1w, 1m, 2m, mtd, ytd, ly, cust
        start_date: Start date (YYYY-MM-DD) when date_range is 'cust'
        end_date: End date (YYYY-MM-DD) when date_range is 'cust'
    """
    try:
        custom_range = None
        if date_range == "cust":
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date and end_date required when date_range is 'cust'",
                )
            custom_range = [start_date, end_date]
        history = s.account_data.get_account_history(account_id, date_range, custom_range)
        return history
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/quote/{account_id}/{symbol}")
async def get_quote(account_id: str, symbol: str, s: FirstradeState = Depends(get_session)):
    """Get quote for a symbol."""
    try:
        quote = symbols.SymbolQuote(s.session, account_id, symbol.upper())
        return {
            "symbol": quote.symbol,
            "company_name": quote.company_name,
            "exchange": quote.exchange,
            "bid": quote.bid,
            "ask": quote.ask,
            "last": quote.last,
            "bid_size": quote.bid_size,
            "ask_size": quote.ask_size,
            "last_size": quote.last_size,
            "change": quote.change,
            "high": quote.high,
            "low": quote.low,
            "volume": quote.volume,
            "open": quote.open,
            "quote_time": quote.quote_time,
            "last_trade_time": quote.last_trade_time,
            "is_fractional": quote.is_fractional,
            "has_option": quote.has_option,
            "is_etf": quote.is_etf,
            "realtime": quote.realtime,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/options/{symbol}/dates")
async def get_option_dates(symbol: str, s: FirstradeState = Depends(get_session)):
    """Get available option expiration dates for a symbol."""
    try:
        option_quote = symbols.OptionQuote(s.session, symbol.upper())
        return option_quote.option_dates
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/options/{symbol}/chain/{exp_date}")
async def get_option_chain(symbol: str, exp_date: str, s: FirstradeState = Depends(get_session)):
    """Get option chain for a symbol and expiration date."""
    try:
        option_quote = symbols.OptionQuote(s.session, symbol.upper())
        return option_quote.get_option_quote(symbol.upper(), exp_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/options/{symbol}/greeks/{exp_date}")
async def get_option_greeks(symbol: str, exp_date: str, s: FirstradeState = Depends(get_session)):
    """Get option greeks for a symbol and expiration date."""
    try:
        option_quote = symbols.OptionQuote(s.session, symbol.upper())
        return option_quote.get_greek_options(symbol.upper(), exp_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/orders")
async def place_order(request: OrderRequest, s: FirstradeState = Depends(get_session)):
    """Place a stock order."""
    try:
        result = s.order_handler.place_order(
            account=request.account,
            symbol=request.symbol.upper(),
            price_type=get_price_type(request.price_type),
            order_type=get_order_type(request.order_type),
            duration=get_duration(request.duration),
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            dry_run=request.dry_run,
            notional=request.notional,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/orders/options")
async def place_option_order(request: OptionOrderRequest, s: FirstradeState = Depends(get_session)):
    """Place an option order."""
    try:
        result = s.order_handler.place_option_order(
            account=request.account,
            option_symbol=request.option_symbol,
            price_type=get_price_type(request.price_type),
            order_type=get_order_type(request.order_type),
            duration=get_duration(request.duration),
            contracts=request.contracts,
            price=request.price,
            stop_price=request.stop_price,
            dry_run=request.dry_run,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/orders/cancel")
async def cancel_order(request: CancelOrderRequest, s: FirstradeState = Depends(get_session)):
    """Cancel an existing order."""
    try:
        result = s.account_data.cancel_order(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
