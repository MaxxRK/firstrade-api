"""
MCP (Model Context Protocol) Server for Firstrade API.

This server exposes Firstrade trading functionality as MCP tools
that can be used by LLMs like Claude.

Supports both stdio and SSE (Server-Sent Events) transport modes.
"""

import argparse
import json
import os
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from firstrade import account, order, symbols


# Global state
class FirstradeState:
    session: Optional[account.FTSession] = None
    account_data: Optional[account.FTAccountData] = None
    order_handler: Optional[order.Order] = None
    default_account: Optional[str] = None


state = FirstradeState()


def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = os.environ.get("FIRSTRADE_CONFIG", "/config/config.json")
    if not os.path.exists(config_path):
        config_path = "config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return json.load(f)


def init_session():
    """Initialize Firstrade session from config."""
    if state.session is not None:
        return True

    try:
        config = load_config()
        state.session = account.FTSession(
            username=config.get("username"),
            password=config.get("password"),
            pin=config.get("pin"),
            email=config.get("email"),
            phone=config.get("phone"),
            mfa_secret=config.get("mfa_secret"),
            profile_path=config.get("profile_path", "/data"),
        )
        need_code = state.session.login()
        if need_code:
            raise RuntimeError(
                "MFA code required. Please use mfa_secret in config for automated login."
            )
        state.account_data = account.FTAccountData(state.session)
        state.order_handler = order.Order(state.session)
        if state.account_data.account_numbers:
            state.default_account = state.account_data.account_numbers[0]
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to initialize session: {e}")


def get_account_id(account_id: Optional[str] = None) -> str:
    """Get account ID, using default if not specified."""
    if account_id:
        return account_id
    if state.default_account:
        return state.default_account
    raise ValueError("No account specified and no default account available")


# Create MCP server
server = Server("firstrade-mcp")


