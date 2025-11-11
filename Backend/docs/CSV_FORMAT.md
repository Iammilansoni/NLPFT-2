# CSV Dataset Format

## Standard Format (Matching csv_dataset.csv)

All CSV datasets must follow this format:

```csv
query,api,endpoint,request,response
"login -> user name=avsinghal pass=Secure*888",login,<base_url>/api/login,"{""username"": ""avsinghal"", ""password"": ""Secure*888""}","{""definition"": ""Authenticates user with username and password credentials and starts a new session.""}"
```

## Column Definitions

| Column | Required | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `query` | ✅ Yes | String | Natural language query text | `"login -> user name=avsinghal pass=Secure*888"` |
| `api` | ✅ Yes | String | API intent name | `"login"` |
| `endpoint` | ⚠️ Optional | String | API endpoint URL | `"<base_url>/api/login"` |
| `request` | ⚠️ Optional | JSON String | Request parameters as JSON | `"{\"username\": \"avsinghal\", \"password\": \"Secure*888\"}"` |
| `response` | ⚠️ Optional | JSON String | Response definition as JSON | `"{\"definition\": \"...\"}"` |

## Examples

### Minimal Example
```csv
query,api
"login with john",login
```

### Full Example
```csv
query,api,endpoint,request,response
"login with username admin and password Pass123",login,<base_url>/api/login,"{""username"": ""admin"", ""password"": ""Pass123""}","{""definition"": ""Authenticates user with username and password credentials and starts a new session.""}"
"reset password for user@example.com",reset_password,<base_url>/api/reset_password,"{""email"": ""user@example.com""}","{""definition"": ""Sends password reset email to the specified email address.""}"
```

## Data Sources

All three data sources use this same format:

1. **Your csv_dataset.csv** - Already in this format ✅
2. **User Uploaded CSV** - Must follow this format
3. **Gemini Generated Dataset** - Automatically generates in this format

## Redis Storage

All CSV data is converted to Redis with this schema:
- `query` → `query`
- `api` → `api`
- `endpoint` → `endpoint`
- `request` → `request` (stored as JSON string)
- `response` → `response` (stored as JSON string)
- `query_embedding` → Generated 384-dim vector

## Notes

- The `request` field should contain a JSON object with the extracted parameters/slots
- The `response` field should contain a JSON object with API response definition
- If `endpoint`, `request`, or `response` are missing, defaults will be generated
- All embeddings are stored with hash-based keys: `api:{hash_id}` for deduplication

