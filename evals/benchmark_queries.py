"""
Held-out routing benchmark — 180 labeled query -> template pairs.
=================================================================

None of these strings appear in `api_surface.py` utterances. The index is built
from utterances only; the model never sees these queries during indexing.

FOUR DIFFICULTY TIERS
---------------------
direct         Plain, unambiguous phrasing. Any working retriever should get
               these. If Hit@1 is not near-perfect here, something is broken.

paraphrase     Same intent, different vocabulary — minimal lexical overlap with
               the indexed utterances. Measures genuine semantic generalisation
               rather than keyword matching.

colloquial     Casual, terse, typo'd, or slang phrasing of the kind real users
               actually type. Measures robustness to distribution shift.

hard_negative  THE TIER THAT MATTERS. Each query is lexically closest to a
               SIBLING template in the same cluster but semantically belongs to
               the labeled one. Example: "I'm locked out and need a new password"
               shares almost every token with Password_Change, but the user
               cannot authenticate, so it must route to Password_Reset_Request.

               Bi-encoder recall reliably surfaces all siblings in the top-50 and
               reliably picks the wrong one at rank 1. This tier is where a
               cross-encoder either proves its value or fails to.

Reporting metrics per-tier — not just in aggregate — is what makes the result
diagnostic. A single headline Hit@1 number can hide a reranker that improves
easy queries and regresses hard ones.
"""

from __future__ import annotations

from typing import Any, Dict, List