@server.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="get_accounts",
            description="Get all Firstrade account numbers and their total balances",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_account_balances",
            description="Get detailed balance information for a specific account including cash, buying power, and equity",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional, uses default if not specified)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_positions",
            description="Get all current stock positions held in an account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional, uses default if not specified)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_orders",
            description="Get all pending and recent orders for an account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional, uses default if not specified)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_account_history",
            description="Get transaction history for an account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional, uses default if not specified)",
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Date range: today, 1w, 1m, 2m, mtd, ytd, ly, cust",
                        "default": "ytd",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD) when date_range is 'cust'",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD) when date_range is 'cust'",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_quote",
            description="Get real-time stock quote for a symbol including bid, ask, last price, volume, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA, GOOGL)",
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional, uses default if not specified)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_option_dates",
            description="Get available option expiration dates for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_option_chain",
            description="Get option chain (calls and puts) for a symbol and expiration date",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                    "exp_date": {
                        "type": ["string", "integer"],
                        "description": "Expiration date from get_option_dates (e.g., 20260130)",
                    },
                },
                "required": ["symbol", "exp_date"],
            },
        ),
        Tool(
            name="get_option_greeks",
            description="Get option greeks (delta, gamma, theta, vega) for options on a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                    "exp_date": {
                        "type": ["string", "integer"],
                        "description": "Expiration date (e.g., 20260130)",
                    },
                },
                "required": ["symbol", "exp_date"],
            },
        ),
        Tool(
            name="place_order",
            description="Place a stock order (buy or sell). Use dry_run=true to preview without executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER"],
                        "description": "Type of order",
                    },
                    "price_type": {
                        "type": "string",
                        "enum": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
                        "description": "Price type",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares",
                    },
                    "price": {
                        "type": "number",
                        "description": "Limit price (required for LIMIT orders)",
                    },
                    "stop_price": {
                        "type": "number",
                        "description": "Stop price (required for STOP orders)",
                    },
                    "duration": {
                        "type": "string",
                        "enum": ["DAY", "GT90", "PRE_MARKET", "AFTER_MARKET"],
                        "description": "Order duration",
                        "default": "DAY",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only preview the order without executing",
                        "default": True,
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Account number (optional)",
                    },
                },
                "required": ["symbol", "order_type", "price_type", "quantity"],
            },
        ),
        Tool(
            name="cancel_order",
            description="Cancel an existing order by order ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to cancel",
                    },
                },
                "required": ["order_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    try:
        # Initialize session if needed
        init_session()

        if name == "get_accounts":
            result = {
                "account_numbers": state.account_data.account_numbers,
                "account_balances": state.account_data.account_balances,
            }

        elif name == "get_account_balances":
            account_id = get_account_id(arguments.get("account_id"))
            result = state.account_data.get_account_balances(account_id)

        elif name == "get_positions":
            account_id = get_account_id(arguments.get("account_id"))
            result = state.account_data.get_positions(account_id)

        elif name == "get_orders":
            account_id = get_account_id(arguments.get("account_id"))
            result = state.account_data.get_orders(account_id)

        elif name == "get_account_history":
            account_id = get_account_id(arguments.get("account_id"))
            date_range = arguments.get("date_range", "ytd")
            custom_range = None
            if date_range == "cust":
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                if not start_date or not end_date:
                    raise ValueError("start_date and end_date required for custom range")
                custom_range = [start_date, end_date]
            result = state.account_data.get_account_history(account_id, date_range, custom_range)

        elif name == "get_quote":
            symbol = arguments["symbol"].upper()
            account_id = get_account_id(arguments.get("account_id"))
            quote = symbols.SymbolQuote(state.session, account_id, symbol)
            result = {
                "symbol": quote.symbol,
                "company_name": quote.company_name,
                "exchange": quote.exchange,
                "bid": quote.bid,
                "ask": quote.ask,
                "last": quote.last,
                "change": quote.change,
                "high": quote.high,
                "low": quote.low,
                "volume": quote.volume,
                "open": quote.open,
                "quote_time": quote.quote_time,
                "is_fractional": quote.is_fractional,
                "has_option": quote.has_option,
            }

        elif name == "get_option_dates":
            symbol = arguments["symbol"].upper()
            option_quote = symbols.OptionQuote(state.session, symbol)
            result = option_quote.option_dates

        elif name == "get_option_chain":
            symbol = arguments["symbol"].upper()
            exp_date = str(arguments["exp_date"])  # Convert to string in case it's passed as int
            option_quote = symbols.OptionQuote(state.session, symbol)
            result = option_quote.get_option_quote(symbol, exp_date)

        elif name == "get_option_greeks":
            symbol = arguments["symbol"].upper()
            exp_date = str(arguments["exp_date"])  # Convert to string in case it's passed as int
            option_quote = symbols.OptionQuote(state.session, symbol)
            result = option_quote.get_greek_options(symbol, exp_date)

        elif name == "place_order":
            account_id = get_account_id(arguments.get("account_id"))
            symbol = arguments["symbol"].upper()

            # Map string to enum
            price_type_map = {
                "MARKET": order.PriceType.MARKET,
                "LIMIT": order.PriceType.LIMIT,
                "STOP": order.PriceType.STOP,
                "STOP_LIMIT": order.PriceType.STOP_LIMIT,
            }
            order_type_map = {
                "BUY": order.OrderType.BUY,
                "SELL": order.OrderType.SELL,
                "SELL_SHORT": order.OrderType.SELL_SHORT,
                "BUY_TO_COVER": order.OrderType.BUY_TO_COVER,
            }
            duration_map = {
                "DAY": order.Duration.DAY,
                "GT90": order.Duration.GT90,
                "PRE_MARKET": order.Duration.PRE_MARKET,
                "AFTER_MARKET": order.Duration.AFTER_MARKET,
            }

            result = state.order_handler.place_order(
                account=account_id,
                symbol=symbol,
                price_type=price_type_map[arguments["price_type"]],
                order_type=order_type_map[arguments["order_type"]],
                duration=duration_map.get(arguments.get("duration", "DAY"), order.Duration.DAY),
                quantity=arguments["quantity"],
                price=arguments.get("price", 0.0),
                stop_price=arguments.get("stop_price"),
                dry_run=arguments.get("dry_run", True),
            )

        elif name == "cancel_order":
            order_id = arguments["order_id"]
            result = state.account_data.cancel_order(order_id)

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_stdio():
    """Run the MCP server in stdio mode."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run_sse(host: str = "0.0.0.0", port: int = 8080):
    """Run the MCP server in SSE mode."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse, Response
    import uvicorn

    # Create SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE connections."""
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
        return Response()

    async def health(request):
        """Health check endpoint."""
        return JSONResponse({"status": "ok", "transport": "sse"})

    # Create Starlette app
    app = Starlette(
        debug=False,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/sse", handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    print(f"Starting MCP server with SSE transport on http://{host}:{port}")
    print(f"  SSE endpoint: http://{host}:{port}/sse")
    print(f"  Messages endpoint: http://{host}:{port}/messages/")
    print(f"  Health check: http://{host}:{port}/health")

    uvicorn.run(app, host=host, port=port)


def main():
    """Parse arguments and run the appropriate server mode."""
    parser = argparse.ArgumentParser(description="Firstrade MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode: stdio (default) or sse",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to for SSE mode (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on for SSE mode (default: 8080)",
    )

    args = parser.parse_args()

    if args.transport == "sse":
        run_sse(host=args.host, port=args.port)
    else:
        import asyncio
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
