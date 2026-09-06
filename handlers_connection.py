"""Connection lifecycle for Kashoo Connector."""
from __future__ import annotations
import json, uuid
from imperal_sdk import ActionResult
from kashoo_client import KashooClient
from app import chat
from schemas import (
    NoParams,
    ConnectParams, ConnectionIdParams, ConnectionList, ConnectionRecord, DeleteResult
)

_SECRET = "kashoo_connections"

def _mask(value: str) -> str:
    return value[:4] + "…" + value[-4:] if len(value) > 10 else "***"

async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw: return []
    try: data = json.loads(raw)
    except: return []
    return data if isinstance(data, list) else []

async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))

async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    conns = await _load_connections(ctx)
    if not conns: return None
    if not connection_id:
        for c in conns:
            if c.get("is_active"):
                return c
        return conns[0]
    for c in conns:
        if c["id"] == connection_id:
            return c
    return None

@chat.function(
    "connect_kashoo",
    "Connect your own Kashoo account with OAuth token/API key and Business ID.",
    action_type="write",
    chain_callable=True,
    event="kashoo-connector.connect_kashoo",
    effects=["create:connection"],
    data_model=ConnectParams
)
async def connect_kashoo(ctx, params: ConnectParams) -> ActionResult[ConnectionRecord]:
    """Connect a new Kashoo account."""
    client = KashooClient(
        auth_token=params.auth_token,
        business_id=params.business_id,
        base_url=params.base_url
    )
    v_res = await client.verify_auth()
    if v_res.get("status") == "error":
        return ActionResult.error(
            f"Kashoo connection failed: {v_res.get('message')}",
            code=v_res.get("code", "UNAUTHORIZED")
        )

    conns = await _load_connections(ctx)
    for c in conns:
        c["is_active"] = False

    cid = str(uuid.uuid4())[:8]
    rec = {
        "id": cid,
        "label": params.label.strip() or f"Kashoo-{cid}",
        "auth_token": params.auth_token.strip(),
        "business_id": params.business_id.strip(),
        "base_url": client.base_url,
        "is_active": True
    }
    conns.append(rec)
    await _save_connections(ctx, conns)

    out = ConnectionRecord(
        id=rec["id"],
        label=rec["label"],
        masked_key=_mask(rec["auth_token"]),
        business_id=rec["business_id"],
        base_url=rec["base_url"],
        is_active=True
    )
    return ActionResult.ok(
        out,
        summary=f"Connected Kashoo business {params.business_id} successfully."
    )

@chat.function(
    "list_connections",
    "List connected Kashoo accounts without exposing sensitive tokens.",
    action_type="read",
    chain_callable=True,
    data_model=NoParams
)
async def list_connections(ctx, params: NoParams) -> ActionResult[ConnectionList]:
    """List all accounts."""
    conns = await _load_connections(ctx)
    records = [
        ConnectionRecord(
            id=c["id"],
            label=c.get("label", ""),
            masked_key=_mask(c.get("auth_token", c.get("api_key", ""))),
            business_id=c.get("business_id", ""),
            base_url=c.get("base_url", ""),
            is_active=c.get("is_active", False)
        )
        for c in conns
    ]
    return ActionResult.ok(
        ConnectionList(connections=records, total=len(records)),
        summary=f"Found {len(records)} Kashoo connection(s)."
    )

@chat.function(
    "disconnect_kashoo",
    "Disconnect a Kashoo account.",
    action_type="write",
    chain_callable=True,
    event="kashoo-connector.disconnect_kashoo",
    effects=["delete:connection"],
    data_model=ConnectionIdParams
)
async def disconnect_kashoo(ctx, params: ConnectionIdParams) -> ActionResult[DeleteResult]:
    """Disconnect an account."""
    conns = await _load_connections(ctx)
    target = await resolve_connection(ctx, params.connection_id)
    if not target:
        return ActionResult.error("Kashoo connection not found", code="NOT_FOUND")

    conns = [c for c in conns if c["id"] != target["id"]]
    if conns and not any(c.get("is_active") for c in conns):
        conns[0]["is_active"] = True
    await _save_connections(ctx, conns)

    return ActionResult.ok(
        DeleteResult(id=target["id"], deleted=True, message="Disconnected Kashoo connection"),
        summary=f"Disconnected Kashoo connection {target['id']}."
    )