# api_name -> tier -> [queries]
BENCHMARK: Dict[str, Dict[str, List[str]]] = {
    "User_Login": {
        "direct": [
            "authenticate with email dana@shop.io and password Passw0rd",
            "log in the user with these credentials",
        ],
        "paraphrase": [
            "verify my identity so I can access the dashboard",
            "grant me an access token for my account",
            "begin an authenticated session",
        ],
        "colloquial": [
            "lemme in, email is dana@shop.io pw Passw0rd",
            "signin plz",
        ],
        "hard_negative": [
            "I know my password and just want to get into my account",
            "use my existing password to access the system",
        ],
    },
    "User_Logout": {
        "direct": [
            "log out the current user",
            "end the session for this device",
        ],
        "paraphrase": [
            "close my authenticated session and invalidate the token",
            "drop my credentials from this browser",
            "make my current token stop working",
        ],
        "colloquial": [
            "sign out kthx",
            "get me outta here",
        ],
        "hard_negative": [
            "invalidate the refresh token I am currently holding",
            "kill my session without deleting my account",
        ],
    },
    "Password_Reset_Request": {
        "direct": [
            "send a password reset email to dana@shop.io",
            "begin the forgot password flow",
        ],
        "paraphrase": [
            "I am locked out of my account and need a recovery link",
            "mail me instructions to regain access",
            "trigger account recovery for this address",
        ],
        "colloquial": [
            "cant remember my pw send me the link",
            "forgot pw help",
        ],
        "hard_negative": [
            "I am locked out and need a new password",
            "I need to set a different password but I cannot sign in",
        ],
    },
    "Password_Reset_Confirm": {
        "direct": [
            "complete the reset using token tk_9931 and password N3wPass",
            "submit my new password along with the reset token",
        ],
        "paraphrase": [
            "finalise account recovery with the emailed code and a fresh secret",
            "redeem the recovery token to set my credentials",
            "use the link code to establish a new password",
        ],
        "colloquial": [
            "got the code tk_9931, new pw is N3wPass",
            "here's my reset code, change it",
        ],
        "hard_negative": [
            "set a new password for my account using the code I received",
            "update my password now that I have the reset token",
        ],
    },
    "Password_Change": {
        "direct": [
            "change my password from Old1234 to New5678",
            "update the password on my authenticated account",
        ],
        "paraphrase": [
            "swap my current secret for a different one while signed in",
            "rotate my credentials as a security precaution",
            "replace my working password with a stronger one",
        ],
        "colloquial": [
            "wanna change my pw, current one is Old1234",
            "new password pls, i know the old one",
        ],
        "hard_negative": [
            "I want a new password and I still remember the current one",
            "set a different password, no reset link needed",
        ],
    },
    "User_Register": {
        "direct": [
            "create an account for erin@lab.dev with password Init1al",
            "register a new user named Erin Blake",
        ],
        "paraphrase": [
            "provision a fresh identity in the system",
            "enrol a new person with an email and secret",
            "add someone to the platform for the first time",
        ],
        "colloquial": [
            "signup erin@lab.dev / Init1al",
            "make me a new acct",
        ],
        "hard_negative": [
            "set up credentials for a person who has never logged in before",
            "give this email address an account and a password",
        ],
    },
    "Email_Verify": {
        "direct": [
            "verify erin@lab.dev with the one time code 553201",
            "confirm the email address using the OTP",
        ],
        "paraphrase": [
            "prove ownership of the mailbox with the six digit code",
            "mark this address as validated using the token I got",
            "finish activating the account with the emailed digits",
        ],
        "colloquial": [
            "code is 553201, verify me",
            "otp 553201 done",
        ],
        "hard_negative": [
            "submit the code that was emailed to me after signing up",
            "use the emailed code to activate my new account",
        ],
    },
    "Token_Refresh": {
        "direct": [
            "refresh the access token using rt_5512",
            "issue a new access token from my refresh token",
        ],
        "paraphrase": [
            "extend my session without asking for credentials again",
            "mint a fresh short lived JWT",
            "my bearer token lapsed, give me another",
        ],
        "colloquial": [
            "token expired gimme new one",
            "renew jwt rt_5512",
        ],
        "hard_negative": [
            "I have a valid refresh token and need access again",
            "keep me signed in without re-entering my password",
        ],
    },
    "Get_User_Profile": {
        "direct": [
            "fetch the profile of user 7734",
            "show me the record for dana@shop.io",
        ],
        "paraphrase": [
            "what information do we store about this person",
            "read back a single account's attributes",
            "pull up one specific user's details",
        ],
        "colloquial": [
            "who is user 7734",
            "gimme info on that user",
        ],
        "hard_negative": [
            "get the details for one particular user id",
            "read the profile fields without changing them",
        ],
    },
    "Update_User_Profile": {
        "direct": [
            "set the full name of user 7734 to Dana Reed",
            "patch the timezone field on this profile",
        ],
        "paraphrase": [
            "amend a few attributes on someone's account record",
            "correct the stored display name",
            "adjust locale settings for this person",
        ],
        "colloquial": [
            "rename user 7734 to Dana Reed",
            "fix my tz to Europe/Berlin",
        ],
        "hard_negative": [
            "change details on a user without removing the account",
            "modify profile fields for user 7734",
        ],
    },
    "Delete_User": {
        "direct": [
            "delete the account belonging to user 7734",
            "permanently remove dana@shop.io from the system",
        ],
        "paraphrase": [
            "wipe this person and everything they own",
            "tear down an account irreversibly",
            "expunge the user record entirely",
        ],
        "colloquial": [
            "nuke user 7734",
            "delete my acct forever",
        ],
        "hard_negative": [
            "get rid of this user completely rather than editing them",
            "remove the account for good, not just deactivate fields",
        ],
    },
    "List_Users": {
        "direct": [
            "return the first 50 users",
            "list accounts filtered by role admin",
        ],
        "paraphrase": [
            "give me a roster of everyone registered",
            "page through the full membership",
            "enumerate the directory",
        ],
        "colloquial": [
            "show all users",
            "who's on this account",
        ],
        "hard_negative": [
            "get many users at once instead of a single one",
            "browse the collection of user records",
        ],
    },
    "Create_Order": {
        "direct": [
            "place an order for customer 4410 with 3 units of SKU-91",
            "create a new order with two line items",
        ],
        "paraphrase": [
            "register a fresh purchase against this account",
            "open a sales record for these goods",
            "commit a basket to checkout",
        ],
        "colloquial": [
            "order 3x SKU-91 for cust 4410",
            "buy this stuff",
        ],
        "hard_negative": [
            "start a brand new order rather than looking one up",
            "submit a purchase for a customer",
        ],
    },
    "Cancel_Order": {
        "direct": [
            "cancel order 8820 before it ships",
            "call off the order for this customer",
        ],
        "paraphrase": [
            "halt fulfilment on an order that has not left the warehouse",
            "withdraw a pending purchase",
            "scrap this order",
        ],
        "colloquial": [
            "cancel 8820 pls",
            "dont ship that order",
        ],
        "hard_negative": [
            "stop order 8820 but do not move any money",
            "kill an order that has not shipped, no refund needed",
        ],
    },
    "Get_Order_Status": {
        "direct": [
            "what is the current state of order 8820",
            "show the fulfilment status of this order",
        ],
        "paraphrase": [
            "where is my parcel right now",
            "read back the progress of a purchase",
            "has this shipment moved yet",
        ],
        "colloquial": [
            "wheres my order 8820",
            "order status?",
        ],
        "hard_negative": [
            "look at order 8820 without changing anything",
            "check on an order rather than cancelling it",
        ],
    },
    "Refund_Order": {
        "direct": [
            "refund 32.50 against order 8820",
            "issue a money-back on this completed order",
        ],
        "paraphrase": [
            "return the customer's funds for a delivered purchase",
            "credit back part of what they paid",
            "reverse the charge on a fulfilled order",
        ],
        "colloquial": [
            "give em their money back on 8820",
            "refund 32.50 plz",
        ],
        "hard_negative": [
            "send money back for order 8820 that already shipped",
            "reverse payment on a completed order, not cancel it",
        ],
    },
    "Create_Payment": {
        "direct": [
            "charge 250 USD to payment method pm_442",
            "take a payment of 18.99 GBP",
        ],
        "paraphrase": [
            "debit the customer's card for this amount",
            "initiate a monetary capture",
            "run the transaction for two hundred fifty dollars",
        ],
        "colloquial": [
            "bill em 250 usd",
            "charge card pm_442",
        ],
        "hard_negative": [
            "move money from the customer now rather than checking a charge",
            "start a new charge instead of reading an old one",
        ],
    },
    "Get_Payment_Status": {
        "direct": [
            "check whether payment pay_774 succeeded",
            "show the state of this transaction",
        ],
        "paraphrase": [
            "did the card go through or get declined",
            "read back the outcome of a charge",
            "is the money settled yet",
        ],
        "colloquial": [
            "did pay_774 work",
            "payment ok?",
        ],
        "hard_negative": [
            "look up an existing charge rather than creating one",
            "tell me about payment pay_774 without charging anything",
        ],
    },
    "Send_Notification": {
        "direct": [
            "send an email to user 7734 saying their order shipped",
            "push a message to this user's device",
        ],
        "paraphrase": [
            "alert the customer that something changed",
            "deliver a one-off message over SMS",
            "ping the user with an update",
        ],
        "colloquial": [
            "text user 7734 that its shipped",
            "notify them",
        ],
        "hard_negative": [
            "actually deliver a message rather than changing settings",
            "send something to user 7734 over the sms channel now",
        ],
    },
    "Update_Notification_Prefs": {
        "direct": [
            "disable SMS notifications for user 7734",
            "change which channels this user is subscribed to",
        ],
        "paraphrase": [
            "stop sending me marketing mail",
            "adjust my alert subscriptions",
            "configure delivery channel preferences",
        ],
        "colloquial": [
            "turn off texts for 7734",
            "unsubscribe me",
        ],
        "hard_negative": [
            "change the sms setting for user 7734 without sending anything",
            "alter notification channels rather than dispatching a message",
        ],
    },
}


def load_benchmark() -> List[Dict[str, Any]]:
    """Flatten BENCHMARK into a list of labeled eval cases with stable ids."""
    cases: List[Dict[str, Any]] = []
    counter = 0
    for api_name, tiers in BENCHMARK.items():
        for tier, queries in tiers.items():
            for query in queries:
                counter += 1
                cases.append(
                    {
                        "id": f"q{counter:03d}",
                        "query": query,
                        "expected_api": api_name,
                        "tier": tier,
                    }
                )
    return cases


TIERS = ("direct", "paraphrase", "colloquial", "hard_negative")


if __name__ == "__main__":
    cases = load_benchmark()
    from collections import Counter

    print(f"total cases      : {len(cases)}")
    print(f"templates covered: {len(BENCHMARK)}")
    for tier, n in Counter(c["tier"] for c in cases).most_common():
        print(f"  {tier:<15}: {n}")
