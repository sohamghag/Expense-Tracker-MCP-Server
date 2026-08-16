# Expense Tracker MCP Server

An MCP (Model Context Protocol) server that exposes expense-management capabilities as reusable tools and resources.

The server uses **FastMCP** and **Supabase** as the backend database, allowing MCP-compatible AI applications to interact with expense data through natural-language tool calling.

## Architecture

```text
                 MCP Client
                     │
                     │ MCP / STDIO / HTTP
                     ▼
          ┌──────────────────────┐
          │  Expense MCP Server  │
          │       FastMCP        │
          └──────────┬───────────┘
                     │
          ┌──────────┴───────────┐
          │                      │
        Tools                Resources
          │                      │
          ▼                      ▼
   Expense Operations      categories://all
          │
          ▼
       Supabase
          │
          ▼
     transactions
        table
```
