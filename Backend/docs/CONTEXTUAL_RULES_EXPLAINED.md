# Contextual Rules for Slot Extraction

## What Are Contextual Rules?

**Contextual rules** are domain-specific patterns that understand the **context** and **structure** of natural language queries, not just individual words.

Unlike simple regex (which looks for patterns like `email: X`), contextual rules understand **relationships between words** and **common phrasing patterns**.

---

## Examples of Contextual Rules

### **1. "for X and Y" Pattern**

**Rule:** When users say "for X and Y", they usually mean username and password.

```python
# Pattern
pattern = r"for\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"

# Matches
"login for john and pass123"
"authenticate for admin and SecureP@ss"
"sign in for user_123 and myPassword!"

# Extracts
{
  "username": "john",
  "password": "pass123"
}
```

**Why it's contextual:**
- Understands "for" indicates the values that follow
- Knows "and" separates two related values
- Infers first value = username, second = password

---

### **2. "credentials for/as X and Y" Pattern**

**Rule:** When users mention "credentials", the next values are username/password.

```python
# Pattern
pattern = r"credentials?\s+(?:for|as)\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"

# Matches
"login with credentials for john and pass123"
"authenticate using credentials as admin and SecureP@ss"
"use credentials for test_user and Test@123"

# Extracts
{
  "username": "john",
  "password": "pass123"
}
```

**Why it's contextual:**
- Recognizes "credentials" as a signal word
- Understands "for/as" introduces the credential values
- Maintains order: first = username, second = password

---

### **3. "with credentials as X and Y" Pattern**

**Rule:** "with credentials as" is another way to provide login info.

```python
# Pattern
pattern = r"with\s+(?:credentials?|the\s+credentials?)\s+as\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"

# Matches
"login with credentials as john and pass123"
"authenticate with the credentials as admin and SecureP@ss"

# Extracts
{
  "username": "john",
  "password": "pass123"
}
```

---

### **4. "with name X and Y" Pattern**

**Rule:** For profile updates, "with name X and Y" means name and another field.

```python
# Pattern
pattern = r"with\s+(?:name|user)\s+([a-zA-Z\s]+?)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"

# Matches
"update profile with name John Doe and newPassword123"
"change user Milan Kumar and pass@123"

# Extracts
{
  "name": "John Doe",
  "password": "newPassword123"
}
```

---

### **5. "to <email>" Pattern**

**Rule:** "to" followed by an email address means that's the target email.

```python
# Pattern
pattern = r"to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"

# Matches
"send reset link to ali@gmail.com"
"email verification to user@example.com"
"send invite to john.doe@company.com"

# Extracts
{
  "email": "ali@gmail.com"
}
```

**Why it's contextual:**
- Understands "to" indicates the recipient
- Knows what follows is likely an email address
- Different from just finding any email in the text

---

## Comparison: Regex vs Contextual Rules

### **Simple Regex (Not Contextual)**

```python
# Just looks for "email:" or "email ="
pattern = r"email[:\s=]+([a-zA-Z0-9._%+-]+@...)"

# Works for:
"email: ali@gmail.com" ✅
"email = ali@gmail.com" ✅

# Fails for:
"send to ali@gmail.com" ❌
"reset password for ali@gmail.com" ❌
```

### **Contextual Rule (Smart)**

```python
# Understands context words like "to", "for", "send"
patterns = [
    r"to\s+([a-zA-Z0-9._%+-]+@...)",      # "to X"
    r"for\s+([a-zA-Z0-9._%+-]+@...)",     # "for X"
    r"send\s+.*?\s+([a-zA-Z0-9._%+-]+@...)"  # "send ... X"
]

# Works for:
"send to ali@gmail.com" ✅
"reset password for ali@gmail.com" ✅
"email verification to user@test.com" ✅
```

---

## Real-World Example

### **Query:** `"login with credentials for john and pass123"`

#### **Without Contextual Rules:**

```python
# Simple regex only
slots_regex = {
  # Might find "john" but not know it's username
  # Might find "pass123" but not know it's password
}
```

#### **With Contextual Rules:**

```python
# Contextual pattern matches "for X and Y"
slots_contextual = {
  "username": "john",      # ✅ Correctly identified
  "password": "pass123"    # ✅ Correctly identified
}
```

---

## Implementation Example

```python
def extract_slots_contextual(self, query: str) -> Dict[str, str]:
    """
    Extract slots using contextual analysis
    Looks for common patterns like "for X and Y"
    """
    slots = {}
    
    # Pattern 1: "for X and Y" → username and password
    pattern = r"for\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        slots["username"] = match.group(1)
        slots["password"] = match.group(2)
    
    # Pattern 2: "credentials for X and Y"
    pattern = r"credentials?\s+(?:for|as)\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        slots["username"] = match.group(1)
        slots["password"] = match.group(2)
    
    # Pattern 3: "to <email>"
    pattern = r"to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        slots["email"] = match.group(1)
    
    # Pattern 4: "with name X and Y"
    pattern = r"with\s+(?:name|user)\s+([a-zA-Z\s]+?)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        slots["name"] = match.group(1).strip()
        if "password" not in slots:
            slots["password"] = match.group(2).strip()
    
    return slots
```

---

## Why Contextual Rules Matter

| Aspect | Simple Regex | Contextual Rules |
|--------|-------------|------------------|
| **Accuracy** | 50-60% | 80-90% |
| **Natural Language** | ❌ Rigid | ✅ Flexible |
| **User-Friendly** | ❌ Requires exact format | ✅ Understands variations |
| **Maintenance** | ✅ Easy | ⚠️ Requires domain knowledge |

---

## Contextual Rules vs AI Models

| Method | Accuracy | Speed | Cost | Flexibility |
|--------|----------|-------|------|-------------|
| **Contextual Rules** | 80-90% | ⚡ Instant | Free | ⚠️ Fixed patterns |
| **Llama/GPT** | 90-95% | 🐌 2-3 sec | $ | ✅ Learns new patterns |
| **Hybrid (Both)** | 95%+ | ⚡ Fast | $ | ✅ Best of both |

---

## When to Use Contextual Rules

✅ **Use when:**
- You have common, predictable patterns
- Speed is critical
- You want zero API costs
- Patterns are domain-specific

❌ **Don't use when:**
- Queries are highly varied
- You need to understand complex context
- Patterns change frequently

---

## Summary

**Contextual rules** are smart regex patterns that understand:
1. **Word relationships** ("for X and Y")
2. **Signal words** ("credentials", "to", "with")
3. **Common phrasings** in your domain
4. **Field order** (first = username, second = password)

They're **faster than AI** but **smarter than simple regex**, making them perfect for common patterns in your API testing domain! 🚀
