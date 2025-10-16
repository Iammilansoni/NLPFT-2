#!/usr/bin/env python3
"""
Comprehensive Test Suite - 100 Different API Query Variations
Testing all API types: login, logout, register, reset_password, update_profile,
upload_file, download_file, search, get_user, delete_account
"""
import json
import sys

# Try to import the optimized version first, fall back to regular version
try:
    from JSONoutput_generator_optimized import answer
    print("✅ Using optimized generator")
except ImportError:
    try:
        from JSONoutput_generator import answer
        print("✅ Using standard generator")
    except ImportError:
        print("❌ Error: Cannot import generator. Please install required dependencies.")
        sys.exit(1)

print("="*80)
print("🧪 COMPREHENSIVE API TEST SUITE - 100 DIFFERENT QUERY VARIATIONS")
print("="*80)

# Test queries organized by API type
test_queries = {
    "LOGIN (10 variations)": [
        # 1-10: LOGIN
        "login user pratul.ag with password Welcome#2025",
        "sign in to example.com using admin and SecurePass@123",
        "log me into github.com with username developer_pro password DevPass#456",
        "authenticate on api.stripe.com as testuser with pass Test@789",
        "I want to login to myapp.io user john.doe password JohnD@2025",
        "sign in frontend_pro User@321",
        "access portal.company.com with credentials mike.smith MikeS#999",
        "login to app.azure.com username azure_admin password Azure@2025",
        "log into dashboard.aws.com as root_user with RootPass#123",
        "sign in to prod.server.net user prod_admin password Pr0d@Admin",
    ],
    
    "LOGOUT (10 variations)": [
        # 11-20: LOGOUT
        "logout from example.com with token abc123xyz",
        "sign out of github.com using session token sess_abc123",
        "log out from api.server.com bearer token bearer_xyz789",
        "disconnect from portal.app.io token auth_token_456",
        "logout of mysite.com with authentication token jwt_abc123",
        "sign me out from app.google.com token google_sess_xyz",
        "end session on dashboard.com with token session_end_123",
        "logout from secure.site.net bearer bearer_secure_789",
        "sign out of admin.panel.com session token admin_sess_456",
        "terminate session at api.cloud.com token cloud_token_xyz",
    ],
    
    "REGISTER (10 variations)": [
        # 21-30: REGISTER
        "Please validate confedential avadhi and avdhi@123",
        "register new user john@example.com with password Test@2025",
        "sign up on github.com username newdev email dev@company.com password DevNew@123",
        "create account at api.service.com user service_user email user@service.com pass Service#456",
        "register on myapp.io as mike.wilson email mike.w@email.com password Mike@789",
        "sign up for portal.site.com username portal_user email portal@site.com password Portal#2025",
        "create new account on app.startup.io user startup_admin email admin@startup.io pass StartUp@123",
        "register at dashboard.cloud.com username cloud_user email cloud@email.com password Cloud#456",
        "sign up on secure.app.net user secure_admin email secure@app.net pass Secure@789",
        "create account for api.payment.com username payment_user email pay@ment.com password Pay@2025",
    ],
    
    "RESET_PASSWORD (10 variations)": [
        # 31-40: RESET PASSWORD
        "reset password for john.doe@example.com on example.com",
        "forgot password on github.com for developer@github.com",
        "recover password at api.server.com email admin@server.com",
        "reset my password on portal.app.io for user@app.io",
        "I forgot my password on mysite.com email forgot@mysite.com",
        "password recovery for dashboard.com using recovery@dashboard.com",
        "reset password on secure.net for secure@secure.net",
        "forgot my credentials at app.cloud.com email cloud@app.com",
        "recover account password on api.service.io for service@api.io",
        "reset password for admin.panel.com using admin@panel.com",
    ],
    
    "UPDATE_PROFILE (10 variations)": [
        # 41-50: UPDATE PROFILE
        "update profile on example.com user U12345 name John Doe phone +1-555-1234",
        "edit profile at github.com userid GH789 name Jane Smith phone +44-20-1234",
        "change my name on api.server.com user USR456 to Mike Wilson phone +91-98765",
        "update my details on portal.app.io id P999 name Sarah Connor phone +1-555-9999",
        "modify profile at mysite.com user M123 name Robert Brown phone +61-412-345",
        "edit user profile on dashboard.com userid D456 name Emily Davis phone +49-30-1234",
        "update account info on secure.net user SEC789 name David Lee phone +86-138-1234",
        "change profile on app.cloud.com id C321 name Lisa Wang phone +65-9123-4567",
        "modify user details at api.service.io user S654 name Tom Harris phone +33-6-1234",
        "update my info on admin.panel.com userid A987 name Anna Martinez phone +34-612-345",
    ],
    
    "UPLOAD_FILE (10 variations)": [
        # 51-60: UPLOAD FILE
        "upload report.pdf to example.com",
        "send presentation.pptx to api.server.com",
        "attach invoice.docx file to portal.app.io",
        "upload image.png to github.com",
        "send data.csv file to mysite.com",
        "attach spreadsheet.xlsx to dashboard.com",
        "upload video.mp4 to secure.net",
        "send archive.zip file to app.cloud.com",
        "attach document.txt to api.service.io",
        "upload backup.sql to admin.panel.com",
    ],
    
    "DOWNLOAD_FILE (10 variations)": [
        # 61-70: DOWNLOAD FILE
        "download file F12345 from example.com",
        "get file DOC789 from api.server.com",
        "fetch file IMG456 from portal.app.io",
        "download document F999 from github.com",
        "retrieve file DATA123 from mysite.com",
        "get file RPT456 from dashboard.com",
        "fetch file VID789 from secure.net",
        "download file ARC321 from app.cloud.com",
        "retrieve file BKP654 from api.service.io",
        "get file LOG987 from admin.panel.com",
    ],
    
    "SEARCH (10 variations)": [
        # 71-80: SEARCH
        "find files type:pdf about marketing plan on example.com",
        "search for project documents on api.server.com",
        "lookup user reports type:docx on portal.app.io",
        "find invoices type:pdf from date:2025-01 on github.com",
        "search financial data type:xlsx on mysite.com",
        "lookup customer records type:csv date:2024-12 on dashboard.com",
        "find technical specs type:pdf on secure.net",
        "search meeting notes type:docx on app.cloud.com",
        "lookup product images type:png on api.service.io",
        "find system logs type:txt date:2025-10 on admin.panel.com",
    ],
    
    "GET_USER (10 variations)": [
        # 81-90: GET USER
        "get user details for U12345 from example.com",
        "fetch user info for USR789 on api.server.com",
        "retrieve user U456 from portal.app.io",
        "get user details U999 on github.com",
        "fetch account info for M123 from mysite.com",
        "retrieve user data D456 on dashboard.com",
        "get user profile SEC789 from secure.net",
        "fetch user details C321 on app.cloud.com",
        "retrieve user info S654 from api.service.io",
        "get account details A987 on admin.panel.com",
    ],
    
    "DELETE_ACCOUNT (10 variations)": [
        # 91-100: DELETE ACCOUNT
        "delete account U12345 from example.com confirmed",
        "remove account USR789 on api.server.com yes confirm",
        "close account U456 from portal.app.io confirmed",
        "delete user U999 on github.com with confirmation",
        "remove my account M123 from mysite.com yes",
        "close user account D456 on dashboard.com confirmed",
        "delete account SEC789 from secure.net confirm yes",
        "remove user C321 on app.cloud.com confirmed",
        "close account S654 from api.service.io yes",
        "delete user account A987 on admin.panel.com confirmed",
    ],
}

