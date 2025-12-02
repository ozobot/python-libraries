# ozobot-jsonrpc

A Python library for implementing JSON-RPC 2.0 clients with Ozobot extensions and asyncio support. 


## Ozobot extensions
- RPC notifications
- Cancellation handling (client and server initiated)


## Key Components

- `Executor`: Main class for sending requests and handling responses/notifications
- `Method`: Defines request/response/notification types for RPC methods
- `Query`: Encapsulates a single RPC call with access to response and notifications
