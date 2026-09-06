"""Panel UI for Kashoo Connector following UI_INTERFACE_STANDARD.md and AUTH_AND_CREDENTIALS_STANDARD.md."""
from __future__ import annotations
from imperal_sdk import ui
from app import ext

def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings",
        variant="secondary",
        size="sm",
        icon="settings",
        on_click=ui.Call("__panel__kashoo_settings")
    )

def _help_modal() -> ui.UINode:
    return ui.Modal(
        trigger=ui.Button("How do I connect Kashoo?", variant="ghost", size="sm"),
        title="Connecting Kashoo",
        children=[
            ui.Text(
                "1. Sign in to your Kashoo account at app.kashoo.com.\n"
                "2. In Business Settings, find your numeric or UUID Business ID.\n"
                "3. In User Profile / Integrations, generate an OAuth Access Token or API Key.\n"
                "4. Enter the Auth Token and Business ID above and click Connect Kashoo.",
                variant="body"
            )
        ]
    )

@ext.panel("kashoo_sidebar", slot="left")
async def kashoo_sidebar(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(
        direction="v",
        gap=3,
        align="stretch",
        children=[
            ui.Text("Kashoo Accounting", variant="heading"),
            ui.Text("Manage invoices, contacts, bills, bank accounts and tax rates via Kashoo REST API.", variant="caption"),
            ui.Divider(),
            ui.Form(
                submit_label="Connect Kashoo",
                action=ui.Call("connect_kashoo"),
                children=[
                    ui.Stack(
                        direction="v",
                        gap=2,
                        align="stretch",
                        children=[
                            ui.Text("Auth Token / API Key", variant="caption"),
                            ui.Input(
                                param_name="auth_token",
                                placeholder="Enter Kashoo OAuth Token or API Key"
                            ),
                            ui.Text("Business ID", variant="caption"),
                            ui.Input(
                                param_name="business_id",
                                placeholder="e.g. 12345 or business UUID"
                            ),
                            ui.Text("Friendly Label (Optional)", variant="caption"),
                            ui.Input(
                                param_name="label",
                                placeholder="e.g. Acme Kashoo"
                            ),
                            ui.Text("Base URL (Optional)", variant="caption"),
                            ui.Input(
                                param_name="base_url",
                                placeholder="https://api.kashoo.com"
                            )
                        ]
                    )
                ]
            ),
            ui.Divider(),
            ui.Stack(
                direction="h",
                gap=2,
                children=[
                    _help_modal(),
                    _settings_button()
                ]
            )
        ]
    )