# Track statistics
total_tests = 0
successful = 0
failed = 0
results_by_api = {}

# Run all tests
for category, queries in test_queries.items():
    print(f"\n{'='*80}")
    print(f"📁 {category}")
    print(f"{'='*80}")
    
    for i, query in enumerate(queries, 1):
        total_tests += 1
        global_index = total_tests
        
        print(f"\n{global_index}. Query: {query}")
        print("-"*80)
        
        try:
            result = answer(query)
            api_name = result.get("api", "unknown")
            
            # Track results by API
            if api_name not in results_by_api:
                results_by_api[api_name] = {"success": 0, "total": 0}
            results_by_api[api_name]["total"] += 1
            results_by_api[api_name]["success"] += 1
            
            print(json.dumps(result, indent=2))
            print("✅ SUCCESS")
            successful += 1
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
            # Still track failed attempts
            if "unknown" not in results_by_api:
                results_by_api["unknown"] = {"success": 0, "total": 0}
            results_by_api["unknown"]["total"] += 1

# Print summary statistics
print("\n" + "="*80)
print("📊 TEST SUMMARY STATISTICS")
print("="*80)
print(f"\n✅ Total Tests Run: {total_tests}")
print(f"✅ Successful: {successful} ({successful/total_tests*100:.1f}%)")
print(f"❌ Failed: {failed} ({failed/total_tests*100:.1f}%)")

print("\n" + "-"*80)
print("📈 Results by API Type:")
print("-"*80)
for api_name, stats in sorted(results_by_api.items()):
    success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
    print(f"{api_name:20s}: {stats['success']:2d}/{stats['total']:2d} ({success_rate:5.1f}%)")

print("\n" + "="*80)
print("✅ Testing Complete!")
print("="*80)
