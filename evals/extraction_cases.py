"""
Extraction benchmark: 100 requests with the exact request-body values they carry.

Routing (evals/benchmark_queries.py) measures which endpoint a request goes to.
This set measures the second half: whether the values in the request come out
correctly, and -- just as important -- whether anything is invented.

Every case names its API (routing is not under test here) and the values a
careful human would extract. Values the request does not state are absent from
`expected`: a system that fills them in is hallucinating, and is scored so.

About a fifth of the cases leave a required value out on purpose ("log me in"
has no email or password). They exist to catch invented values.

Conventions for gold values:
  * ids are the bare identifier the user typed: "order #8820" -> "8820"
  * amounts are numbers: "$25" -> 25
  * currency is the ISO code, and only when the request names the currency
    (as a code or a currency word)
  * booleans only when the request clearly turns something on or off
  * `ANY_ITEMS` marks a non-empty list whose exact shape is not scored
"""

from typing import Any, Dict, List

ANY_ITEMS = "__any_nonempty_list__"

CASES: List[Dict[str, Any]] = [
    # -- User_Login --------------------------------------------------------
    {"api": "User_Login", "query": "log in as maria.lopez@acme.io with password Tr0ub4dor&3",
     "expected": {"email": "maria.lopez@acme.io", "password": "Tr0ub4dor&3"}},
    {"api": "User_Login", "query": "sign me in: email kenji@example.org, password hunter22",
     "expected": {"email": "kenji@example.org", "password": "hunter22"}},
    {"api": "User_Login", "query": "authenticate ops-bot@corp.dev using the password S3cure!pass",
     "expected": {"email": "ops-bot@corp.dev", "password": "S3cure!pass"}},
    {"api": "User_Login", "query": "log me in please", "expected": {}},
    {"api": "User_Login", "query": "login for anna@shop.io", "expected": {"email": "anna@shop.io"}},

    # -- User_Logout -------------------------------------------------------
    {"api": "User_Logout", "query": "log out and revoke refresh token rt_7f3a9c21",
     "expected": {"refresh_token": "rt_7f3a9c21"}},
    {"api": "User_Logout", "query": "sign me out, my refresh token is eyJhbGciOi.abc.def",
     "expected": {"refresh_token": "eyJhbGciOi.abc.def"}},
    {"api": "User_Logout", "query": "end the session for token rtok-99812",
     "expected": {"refresh_token": "rtok-99812"}},
    {"api": "User_Logout", "query": "log me out", "expected": {}},
    {"api": "User_Logout", "query": "invalidate refresh token 4f9e2b7d", "expected": {"refresh_token": "4f9e2b7d"}},

    # -- Password_Reset_Request --------------------------------------------
    {"api": "Password_Reset_Request", "query": "send a password reset link to lee.chen@mail.com",
     "expected": {"email": "lee.chen@mail.com"}},
    {"api": "Password_Reset_Request", "query": "I forgot my password, my email is priya.n@startup.ai",
     "expected": {"email": "priya.n@startup.ai"}},
    {"api": "Password_Reset_Request", "query": "reset password for account support@helpdesk.co",
     "expected": {"email": "support@helpdesk.co"}},
    {"api": "Password_Reset_Request", "query": "I can't remember my password", "expected": {}},
    {"api": "Password_Reset_Request", "query": "email a reset code to J.Doe@Example.COM",
     "expected": {"email": "J.Doe@Example.COM"}},

    # -- Password_Reset_Confirm --------------------------------------------
    {"api": "Password_Reset_Confirm", "query": "confirm reset with token 8f2c1a and new password Blue#Sky42",
     "expected": {"token": "8f2c1a", "new_password": "Blue#Sky42"}},
    {"api": "Password_Reset_Confirm", "query": "use reset token RST-55120 to set my password to Winter2026!",
     "expected": {"token": "RST-55120", "new_password": "Winter2026!"}},
    {"api": "Password_Reset_Confirm", "query": "finish the password reset, new password is c0ffeeTime",
     "expected": {"new_password": "c0ffeeTime"}},
    {"api": "Password_Reset_Confirm", "query": "complete my password reset", "expected": {}},
    {"api": "Password_Reset_Confirm", "query": "token a1b2c3d4, new password Qwerty!789",
     "expected": {"token": "a1b2c3d4", "new_password": "Qwerty!789"}},

    # -- Password_Change ---------------------------------------------------
    {"api": "Password_Change", "query": "change my password from oldpass1 to NewPass#9",
     "expected": {"current_password": "oldpass1", "new_password": "NewPass#9"}},
    {"api": "Password_Change", "query": "update password: current is Summer2025, new one is Autumn2026!",
     "expected": {"current_password": "Summer2025", "new_password": "Autumn2026!"}},
    {"api": "Password_Change", "query": "my current password is abc123 and I want it to be Zyx987$$",
     "expected": {"current_password": "abc123", "new_password": "Zyx987$$"}},
    {"api": "Password_Change", "query": "I want to change my password", "expected": {}},
    {"api": "Password_Change", "query": "set my new password to P@ssw0rd2026",
     "expected": {"new_password": "P@ssw0rd2026"}},

    # -- User_Register -----------------------------------------------------
    {"api": "User_Register", "query": "create an account for Omar Haddad, omar.h@mailbox.org, password Dune!1965",
     "expected": {"full_name": "Omar Haddad", "email": "omar.h@mailbox.org", "password": "Dune!1965"}},
    {"api": "User_Register", "query": "sign up with email sara@kite.app and password kiteFly88",
     "expected": {"email": "sara@kite.app", "password": "kiteFly88"}},
    {"api": "User_Register", "query": "register a new user named Li Wei with email li.wei@corp.cn",
     "expected": {"full_name": "Li Wei", "email": "li.wei@corp.cn"}},
    {"api": "User_Register", "query": "I'd like to create an account", "expected": {}},
    {"api": "User_Register", "query": "new signup: tom@garden.net / Tulips#4ever",
     "expected": {"email": "tom@garden.net", "password": "Tulips#4ever"}},

    # -- Email_Verify ------------------------------------------------------
    {"api": "Email_Verify", "query": "verify maria@acme.io with code 482913",
     "expected": {"email": "maria@acme.io", "otp": "482913"}},
    {"api": "Email_Verify", "query": "my verification code is 007341 for dev@tools.io",
     "expected": {"email": "dev@tools.io", "otp": "007341"}},
    {"api": "Email_Verify", "query": "confirm email jo@post.de using OTP 55-21-90",
     "expected": {"email": "jo@post.de", "otp": "55-21-90"}},
    {"api": "Email_Verify", "query": "verify my email address", "expected": {}},
    {"api": "Email_Verify", "query": "the one-time code is 919191", "expected": {"otp": "919191"}},

    # -- Token_Refresh -----------------------------------------------------
    {"api": "Token_Refresh", "query": "refresh my access token using rt_55ab12",
     "expected": {"refresh_token": "rt_55ab12"}},
    {"api": "Token_Refresh", "query": "get a new access token with refresh token zz9-plural-z-alpha",
     "expected": {"refresh_token": "zz9-plural-z-alpha"}},
    {"api": "Token_Refresh", "query": "exchange refresh token 3c3c3c for a fresh token",
     "expected": {"refresh_token": "3c3c3c"}},
    {"api": "Token_Refresh", "query": "my session expired, refresh it", "expected": {}},
    {"api": "Token_Refresh", "query": "rotate token REFRESH-8841",
     "expected": {"refresh_token": "REFRESH-8841"}},

    # -- Get_User_Profile --------------------------------------------------
    {"api": "Get_User_Profile", "query": "show the profile of user 4821", "expected": {"user_id": "4821"}},
    {"api": "Get_User_Profile", "query": "get details for user id u_77af", "expected": {"user_id": "u_77af"}},
    {"api": "Get_User_Profile", "query": "who is user #10293?", "expected": {"user_id": "10293"}},
    {"api": "Get_User_Profile", "query": "show me my profile", "expected": {}},
    {"api": "Get_User_Profile", "query": "fetch account 5566 info", "expected": {"user_id": "5566"}},

    # -- Update_User_Profile -----------------------------------------------
    {"api": "Update_User_Profile", "query": "rename user 4821 to Alice Cooper",
     "expected": {"user_id": "4821", "full_name": "Alice Cooper"}},
    {"api": "Update_User_Profile", "query": "set the timezone of user 3310 to Europe/Berlin",
     "expected": {"user_id": "3310", "timezone": "Europe/Berlin"}},
    {"api": "Update_User_Profile", "query": "user u_9 should be called Grace Hopper with timezone America/New_York",
     "expected": {"user_id": "u_9", "full_name": "Grace Hopper", "timezone": "America/New_York"}},
    {"api": "Update_User_Profile", "query": "change my display name to Sam Rivera",
     "expected": {"full_name": "Sam Rivera"}},
    {"api": "Update_User_Profile", "query": "edit my profile", "expected": {}},

    # -- Delete_User -------------------------------------------------------
    {"api": "Delete_User", "query": "delete user 4821", "expected": {"user_id": "4821"}},
    {"api": "Delete_User", "query": "permanently remove account u_aa12", "expected": {"user_id": "u_aa12"}},
    {"api": "Delete_User", "query": "close the account of user #778 forever", "expected": {"user_id": "778"}},
    {"api": "Delete_User", "query": "delete my account", "expected": {}},
    {"api": "Delete_User", "query": "wipe user id 900001 from the system", "expected": {"user_id": "900001"}},

    # -- List_Users --------------------------------------------------------
    {"api": "List_Users", "query": "list users on page 3", "expected": {"page": 3}},
    {"api": "List_Users", "query": "show 50 users per page", "expected": {"limit": 50}},
    {"api": "List_Users", "query": "list all admin users", "expected": {"role": "admin"}},
    {"api": "List_Users", "query": "page 2 of editors, 25 at a time", "expected": {"page": 2, "role": "editor", "limit": 25}},
    {"api": "List_Users", "query": "list the users", "expected": {}},

    # -- Create_Order ------------------------------------------------------
    {"api": "Create_Order", "query": "place an order for customer 991 with 2 widgets",
     "expected": {"customer_id": "991", "items": ANY_ITEMS}},
    {"api": "Create_Order", "query": "customer c_551 wants 3 units of SKU-44",
     "expected": {"customer_id": "c_551", "items": ANY_ITEMS}},
    {"api": "Create_Order", "query": "order 1 laptop and 2 mice for customer 12",
     "expected": {"customer_id": "12", "items": ANY_ITEMS}},
    {"api": "Create_Order", "query": "create a new order", "expected": {}},
    {"api": "Create_Order", "query": "new order for customer 4040", "expected": {"customer_id": "4040"}},

    # -- Cancel_Order ------------------------------------------------------
    {"api": "Cancel_Order", "query": "cancel order 8820", "expected": {"order_id": "8820"}},
    {"api": "Cancel_Order", "query": "cancel order #5512 because I ordered the wrong size",
     "expected": {"order_id": "5512", "reason": "I ordered the wrong size"}},
    {"api": "Cancel_Order", "query": "please cancel ORD-2291, reason: found it cheaper",
     "expected": {"order_id": "ORD-2291", "reason": "found it cheaper"}},
    {"api": "Cancel_Order", "query": "cancel my order", "expected": {}},
    {"api": "Cancel_Order", "query": "stop order o_77 from shipping", "expected": {"order_id": "o_77"}},

    # -- Get_Order_Status --------------------------------------------------
    {"api": "Get_Order_Status", "query": "where is order 8820?", "expected": {"order_id": "8820"}},
    {"api": "Get_Order_Status", "query": "track order #44102", "expected": {"order_id": "44102"}},
    {"api": "Get_Order_Status", "query": "status of ORD-9931 please", "expected": {"order_id": "ORD-9931"}},
    {"api": "Get_Order_Status", "query": "has my order shipped yet?", "expected": {}},
    {"api": "Get_Order_Status", "query": "check order id o_1234", "expected": {"order_id": "o_1234"}},

    # -- Refund_Order ------------------------------------------------------
    {"api": "Refund_Order", "query": "refund 25 dollars on order 8820", "expected": {"order_id": "8820", "amount": 25}},
    {"api": "Refund_Order", "query": "issue a full refund for order #6612", "expected": {"order_id": "6612"}},
    {"api": "Refund_Order", "query": "refund $12.50 for ORD-771", "expected": {"order_id": "ORD-771", "amount": 12.5}},
    {"api": "Refund_Order", "query": "I want my money back", "expected": {}},
    {"api": "Refund_Order", "query": "give back 99 on order 300", "expected": {"order_id": "300", "amount": 99}},

    # -- Create_Payment ----------------------------------------------------
    {"api": "Create_Payment", "query": "charge 120 USD to card pm_88",
     "expected": {"amount": 120, "currency": "USD", "method_id": "pm_88"}},
    {"api": "Create_Payment", "query": "take a payment of 99.50 EUR", "expected": {"amount": 99.5, "currency": "EUR"}},
    {"api": "Create_Payment", "query": "collect 40 euros using payment method pm_card_visa",
     "expected": {"amount": 40, "currency": "EUR", "method_id": "pm_card_visa"}},
    {"api": "Create_Payment", "query": "create a payment", "expected": {}},
    {"api": "Create_Payment", "query": "bill 15 GBP", "expected": {"amount": 15, "currency": "GBP"}},

    # -- Get_Payment_Status ------------------------------------------------
    {"api": "Get_Payment_Status", "query": "status of payment pay_3Kx9", "expected": {"payment_id": "pay_3Kx9"}},
    {"api": "Get_Payment_Status", "query": "did payment 77120 go through?", "expected": {"payment_id": "77120"}},
    {"api": "Get_Payment_Status", "query": "check payment id PMT-4410", "expected": {"payment_id": "PMT-4410"}},
    {"api": "Get_Payment_Status", "query": "did my payment succeed?", "expected": {}},
    {"api": "Get_Payment_Status", "query": "look up transaction pay_zz01", "expected": {"payment_id": "pay_zz01"}},

    # -- Send_Notification -------------------------------------------------
    {"api": "Send_Notification", "query": "send an sms to user 4821 saying your order shipped",
     "expected": {"user_id": "4821", "channel": "sms", "body": "your order shipped"}},
    {"api": "Send_Notification", "query": "email user u_12 the message: Welcome aboard!",
     "expected": {"user_id": "u_12", "channel": "email", "body": "Welcome aboard!"}},
    {"api": "Send_Notification", "query": "push notify user 3003: Your ride is here",
     "expected": {"user_id": "3003", "channel": "push", "body": "Your ride is here"}},
    {"api": "Send_Notification", "query": "send a notification", "expected": {}},
    {"api": "Send_Notification", "query": "text user 88 that the meeting moved",
     "expected": {"user_id": "88", "channel": "sms", "body": "the meeting moved"}},

    # -- Update_Notification_Prefs -----------------------------------------
    {"api": "Update_Notification_Prefs", "query": "turn off SMS notifications for user 4821",
     "expected": {"user_id": "4821", "sms_enabled": False}},
    {"api": "Update_Notification_Prefs", "query": "enable email alerts for user u_5",
     "expected": {"user_id": "u_5", "email_enabled": True}},
    {"api": "Update_Notification_Prefs", "query": "user 77: no more emails, but keep texts on",
     "expected": {"user_id": "77", "email_enabled": False, "sms_enabled": True}},
    {"api": "Update_Notification_Prefs", "query": "change my notification settings", "expected": {}},
    {"api": "Update_Notification_Prefs", "query": "disable sms for user 1200", "expected": {"user_id": "1200", "sms_enabled": False}},
]
