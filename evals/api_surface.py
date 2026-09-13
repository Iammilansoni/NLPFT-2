"""
Benchmark API surface — the sandbox tenant's template catalogue.
================================================================

Twenty API templates, deliberately organised into CONFUSION CLUSTERS.

The auth cluster is the important one. `Password_Reset_Request`,
`Password_Reset_Confirm`, and `Password_Change` are three genuinely distinct
endpoints that a bi-encoder embeds into nearly the same region of vector space —
they share almost every content word ("password", "reset", "change", "account").

This is precisely where Stage 1 recall is strong (all three land in the top-50)
and Stage 1 *precision* is weak (it routinely picks the wrong sibling). It is
therefore precisely where a cross-encoder should earn its latency budget. A
benchmark without such clusters would show Stage 2 delivering no measurable
improvement, which would tell you nothing about whether the reranker works.

Each template carries `utterances` — the rows that get embedded and indexed.
Benchmark queries in benchmark_queries.py are held out and never appear here.
"""

from __future__ import annotations

from typing import Any, Dict, List

# --------------------------------------------------------------------------
# Template catalogue
# --------------------------------------------------------------------------

API_TEMPLATES: List[Dict[str, Any]] = [
    # ---- AUTH CLUSTER (high sibling confusion) ---------------------------
    {
        "api_name": "User_Login",
        "endpoint": "/auth/login",
        "method": "POST",
        "cluster": "auth",
        "description": "Authenticate an existing user with email and password, returning an access token and refresh token pair.",
        "json_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string"},
            },
            "required": ["email", "password"],
        },
        "utterances": [
            "log in with email alice@example.com and password hunter2",
            "authenticate user bob@corp.io with password s3cret",
            "sign in to my account",
            "log me in as admin@nlpforge.com",
            "start a session with my credentials",
        ],
    },
    {
        "api_name": "User_Logout",
        "endpoint": "/auth/logout",
        "method": "POST",
        "cluster": "auth",
        "description": "Terminate the current session and revoke the active refresh token.",
        "json_schema": {
            "type": "object",
            "properties": {"refresh_token": {"type": "string"}},
            "required": ["refresh_token"],
        },
        "utterances": [
            "log out of my account",
            "end my current session",
            "sign me out",
            "revoke my refresh token",
            "terminate the active session",
        ],
    },
    {
        "api_name": "Password_Reset_Request",
        "endpoint": "/auth/password/reset-request",
        "method": "POST",
        "cluster": "auth",
        "description": "Begin a password reset for a user who cannot log in. Sends a time-limited reset link to the registered email. No authentication required.",
        "json_schema": {
            "type": "object",
            "properties": {"email": {"type": "string", "format": "email"}},
            "required": ["email"],
        },
        "utterances": [
            "I forgot my password, send me a reset link",
            "email a password reset to alice@example.com",
            "start password recovery for my account",
            "send the forgot password email",
            "I cannot log in, help me recover my account",
        ],
    },
    {
        "api_name": "Password_Reset_Confirm",
        "endpoint": "/auth/password/reset-confirm",
        "method": "POST",
        "cluster": "auth",
        "description": "Complete a password reset using the token issued by the reset-request step. Sets the new password. No authentication required beyond the token.",
        "json_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "new_password": {"type": "string"},
            },
            "required": ["token", "new_password"],
        },
        "utterances": [
            "finish my password reset with token abc123 and new password Str0ng!",
            "submit the reset token and set my new password",
            "complete password recovery using the emailed code",
            "apply my new password with the reset token",
            "confirm the password reset link",
        ],
    },
    {
        "api_name": "Password_Change",
        "endpoint": "/auth/password/change",
        "method": "POST",
        "cluster": "auth",
        "description": "Change the password of an already authenticated user. Requires the current password for verification. Distinct from reset, which is for locked-out users.",
        "json_schema": {
            "type": "object",
            "properties": {
                "current_password": {"type": "string"},
                "new_password": {"type": "string"},
            },
            "required": ["current_password", "new_password"],
        },
        "utterances": [
            "change my password from old123 to new456",
            "update my password while logged in",
            "rotate my account password",
            "set a new password using my current one",
            "I know my password but want a different one",
        ],
    },
    {
        "api_name": "User_Register",
        "endpoint": "/auth/register",
        "method": "POST",
        "cluster": "auth",
        "description": "Create a new user account with email, password and display name. Triggers an email verification message.",
        "json_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string"},
                "full_name": {"type": "string"},
            },
            "required": ["email", "password"],
        },
        "utterances": [
            "register a new account for carol@example.com",
            "sign up with email and password",
            "create a user account for Dave Smith",
            "onboard a new user",
            "make me an account",
        ],
    },
    {
        "api_name": "Email_Verify",
        "endpoint": "/auth/verify-email",
        "method": "POST",
        "cluster": "auth",
        "description": "Verify a newly registered email address using the one-time code sent during registration.",
        "json_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "otp": {"type": "string"},
            },
            "required": ["email", "otp"],
        },
        "utterances": [
            "verify my email with code 884213",
            "confirm my email address",
            "submit the OTP from the verification email",
            "activate my account with the emailed code",
            "validate the email on my new account",
        ],
    },
    {
        "api_name": "Token_Refresh",
        "endpoint": "/auth/token/refresh",
        "method": "POST",
        "cluster": "auth",
        "description": "Exchange a valid refresh token for a new short-lived access token without re-entering credentials.",
        "json_schema": {
            "type": "object",
            "properties": {"refresh_token": {"type": "string"}},
            "required": ["refresh_token"],
        },
        "utterances": [
            "refresh my access token",
            "get a new JWT using my refresh token",
            "renew the session token",
            "my access token expired, issue a new one",
            "exchange refresh token for access token",
        ],
    },
    # ---- USER CLUSTER ----------------------------------------------------
    {
        "api_name": "Get_User_Profile",
        "endpoint": "/users/{user_id}",
        "method": "GET",
        "cluster": "user",
        "description": "Fetch the full profile record for a single user by identifier.",
        "json_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
        "utterances": [
            "get the profile for user 4821",
            "show me details of user alice@example.com",
            "fetch a single user record",
            "look up user by id",
            "retrieve profile information",
        ],
    },
    {
        "api_name": "Update_User_Profile",
        "endpoint": "/users/{user_id}",
        "method": "PATCH",
        "cluster": "user",
        "description": "Partially update a user profile: display name, avatar, timezone or locale.",
        "json_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "full_name": {"type": "string"},
                "timezone": {"type": "string"},
            },
            "required": ["user_id"],
        },
        "utterances": [
            "change the display name of user 4821 to Alice Cooper",
            "update my timezone to Asia/Kolkata",
            "edit the user profile fields",
            "set a new avatar for this user",
            "modify user details",
        ],
    },
    {
        "api_name": "Delete_User",
        "endpoint": "/users/{user_id}",
        "method": "DELETE",
        "cluster": "user",
        "description": "Permanently delete a user account and cascade-remove owned resources.",
        "json_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
        "utterances": [
            "delete user account 4821",
            "remove this user permanently",
            "purge the account for bob@corp.io",
            "erase a user and all their data",
            "close and delete my account",
        ],
    },
    {
        "api_name": "List_Users",
        "endpoint": "/users",
        "method": "GET",
        "cluster": "user",
        "description": "List users with pagination and optional role or status filters.",
        "json_schema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "limit": {"type": "integer"},
                "role": {"type": "string"},
            },
        },
        "utterances": [
            "list all users on page 2",
            "show every admin account",
            "get a paginated list of users",
            "enumerate active users",
            "who are the users in this workspace",
        ],
    },
    # ---- ORDER CLUSTER ---------------------------------------------------
    {
        "api_name": "Create_Order",
        "endpoint": "/orders",
        "method": "POST",
        "cluster": "order",
        "description": "Place a new order containing one or more line items for a customer.",
        "json_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "items": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["customer_id", "items"],
        },
        "utterances": [
            "place an order for customer 991 with 2 widgets",
            "create a new order",
            "submit a purchase for three units of SKU-44",
            "buy these items for the customer",
            "start a new order",
        ],
    },
    {
        "api_name": "Cancel_Order",
        "endpoint": "/orders/{order_id}/cancel",
        "method": "POST",
        "cluster": "order",
        "description": "Cancel an order that has not yet shipped. Does not move money; use refund for that.",
        "json_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["order_id"],
        },
        "utterances": [
            "cancel order 5567 because the customer changed their mind",
            "stop this order from shipping",
            "void an unshipped order",
            "call off order number 5567",
            "abort the pending order",
        ],
    },
    {
        "api_name": "Get_Order_Status",
        "endpoint": "/orders/{order_id}",
        "method": "GET",
        "cluster": "order",
        "description": "Retrieve the current fulfilment status and line items of an order.",
        "json_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
        "utterances": [
            "what is the status of order 5567",
            "track my order",
            "show order details",
            "has order 5567 shipped yet",
            "check fulfilment progress",
        ],
    },
    {
        "api_name": "Refund_Order",
        "endpoint": "/orders/{order_id}/refund",
        "method": "POST",
        "cluster": "order",
        "description": "Issue a full or partial monetary refund against a completed order.",
        "json_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["order_id"],
        },
        "utterances": [
            "refund 45.00 on order 5567",
            "give the customer their money back",
            "issue a partial refund",
            "reimburse this completed order",
            "process a refund payment",
        ],
    },
    # ---- PAYMENT CLUSTER -------------------------------------------------
    {
        "api_name": "Create_Payment",
        "endpoint": "/payments",
        "method": "POST",
        "cluster": "payment",
        "description": "Charge a payment method for a given amount and currency.",
        "json_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "method_id": {"type": "string"},
            },
            "required": ["amount", "currency"],
        },
        "utterances": [
            "charge 120 USD to card pm_88",
            "take a payment of 99.50 EUR",
            "create a new payment intent",
            "bill the customer 45 dollars",
            "collect payment",
        ],
    },
    {
        "api_name": "Get_Payment_Status",
        "endpoint": "/payments/{payment_id}",
        "method": "GET",
        "cluster": "payment",
        "description": "Look up whether a payment succeeded, failed, or is still pending.",
        "json_schema": {
            "type": "object",
            "properties": {"payment_id": {"type": "string"}},
            "required": ["payment_id"],
        },
        "utterances": [
            "did payment pay_331 go through",
            "check the status of a payment",
            "is this charge still pending",
            "show payment result",
            "look up transaction state",
        ],
    },
    # ---- NOTIFICATION CLUSTER --------------------------------------------
    {
        "api_name": "Send_Notification",
        "endpoint": "/notifications",
        "method": "POST",
        "cluster": "notification",
        "description": "Dispatch a single notification to a user over email, SMS or push.",
        "json_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "channel": {"type": "string", "enum": ["email", "sms", "push"]},
                "body": {"type": "string"},
            },
            "required": ["user_id", "channel", "body"],
        },
        "utterances": [
            "send an SMS to user 4821 saying your order shipped",
            "push a notification to this user",
            "email the customer an alert",
            "notify user about the update",
            "dispatch a message over push",
        ],
    },
    {
        "api_name": "Update_Notification_Prefs",
        "endpoint": "/users/{user_id}/notification-preferences",
        "method": "PATCH",
        "cluster": "notification",
        "description": "Change which notification channels a user is subscribed to. Does not send anything.",
        "json_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "email_enabled": {"type": "boolean"},
                "sms_enabled": {"type": "boolean"},
            },
            "required": ["user_id"],
        },
        "utterances": [
            "turn off SMS notifications for user 4821",
            "unsubscribe me from marketing emails",
            "change my notification settings",
            "opt out of push alerts",
            "update which channels I receive messages on",
        ],
    },
]


TEMPLATES_BY_NAME: Dict[str, Dict[str, Any]] = {t["api_name"]: t for t in API_TEMPLATES}


def cluster_of(api_name: str) -> str:
    """Return the confusion cluster an API belongs to."""
    tpl = TEMPLATES_BY_NAME.get(api_name)
    return tpl["cluster"] if tpl else "unknown"
