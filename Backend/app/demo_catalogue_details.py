"""
Complete documentation for the 20 demo-catalogue templates.

`app/demo_catalogue.py` holds what ROUTING needs (name, endpoint, method, schema,
utterances) and is shared with the benchmark. This module adds everything the
Template Builder treats as mandatory, so demo templates are indistinguishable
from carefully authored ones:

  * description        >= 500 words: purpose, sibling disambiguation, fields,
                          behaviour, responses, errors, security, operations
  * parameters         one row per request field (type, required, example, doc)
  * sample_requests    >= 3: valid, edge_case and error_case scenarios, each with
                          a request and its expected response
  * sample_responses   >= 3 with status codes
  * response_schema, headers, auth_config, rate_limit, assertions

`build_template_details(tpl)` composes all of it. tests/unit/test_demo_catalogue.py
checks every template against the same rules the Template Builder validates.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Field documentation (shared across templates)
# ---------------------------------------------------------------------------

FIELD_DOCS: Dict[str, Dict[str, Any]] = {
    "email": {"doc": "Primary e-mail address of the account, compared case-insensitively.", "example": "dana@shop.io"},
    "password": {"doc": "Account password in plain text over TLS; hashed server-side, never stored or logged.", "example": "Passw0rd!"},
    "full_name": {"doc": "Display name shown in the UI and in outgoing e-mail greetings.", "example": "Dana Whitfield"},
    "refresh_token": {"doc": "Long-lived refresh token issued at login; single use, rotated on every refresh.", "example": "rt_9f2c41d7b8e04a6c"},
    "token": {"doc": "One-time password-reset token taken from the reset e-mail link; expires after 30 minutes.", "example": "prt_3b7e9a0c51d24f88"},
    "new_password": {"doc": "Replacement password; minimum 8 characters with at least one letter and one digit.", "example": "NewPass#9"},
    "current_password": {"doc": "The account's existing password, re-checked before any change is applied.", "example": "oldpass1"},
    "otp": {"doc": "Six-digit verification code sent to the e-mail address; valid for 10 minutes.", "example": "482913"},
    "user_id": {"doc": "Opaque identifier of the target user account.", "example": "usr_4821"},
    "timezone": {"doc": "IANA timezone name used to localise timestamps and scheduled notifications.", "example": "Europe/London"},
    "page": {"doc": "1-based page number for paginated results.", "example": 1},
    "limit": {"doc": "Maximum number of items per page, between 1 and 100.", "example": 25},
    "role": {"doc": "Optional role filter, for example admin, member or viewer.", "example": "admin"},
    "customer_id": {"doc": "Identifier of the customer placing the order.", "example": "cus_1042"},
    "items": {"doc": "Line items, each with a sku and a quantity of at least 1.", "example": [{"sku": "SKU-RED-M", "quantity": 2}]},
    "order_id": {"doc": "Identifier of an existing order.", "example": "8820"},
    "reason": {"doc": "Free-text reason recorded on the order history for auditing.", "example": "customer changed their mind"},
    "amount": {"doc": "Monetary amount in major units (e.g. 25.00 means twenty-five), up to two decimals.", "example": 25.0},
    "currency": {"doc": "ISO-4217 currency code.", "example": "USD"},
    "method_id": {"doc": "Identifier of a stored payment method; the default method is used when omitted.", "example": "pm_visa_4242"},
    "payment_id": {"doc": "Identifier of a payment returned by Create_Payment.", "example": "pay_7731"},
    "channel": {"doc": "Delivery channel: email, sms or push.", "example": "sms"},
    "body": {"doc": "Message text delivered to the user; up to 1,000 characters (160 for SMS).", "example": "Your order has shipped."},
    "email_enabled": {"doc": "Whether the user receives notifications by e-mail.", "example": True},
    "sms_enabled": {"doc": "Whether the user receives notifications by SMS.", "example": False},
}

# ---------------------------------------------------------------------------
# Per-template specifics
# ---------------------------------------------------------------------------
# purpose        what the endpoint does and why a caller would use it
# not_for        sibling endpoints commonly confused with this one
# success        (status, response body)
# errors         [(status, error_code, when)]
# edge / error   sample scenarios: (query, request, expected_response, note)
# auth           "public" (no session) or "bearer"
# idempotent     safe to retry with the same input

DETAILS: Dict[str, Dict[str, Any]] = {
    "User_Login": {
        "purpose": "Starts an authenticated session for an existing, verified account. It exchanges an e-mail and password for a short-lived access token and a rotating refresh token. Every other authenticated endpoint depends on the tokens issued here.",
        "not_for": {"User_Register": "creates a new account instead of signing in to one", "Token_Refresh": "renews a session without re-entering the password"},
        "success": (200, {"access_token": "at_51c0e2", "refresh_token": "rt_9f2c41d7b8e04a6c", "token_type": "bearer", "expires_in": 1800}),
        "errors": [(401, "INVALID_CREDENTIALS", "the e-mail or password does not match"), (403, "EMAIL_NOT_VERIFIED", "the account exists but its e-mail was never verified"), (429, "TOO_MANY_ATTEMPTS", "five failed attempts were made within a minute")],
        "edge": ("sign in as DANA@Shop.io with password Passw0rd!", {"email": "DANA@Shop.io", "password": "Passw0rd!"}, (200, {"token_type": "bearer", "expires_in": 1800}), "e-mail matching is case-insensitive"),
        "error": ("log me in as dana@shop.io", {"email": "dana@shop.io"}, (422, {"error": "VALIDATION_FAILED", "missing": ["password"]}), "password is required"),
        "auth": "public", "idempotent": False,
        "side_effects": "Records a login audit event and resets the failed-attempt counter.",
    },
    "User_Logout": {
        "purpose": "Ends the caller's current session. The supplied refresh token is revoked so it can never mint new access tokens, and the access token is added to the deny-list until it expires.",
        "not_for": {"Delete_User": "removes the account itself rather than ending a session", "Token_Refresh": "extends a session instead of ending it"},
        "success": (200, {"message": "Logged out"}),
        "errors": [(401, "INVALID_TOKEN", "the refresh token is unknown or already revoked")],
        "edge": ("sign me out everywhere, token rt_9f2c41d7b8e04a6c", {"refresh_token": "rt_9f2c41d7b8e04a6c"}, (200, {"message": "Logged out"}), "repeating the call is harmless"),
        "error": ("log out", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["refresh_token"]}), "refresh token is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "Revokes the refresh token and deny-lists the access token's jti.",
    },
    "Password_Reset_Request": {
        "purpose": "Starts account recovery for a user who has forgotten their password. It e-mails a single-use reset link to the address if an account exists. The response is identical either way, so the endpoint never reveals which e-mail addresses are registered.",
        "not_for": {"Password_Reset_Confirm": "completes the reset with the emailed token", "Password_Change": "changes the password of a signed-in user who knows the current one"},
        "success": (202, {"message": "If the account exists, a reset link has been sent"}),
        "errors": [(429, "TOO_MANY_REQUESTS", "more than three reset e-mails were requested within an hour")],
        "edge": ("send a reset link to someone@unknown.dev", {"email": "someone@unknown.dev"}, (202, {"message": "If the account exists, a reset link has been sent"}), "unknown addresses get the same response"),
        "error": ("I forgot my password", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["email"]}), "e-mail is required"),
        "auth": "public", "idempotent": True,
        "side_effects": "Issues a reset token valid for 30 minutes and sends one e-mail.",
    },
    "Password_Reset_Confirm": {
        "purpose": "Completes account recovery. It validates the single-use token from the reset e-mail and replaces the account's password. All existing sessions are then revoked, so a compromised session cannot outlive the reset.",
        "not_for": {"Password_Reset_Request": "only sends the reset link", "Password_Change": "requires the current password rather than a reset token"},
        "success": (200, {"message": "Password updated"}),
        "errors": [(400, "TOKEN_EXPIRED", "the reset token is older than 30 minutes"), (400, "TOKEN_USED", "the token was already redeemed"), (422, "WEAK_PASSWORD", "the new password fails the strength policy")],
        "edge": ("reset my password to NewPass#9 using token prt_3b7e9a0c51d24f88", {"token": "prt_3b7e9a0c51d24f88", "new_password": "NewPass#9"}, (200, {"message": "Password updated"}), "valid token and policy-compliant password"),
        "error": ("set my new password to abc with token prt_3b7e9a0c51d24f88", {"token": "prt_3b7e9a0c51d24f88", "new_password": "abc"}, (422, {"error": "WEAK_PASSWORD"}), "password shorter than 8 characters"),
        "auth": "public", "idempotent": False,
        "side_effects": "Consumes the token, rotates the password hash and revokes every session.",
    },
    "Password_Change": {
        "purpose": "Lets a signed-in user rotate their password by proving knowledge of the current one. It is the routine security action, distinct from recovery. Other sessions are revoked, but the caller's own session stays valid.",
        "not_for": {"Password_Reset_Request": "is for users who cannot sign in", "Password_Reset_Confirm": "uses an e-mailed token instead of the current password"},
        "success": (200, {"message": "Password changed"}),
        "errors": [(401, "WRONG_PASSWORD", "the current password is incorrect"), (422, "WEAK_PASSWORD", "the new password fails the strength policy"), (422, "PASSWORD_REUSED", "the new password equals the current one")],
        "edge": ("change my password from oldpass1 to oldpass1", {"current_password": "oldpass1", "new_password": "oldpass1"}, (422, {"error": "PASSWORD_REUSED"}), "new password must differ"),
        "error": ("change my password to NewPass#9", {"new_password": "NewPass#9"}, (422, {"error": "VALIDATION_FAILED", "missing": ["current_password"]}), "current password is required"),
        "auth": "bearer", "idempotent": False,
        "side_effects": "Rotates the password hash and revokes all other sessions.",
    },
    "User_Register": {
        "purpose": "Creates a new account from an e-mail address and password and sends a six-digit verification code to the address. The account cannot sign in until Email_Verify confirms that code.",
        "not_for": {"User_Login": "signs in to an account that already exists", "Email_Verify": "confirms the code sent by this endpoint"},
        "success": (201, {"user_id": "usr_5120", "email": "dana@shop.io", "email_verified": False}),
        "errors": [(409, "EMAIL_TAKEN", "an account already uses the address"), (422, "WEAK_PASSWORD", "the password fails the strength policy")],
        "edge": ("create an account for dana@shop.io with password Passw0rd!", {"email": "dana@shop.io", "password": "Passw0rd!"}, (201, {"user_id": "usr_5120", "email_verified": False}), "full_name is optional"),
        "error": ("sign me up with admin@nlpforge.dev and password hunter22", {"email": "admin@nlpforge.dev", "password": "hunter22"}, (409, {"error": "EMAIL_TAKEN"}), "address already registered"),
        "auth": "public", "idempotent": False,
        "side_effects": "Creates the user row and sends one verification e-mail.",
    },
    "Email_Verify": {
        "purpose": "Confirms ownership of an e-mail address by checking the six-digit code sent at registration. It marks the account verified, which unlocks sign-in.",
        "not_for": {"User_Register": "creates the account and sends the code", "Password_Reset_Confirm": "uses a reset token, not a verification code"},
        "success": (200, {"email": "dana@shop.io", "email_verified": True}),
        "errors": [(400, "INVALID_OTP", "the code does not match"), (400, "OTP_EXPIRED", "the code is older than 10 minutes"), (429, "TOO_MANY_ATTEMPTS", "five wrong codes were entered")],
        "edge": ("verify dana@shop.io again with code 482913", {"email": "dana@shop.io", "otp": "482913"}, (200, {"email_verified": True}), "already-verified accounts return success"),
        "error": ("verify my email with code 12", {"otp": "12"}, (422, {"error": "VALIDATION_FAILED", "missing": ["email"]}), "email is required and codes are six digits"),
        "auth": "public", "idempotent": True,
        "side_effects": "Marks the e-mail verified and invalidates the code.",
    },
    "Token_Refresh": {
        "purpose": "Keeps a session alive without asking for the password again. A valid refresh token is exchanged for a new access token and a new refresh token, and the old refresh token is revoked (rotation).",
        "not_for": {"User_Login": "requires credentials", "User_Logout": "ends the session instead"},
        "success": (200, {"access_token": "at_7d19aa", "refresh_token": "rt_1a88c0f2", "expires_in": 1800}),
        "errors": [(401, "INVALID_TOKEN", "the refresh token is unknown, expired or revoked"), (401, "TOKEN_REUSED", "a rotated token was presented again, so the whole session family is revoked")],
        "edge": ("refresh my session with token rt_9f2c41d7b8e04a6c", {"refresh_token": "rt_9f2c41d7b8e04a6c"}, (200, {"expires_in": 1800}), "returns a rotated pair"),
        "error": ("refresh my token", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["refresh_token"]}), "refresh token is required"),
        "auth": "public", "idempotent": False,
        "side_effects": "Revokes the presented refresh token and issues a new pair.",
    },
    "Get_User_Profile": {
        "purpose": "Reads one user's profile: name, e-mail, timezone, role and account timestamps. It is read-only and safe to call repeatedly, so it is the endpoint to use when an agent needs facts about a user before acting.",
        "not_for": {"List_Users": "returns many users with pagination", "Update_User_Profile": "modifies the profile"},
        "success": (200, {"user_id": "usr_4821", "full_name": "Dana Whitfield", "email": "dana@shop.io", "timezone": "Europe/London", "role": "member"}),
        "errors": [(404, "USER_NOT_FOUND", "no user has that id"), (403, "FORBIDDEN", "a non-admin requests another user's profile")],
        "edge": ("show me the profile for user usr_0000", {"user_id": "usr_0000"}, (404, {"error": "USER_NOT_FOUND"}), "unknown id"),
        "error": ("show me a user profile", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["user_id"]}), "user id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "None.",
    },
    "Update_User_Profile": {
        "purpose": "Partially updates a user's profile. Only the fields present in the body change (PATCH semantics). It covers display name and timezone, while e-mail and role are changed through dedicated, audited flows.",
        "not_for": {"Update_Notification_Prefs": "changes notification channels, not profile fields", "Get_User_Profile": "only reads"},
        "success": (200, {"user_id": "usr_4821", "full_name": "Dana W.", "timezone": "America/New_York"}),
        "errors": [(404, "USER_NOT_FOUND", "no user has that id"), (422, "INVALID_TIMEZONE", "the timezone is not an IANA name")],
        "edge": ("set the timezone of user usr_4821 to Mars/Olympus", {"user_id": "usr_4821", "timezone": "Mars/Olympus"}, (422, {"error": "INVALID_TIMEZONE"}), "timezone must be an IANA name"),
        "error": ("rename me to Dana W.", {"full_name": "Dana W."}, (422, {"error": "VALIDATION_FAILED", "missing": ["user_id"]}), "user id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "Writes an audit entry listing the changed fields.",
    },
    "Delete_User": {
        "purpose": "Permanently deletes a user account and its personal data, subject to a 7-day grace period during which support can restore it. It is destructive, so callers should confirm intent before routing here.",
        "not_for": {"User_Logout": "only ends a session", "Update_User_Profile": "changes data rather than removing the account"},
        "success": (202, {"user_id": "usr_4821", "status": "scheduled_for_deletion", "purge_at": "2026-09-30T00:00:00Z"}),
        "errors": [(404, "USER_NOT_FOUND", "no user has that id"), (409, "HAS_OPEN_ORDERS", "the user still has unfulfilled orders")],
        "edge": ("delete user usr_4821 who still has an open order", {"user_id": "usr_4821"}, (409, {"error": "HAS_OPEN_ORDERS"}), "open orders block deletion"),
        "error": ("delete my account", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["user_id"]}), "user id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "Revokes all sessions and schedules a data purge.",
    },
    "List_Users": {
        "purpose": "Returns a page of users for administrative screens, optionally filtered by role. Results are ordered by creation time, newest first, and include a total count for pagination controls.",
        "not_for": {"Get_User_Profile": "returns exactly one user by id"},
        "success": (200, {"items": [{"user_id": "usr_4821", "full_name": "Dana Whitfield", "role": "admin"}], "page": 1, "limit": 25, "total": 1}),
        "errors": [(403, "FORBIDDEN", "the caller is not an administrator"), (422, "INVALID_LIMIT", "limit is outside 1 to 100")],
        "edge": ("list users page 99", {"page": 99}, (200, {"items": [], "page": 99, "total": 1}), "pages past the end return an empty list"),
        "error": ("list 500 users at once", {"limit": 500}, (422, {"error": "INVALID_LIMIT"}), "limit is capped at 100"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "None.",
    },
    "Create_Order": {
        "purpose": "Places a new order for a customer from one or more line items. Stock is reserved and the order starts in the pending_payment state until Create_Payment settles it.",
        "not_for": {"Create_Payment": "pays for an order that already exists", "Get_Order_Status": "only reads an order"},
        "success": (201, {"order_id": "8820", "status": "pending_payment", "total": 49.98, "currency": "USD"}),
        "errors": [(422, "EMPTY_ORDER", "items is empty"), (409, "OUT_OF_STOCK", "a SKU lacks the requested quantity"), (404, "CUSTOMER_NOT_FOUND", "the customer id is unknown")],
        "edge": ("order 0 units of SKU-RED-M for customer cus_1042", {"customer_id": "cus_1042", "items": [{"sku": "SKU-RED-M", "quantity": 0}]}, (422, {"error": "INVALID_QUANTITY"}), "quantities must be at least 1"),
        "error": ("start a new order", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["customer_id", "items"]}), "customer and items are required"),
        "auth": "bearer", "idempotent": False,
        "side_effects": "Reserves stock for 30 minutes and emits order.created.",
    },
    "Cancel_Order": {
        "purpose": "Cancels an order that has not shipped. Reserved stock is released and any captured payment is refunded in full automatically. For partial money-back on a delivered order, use Refund_Order instead.",
        "not_for": {"Refund_Order": "returns money, possibly partially, on an order that is kept or already delivered", "Delete_User": "removes an account"},
        "success": (200, {"order_id": "8820", "status": "cancelled", "refund_id": "rf_2291"}),
        "errors": [(404, "ORDER_NOT_FOUND", "no order has that id"), (409, "ALREADY_SHIPPED", "the order left the warehouse")],
        "edge": ("cancel order 5567 which already shipped", {"order_id": "5567"}, (409, {"error": "ALREADY_SHIPPED"}), "shipped orders must be refunded instead"),
        "error": ("cancel my order", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["order_id"]}), "order id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "Releases stock, triggers a full refund when paid, emits order.cancelled.",
    },
    "Get_Order_Status": {
        "purpose": "Reads an order's current state (pending_payment, paid, shipped, delivered or cancelled) with its line items, totals and tracking number once shipped. It is the read-only companion to every order action.",
        "not_for": {"Get_Payment_Status": "reports on a payment rather than an order", "Cancel_Order": "changes the order"},
        "success": (200, {"order_id": "8820", "status": "shipped", "tracking_number": "1Z999AA10123456784"}),
        "errors": [(404, "ORDER_NOT_FOUND", "no order has that id"), (403, "FORBIDDEN", "the order belongs to another customer")],
        "edge": ("where is order 0000", {"order_id": "0000"}, (404, {"error": "ORDER_NOT_FOUND"}), "unknown order id"),
        "error": ("where is my order", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["order_id"]}), "order id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "None.",
    },
    "Refund_Order": {
        "purpose": "Returns money to the customer for an order, fully or partially, without cancelling it. It is typical for damaged or missing items. When amount is omitted, the remaining refundable balance is refunded.",
        "not_for": {"Cancel_Order": "stops an unshipped order entirely", "Create_Payment": "charges rather than refunds"},
        "success": (201, {"refund_id": "rf_2291", "order_id": "8820", "amount": 25.0, "status": "pending"}),
        "errors": [(404, "ORDER_NOT_FOUND", "no order has that id"), (422, "AMOUNT_EXCEEDS_BALANCE", "the amount is more than the refundable balance"), (409, "NOT_PAID", "the order was never paid")],
        "edge": ("refund order 8820 in full", {"order_id": "8820"}, (201, {"order_id": "8820", "status": "pending"}), "omitting amount refunds the remaining balance"),
        "error": ("refund 900 dollars on order 8820", {"order_id": "8820", "amount": 900.0}, (422, {"error": "AMOUNT_EXCEEDS_BALANCE"}), "amount above the order total"),
        "auth": "bearer", "idempotent": False,
        "side_effects": "Creates a refund against the original payment and emits order.refunded.",
    },
    "Create_Payment": {
        "purpose": "Charges an amount in a given currency to a stored payment method, usually to settle a pending order. Supply an Idempotency-Key header so that network retries never double-charge.",
        "not_for": {"Refund_Order": "moves money back to the customer", "Get_Payment_Status": "only reads a payment"},
        "success": (201, {"payment_id": "pay_7731", "status": "succeeded", "amount": 49.98, "currency": "USD"}),
        "errors": [(402, "CARD_DECLINED", "the issuer declined the charge"), (422, "UNSUPPORTED_CURRENCY", "the currency is not enabled"), (409, "DUPLICATE_REQUEST", "the Idempotency-Key was reused with a different body")],
        "edge": ("charge 49.98 USD", {"amount": 49.98, "currency": "USD"}, (201, {"status": "succeeded"}), "the default payment method is used when method_id is omitted"),
        "error": ("pay 20 in dogecoin", {"amount": 20.0, "currency": "DOGE"}, (422, {"error": "UNSUPPORTED_CURRENCY"}), "currency must be enabled"),
        "auth": "bearer", "idempotent": False,
        "side_effects": "Captures funds and emits payment.succeeded or payment.failed.",
    },
    "Get_Payment_Status": {
        "purpose": "Reads a payment's lifecycle state (processing, succeeded, failed or refunded) with the failure reason when the charge was declined. Poll it after Create_Payment returns processing.",
        "not_for": {"Get_Order_Status": "reports on an order", "Create_Payment": "creates a charge"},
        "success": (200, {"payment_id": "pay_7731", "status": "succeeded", "amount": 49.98}),
        "errors": [(404, "PAYMENT_NOT_FOUND", "no payment has that id")],
        "edge": ("did payment pay_0001 go through", {"payment_id": "pay_0001"}, (200, {"payment_id": "pay_0001", "status": "failed", "failure_reason": "insufficient_funds"}), "declined payments report a reason"),
        "error": ("did my payment go through", {}, (422, {"error": "VALIDATION_FAILED", "missing": ["payment_id"]}), "payment id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "None.",
    },
    "Send_Notification": {
        "purpose": "Delivers a single message to one user over e-mail, SMS or push. The user's notification preferences are honoured: a disabled channel is reported rather than bypassed.",
        "not_for": {"Update_Notification_Prefs": "changes which channels a user accepts; it sends nothing"},
        "success": (202, {"notification_id": "ntf_6610", "channel": "sms", "status": "queued"}),
        "errors": [(404, "USER_NOT_FOUND", "no user has that id"), (409, "CHANNEL_DISABLED", "the user opted out of the channel"), (422, "BODY_TOO_LONG", "an SMS body exceeds 160 characters")],
        "edge": ("text user usr_4821 that their order shipped, but they disabled SMS", {"user_id": "usr_4821", "channel": "sms", "body": "Your order has shipped."}, (409, {"error": "CHANNEL_DISABLED"}), "preferences are enforced"),
        "error": ("notify usr_4821 by fax", {"user_id": "usr_4821", "channel": "fax"}, (422, {"error": "VALIDATION_FAILED", "detail": "channel must be one of email, sms, push; body is required"}), "invalid channel and missing body"),
        "auth": "bearer", "idempotent": False,
        "side_effects": "Queues one delivery and records it in the user's notification log.",
    },
    "Update_Notification_Prefs": {
        "purpose": "Changes which channels a user accepts notifications on. It sends nothing itself. Only the flags present are changed, and the result governs what Send_Notification may deliver.",
        "not_for": {"Send_Notification": "delivers a message", "Update_User_Profile": "changes profile fields"},
        "success": (200, {"user_id": "usr_4821", "email_enabled": True, "sms_enabled": False}),
        "errors": [(404, "USER_NOT_FOUND", "no user has that id")],
        "edge": ("keep my notification settings the same for usr_4821", {"user_id": "usr_4821"}, (200, {"user_id": "usr_4821", "email_enabled": True, "sms_enabled": False}), "an empty update returns current preferences"),
        "error": ("turn off sms", {"sms_enabled": False}, (422, {"error": "VALIDATION_FAILED", "missing": ["user_id"]}), "user id is required"),
        "auth": "bearer", "idempotent": True,
        "side_effects": "Writes an audit entry of the changed channels.",
    },
}

CLUSTER_CONTEXT = {
    "auth": "It belongs to the authentication family. That family has eight sibling endpoints that share vocabulary (password, token, e-mail, session), so it is the most important family to route precisely. These endpoints are also where a wrong route has security consequences.",
    "user": "It belongs to the user-management family, which covers reading, listing, updating and deleting accounts. These endpoints differ mainly by the verb in the request, so routing depends on recognising intent (read, change or remove) rather than the nouns.",
    "order": "It belongs to the order lifecycle family (create, read, cancel, refund). Its members share the order vocabulary, so the distinguishing signal is the action the user wants and the order's state.",
    "payment": "It belongs to the payments family. Money moves only through explicit, idempotent calls, and read endpoints never have side effects.",
    "notification": "It belongs to the notifications family. Delivery and preferences are separate endpoints, so that sending a message can never change what a user has opted into.",
}


def _example_request(tpl: Dict[str, Any]) -> Dict[str, Any]:
    props = tpl["json_schema"].get("properties", {})
    return {k: copy.deepcopy(FIELD_DOCS[k]["example"]) for k in props if k in FIELD_DOCS}


def _response_schema(body: Dict[str, Any]) -> Dict[str, Any]:
    def typ(v: Any) -> str:
        return {bool: "boolean", int: "integer", float: "number", list: "array", dict: "object"}.get(type(v), "string")

    return {"type": "object", "properties": {k: {"type": typ(v)} for k, v in body.items()}}


def _description(tpl: Dict[str, Any], d: Dict[str, Any]) -> str:
    props = tpl["json_schema"].get("properties", {})
    required = set(tpl["json_schema"].get("required", []))
    method, endpoint = tpl["method"], tpl["endpoint"]
    status, body = d["success"]

    fields = " ".join(
        f"`{k}` ({v.get('type', 'string')}, {'required' if k in required else 'optional'}): "
        f"{FIELD_DOCS.get(k, {}).get('doc', 'see schema')}"
        for k, v in props.items()
    )
    siblings = " ".join(f"Do not use it when the request {why}: route to {name} instead." for name, why in d["not_for"].items())
    errors = " ".join(f"{s} {code} is returned when {when}." for s, code, when in d["errors"])
    auth = (
        "It is a public endpoint and accepts requests without a session. Abuse is contained by per-IP rate limiting and uniform responses that do not leak account existence."
        if d["auth"] == "public"
        else "It requires a valid bearer access token (sent as an HttpOnly session cookie by browsers, or an Authorization header by API clients). Every request is scoped to the caller's tenant, and cross-tenant identifiers are treated as not found."
    )
    retry = (
        "The operation is idempotent: repeating an identical request leaves the system in the same state. Clients may retry safely after a timeout."
        if d["idempotent"]
        else "The operation is not idempotent. Clients should send an Idempotency-Key header and reuse it on retry, so a network failure never applies the action twice."
    )
    verb = {"GET": "reads", "POST": "performs an action on", "PATCH": "partially updates", "DELETE": "removes"}[method]
    req_names = [k for k in props if k in required]
    opt_names = [k for k in props if k not in required]
    example = _example_request(tpl)
    sensitive = method == "DELETE" or tpl["cluster"] == "payment" or tpl["api_name"] == "Refund_Order"
    confirm = (
        "Because this action is destructive or moves money, an agent should restate the resolved call and get explicit "
        "confirmation before executing it."
        if sensitive
        else "It has no destructive side effects, so an agent can execute it once the required fields are known."
    )
    integration = (
        f"Integration. When a natural-language request routes here, the caller must collect "
        f"{', '.join(req_names) if req_names else 'no required fields'} before executing"
        + (f"; {', '.join(opt_names)} {'is' if len(opt_names) == 1 else 'are'} optional and default server-side" if opt_names else "")
        + f". {confirm} The template ships three reviewed scenarios: a valid request, an edge case "
        f"({d['edge'][3]}) and an error case ({d['error'][3]}). The dataset generator expands these into realistic "
        f"variations used to train and evaluate routing."
    )

    return (
        f"{d['purpose']} {tpl['description']}\n\n"
        f"Endpoint. {tpl['api_name'].replace('_', ' ')} ({method} {endpoint}) {verb} a resource in the demo platform API.\n\n"
        f"When to use it. {CLUSTER_CONTEXT[tpl['cluster']]} Typical requests look like: "
        + "; ".join(f"\"{u}\"" for u in tpl["utterances"][:3])
        + f". {siblings}\n\n"
        f"Request. The body is JSON validated against the template's JSON Schema. Unknown fields are rejected, and every "
        f"required field must be present. {fields} Path parameters in the endpoint are filled from the fields of the same "
        f"name. Clients should send Content-Type: application/json and may send an X-Request-ID header, which is echoed "
        f"back for tracing.\n\n"
        f"Response. On success the endpoint returns HTTP {status} with a JSON body such as "
        f"{', '.join(f'{k}={v!r}' for k, v in list(body.items())[:4])}. Timestamps are ISO-8601 in UTC, and identifiers "
        f"are opaque strings that clients should not parse.\n\n"
        f"Errors. Errors use one envelope, {{\"error\": CODE, \"message\": ..., \"request_id\": ...}}, with a stable, "
        f"machine-readable code. {errors} A 422 VALIDATION_FAILED lists the missing or invalid fields, so a caller can "
        f"ask the user for exactly what is absent instead of guessing. Unexpected failures return 500 with the request id "
        f"for support.\n\n"
        f"Behaviour. {d['side_effects']} {retry}\n\n"
        f"Example. The request \"{tpl['utterances'][1]}\" resolves to {method} {endpoint} with the body "
        f"{example}.\n\n"
        f"{integration}\n\n"
        f"Security. {auth} Sensitive values such as passwords and tokens are never logged; request logs record only field "
        f"names and a redacted marker.\n\n"
        f"Operations. The endpoint is rate limited to {60 if method == 'GET' else 30} requests per minute per client, and "
        f"exceeding the limit returns 429 with a Retry-After header. Latency is tracked per route, and the p95 target is "
        f"under 300 ms excluding downstream providers. The API is versioned by the /v1 prefix. Breaking changes ship under "
        f"a new version with at least 90 days of overlap."
    )


def build_template_details(tpl: Dict[str, Any]) -> Dict[str, Any]:
    """Every Template Builder field for one catalogue template."""
    d = DETAILS[tpl["api_name"]]
    props = tpl["json_schema"].get("properties", {})
    required = set(tpl["json_schema"].get("required", []))
    status, body = d["success"]

    valid_request = _example_request(tpl)
    edge_q, edge_req, (edge_status, edge_body), edge_note = d["edge"]
    err_q, err_req, (err_status, err_body), err_note = d["error"]

    sample_requests: List[Dict[str, Any]] = [
        {"scenario": "valid", "query": tpl["utterances"][0], "request": valid_request,
         "expected_response": {"status_code": status, "body": body}, "note": "happy path"},
        {"scenario": "edge_case", "query": edge_q, "request": edge_req,
         "expected_response": {"status_code": edge_status, "body": edge_body}, "note": edge_note},
        {"scenario": "error_case", "query": err_q, "request": err_req,
         "expected_response": {"status_code": err_status, "body": err_body}, "note": err_note},
    ]
    sample_responses = [
        {"status_code": status, "scenario": "valid", "response_body": body},
        {"status_code": edge_status, "scenario": "edge_case", "response_body": edge_body},
        {"status_code": err_status, "scenario": "error_case", "response_body": err_body},
    ]
    parameters = [
        {
            "name": k,
            "type": v.get("type", "string"),
            "required": k in required,
            "example": FIELD_DOCS.get(k, {}).get("example"),
            "description": FIELD_DOCS.get(k, {}).get("doc", f"{k} field"),
        }
        for k, v in props.items()
    ]
    return {
        "description": _description(tpl, d),
        "parameters": parameters,
        "sample_requests": sample_requests,
        "sample_responses": sample_responses,
        "response_schema": _response_schema(body),
        "headers": {"Content-Type": "application/json", "Accept": "application/json"},
        "auth_config": {"type": "none"} if d["auth"] == "public" else {"type": "bearer", "token_env": "DEMO_API_TOKEN"},
        "rate_limit": {"requests_per_minute": 60 if tpl["method"] == "GET" else 30},
        "assertions": [
            {"type": "status_code", "expected": status},
            {"type": "json_schema", "target": "response_schema"},
        ],
        "domain_tags": [tpl["cluster"], "demo", tpl["method"].lower()],
    }
