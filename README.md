# firstrade-api

A reverse-engineered python API to interact with the Firstrade Trading platform.

This is not an official api! This api's functionality may change at any time.

This api provides a means of buying and selling stocks through Firstrade. It uses the Session class from requests to get authorization cookies. The rest is done with reverse engineered requests to Firstrade's API.

In order to use Fractional shares you must accept the agreement on the website before using it in this API.

---

## Contribution

Please feel free to contribute to this project. If you find any bugs, please open an issue.

## Disclaimer
I am not a financial advisor and not affiliated with Firstrade in any way. Use this tool at your own risk. I am not responsible for any losses or damages you may incur by using this project. This tool is provided as-is with no warranty.

## Setup

Install using pypi:

```
pip install firstrade
```

## Quikstart

The code in `test.py` will:
- Login and print account info.
- Get a quote for 'INTC' and print out the information
- Place a dry run market order for 'INTC' on the first account in the `account_numbers` list
- Print out the order confirmation
- Contains a cancel order example
- Get an option Dates, Quotes, and Greeks
- Place a dry run option order
---

## Implemented Features

- [x] Login (With all 2FA methods now supported!) 
- [x] Get Quotes
- [x] Get Account Data
- [x] Place Orders and Receive order confirmation
- [x] Get Currently Held Positions
- [x] Fractional Trading support (thanks to @jiak94)
- [x] Check on placed order status. (thanks to @Cfomodz)
- [x] Cancel placed orders
- [x] Options (Orders, Quotes, Greeks)
- [x] Order History
- [x] REST API Server (Docker)
- [x] MCP Server (Model Context Protocol)

## TO DO

- [ ] Test options fully
- [ ] Give me some Ideas!

## Options

### I am very new to options trading and have not fully tested this feature.

Please:
- USE THIS FEATURE LIKE IT IS A ALPHA/BETA
- PUT IN A GITHUB ISSUE IF YOU FIND ANY PROBLEMS
  
## REST API Server (Docker)

You can run firstrade-api as a REST API server using Docker.

### Setup

1. Create a config file:

```bash
cp config.example.json config.json
```

2. Edit `config.json` with your Firstrade credentials:

```json
{
    "username": "your_username",
    "password": "your_password",
    "pin": "your_pin",
    "email": null,
    "phone": null,
    "mfa_secret": "your_mfa_secret_if_using_authenticator_app",
    "profile_path": "/data"
}
```

**Config fields:**
- `username`: Firstrade username
- `password`: Firstrade password
- `pin`: PIN code (if using PIN login)
- `mfa_secret`: TOTP secret key (recommended for automated MFA)
- `email`/`phone`: For email/SMS MFA (requires manual code input)

### Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Run with Docker

```bash
docker build -t firstrade-api .
docker run -d -p 8000:8000 \
  -v $(pwd)/config.json:/config/config.json:ro \
  -v firstrade-data:/data \
  firstrade-api
```

### API Documentation

Once running, access the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/accounts` | Get all accounts |
| GET | `/accounts/{id}/balances` | Account balances |
| GET | `/accounts/{id}/positions` | Account positions |
| GET | `/accounts/{id}/orders` | Account orders |
| GET | `/accounts/{id}/history` | Account history |
| GET | `/quote/{account_id}/{symbol}` | Stock quote |
| GET | `/options/{symbol}/dates` | Option expiration dates |
| GET | `/options/{symbol}/chain/{exp_date}` | Option chain |
| GET | `/options/{symbol}/greeks/{exp_date}` | Option greeks |
| POST | `/orders` | Place stock order |
| POST | `/orders/options` | Place option order |
| POST | `/orders/cancel` | Cancel order |

### Example Usage

```bash
# Health check
curl http://localhost:8000/health

# Get accounts
curl http://localhost:8000/accounts

# Get quote
curl http://localhost:8000/quote/{account_id}/AAPL

# Place a dry-run order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "account": "your_account_id",
    "symbol": "AAPL",
    "price_type": "LIMIT",
    "order_type": "BUY",
    "duration": "DAY",
    "quantity": 1,
    "price": 150.00,
    "dry_run": true
  }'
```

---

## MCP Server (Model Context Protocol)

The MCP server allows LLMs like Claude to interact with your Firstrade account directly.

### Setup

1. Create `config.json` (same format as REST API server)

2. Install dependencies:

```bash
pip install firstrade mcp
```

### Run Locally

```bash
python mcp_server.py
```

### Run with Docker

```bash
docker build -f Dockerfile.mcp -t firstrade-mcp .
```

### Configure Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "firstrade": {
      "command": "python",
      "args": ["/path/to/firstrade-api/mcp_server.py"],
      "env": {
        "FIRSTRADE_CONFIG": "/path/to/config.json"
      }
    }
  }
}
```

Or using Docker:

```json
{
  "mcpServers": {
    "firstrade": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/config.json:/config/config.json:ro",
        "-v", "firstrade-data:/data",
        "firstrade-mcp"
      ]
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_accounts` | Get all account numbers and balances |
| `get_account_balances` | Get detailed balance information |
| `get_positions` | Get current stock positions |
| `get_orders` | Get pending and recent orders |
| `get_account_history` | Get transaction history |
| `get_quote` | Get real-time stock quote |
| `get_option_dates` | Get option expiration dates |
| `get_option_chain` | Get option chain for a symbol |
| `get_option_greeks` | Get option greeks |
| `place_order` | Place a stock order (supports dry_run) |
| `cancel_order` | Cancel an existing order |

### Example Prompts for Claude

Once configured, you can ask Claude things like:

- "What are my Firstrade account balances?"
- "Show me my current stock positions"
- "Get a quote for AAPL"
- "What options are available for TSLA expiring next month?"
- "Preview a limit order to buy 10 shares of NVDA at $800"

---

## If you would like to support me, you can do so here:
[![GitHub Sponsors](https://img.shields.io/github/sponsors/maxxrk?style=social)](https://github.com/sponsors/maxxrk)