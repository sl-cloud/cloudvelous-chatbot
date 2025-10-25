# Cloudvelous Chat Assistant - User Manual

**Version:** 0.3.0
**Last Updated:** October 25, 2025

A complete guide to using the Cloudvelous Chat Assistant from asking questions to training the AI.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [🔐 Authentication Setup (REQUIRED FOR ADMIN)](#authentication-setup)
4. [Basic Workflow](#basic-workflow)
5. [Step-by-Step Guide](#step-by-step-guide)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Introduction

### What is Cloudvelous Chat Assistant?

Cloudvelous is an intelligent chatbot that answers questions about your GitHub repositories using:
- **RAG (Retrieval-Augmented Generation)**: Finds relevant documentation and uses it to generate accurate answers
- **Self-Learning**: Gets smarter over time based on your feedback
- **Workflow Memory**: Remembers successful patterns to improve future answers

### How Does It Work?

```
Your Question
    ↓
[1. Embed your question into a vector]
    ↓
[2. Search for similar past successful answers]
    ↓
[3. Find relevant documentation chunks]
    ↓
[4. Generate answer using AI + documentation]
    ↓
Your Answer
    ↓
[You provide feedback: ✓ or ✗]
    ↓
[System learns and improves]
```

---

## Getting Started

### Prerequisites

1. **Backend is running:**
   ```bash
   cd /home/steve/repos/portfolio/cloudvelous-chatbot
   docker compose up -d
   ```

2. **Verify API is accessible:**
   ```bash
   curl http://localhost:8000/health
   ```

   You should see:
   ```json
   {
     "status": "healthy",
     "version": "0.3.0",
     "phase": "3"
   }
   ```

3. **Check all services are running:**
   ```bash
   docker compose ps
   ```

   Expected output:
   ```
   NAME                              STATUS
   cloudvelous-chatbot-backend       running
   cloudvelous-chatbot-db            running (healthy)
   cloudvelous-chatbot-postadmin     running
   ```

### Access Methods

**Option 1: Swagger UI (Recommended for beginners)**
- URL: http://localhost:8000/docs
- Visual interface with "Try it out" buttons
- Built-in authentication
- Interactive testing

**Option 2: cURL (Terminal)**
- Fast for testing
- Good for automation
- Copy-paste ready examples

**Option 3: Python Scripts**
- Most flexible
- Best for workflows
- Full code examples provided

---

## 🔐 Authentication Setup

### Understanding Authentication in Cloudvelous

**Two Types of Operations:**

| Operation Type | Auth Required? | Examples |
|---------------|----------------|----------|
| **Public** | ❌ No | Ask questions (`/api/ask`) |
| **Admin** | ✅ Yes | Training, inspection, stats |

### Step 1: Set Up Your Admin Credentials

#### First Time Setup

1. **Navigate to your project:**
   ```bash
   cd /home/steve/repos/portfolio/cloudvelous-chatbot
   ```

2. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Generate secure secrets:**
   ```bash
   # Generate JWT secret (32+ characters)
   openssl rand -hex 32
   # Output: 8f3d7c2e1a9b5f4d8c3e7a2f1b9d5e8c4f7a2b5d8e1c4f7a2b5d8e1c4f7a2b5d

   # Generate API key (16+ characters)
   openssl rand -hex 16
   # Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

4. **Edit `.env` file:**
   ```bash
   nano .env
   ```

5. **Update these critical values:**
   ```bash
   # Admin Authentication
   ADMIN_JWT_SECRET=8f3d7c2e1a9b5f4d8c3e7a2f1b9d5e8c4f7a2b5d8e1c4f7a2b5d8e1c4f7a2b5d
   ADMIN_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

   # Database
   POSTGRES_PASSWORD=your_secure_db_password

   # LLM API Keys (at least one required)
   OPENAI_API_KEY=sk-your-openai-key-here
   # OR
   GEMINI_API_KEY=your-gemini-key-here
   ```

6. **Restart services to apply changes:**
   ```bash
   docker compose down
   docker compose up -d
   ```

### Step 2: Choose Your Authentication Method

You have **two options** for admin authentication:

#### Option A: API Key (Simplest - Recommended)

**Use for:** Scripts, automation, daily use

**Header format:**
```
X-API-Key: your-api-key-from-env
```

**Example:**
```bash
export API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "X-API-Key: $API_KEY"
```

✅ **Pros:** Simple, never expires, easy to use
❌ **Cons:** Less secure than JWT, same key for everyone

---

#### Option B: JWT Token (More Secure)

**Use for:** Production, multiple admins, web dashboards

**How it works:**
1. Generate a JWT token (expires after 24 hours)
2. Use token in Authorization header
3. Token expires, generate new one

**Generate a token:**

```python
# generate_token.py
from datetime import timedelta
from jose import jwt
from datetime import datetime

# Your JWT secret from .env
JWT_SECRET = "8f3d7c2e1a9b5f4d8c3e7a2f1b9d5e8c4f7a2b5d8e1c4f7a2b5d8e1c4f7a2b5d"
JWT_ALGORITHM = "HS256"

# Create token
data = {
    "sub": "admin",
    "role": "admin",
    "exp": datetime.utcnow() + timedelta(hours=24)
}

token = jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(f"Your JWT Token:\n{token}")
print(f"\nExpires in: 24 hours")
print(f"\nUse in header: Authorization: Bearer {token}")
```

**Run it:**
```bash
# Install jose if needed
pip install python-jose

# Generate token
python generate_token.py
```

**Use the token:**
```bash
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

✅ **Pros:** More secure, expiration, can include user info
❌ **Cons:** Need to regenerate when expired, more complex

---

### Step 3: Test Your Authentication

#### Test with Swagger UI (Visual):

1. **Open Swagger UI:**
   ```
   http://localhost:8000/docs
   ```

2. **Click the "Authorize" button** (top right, looks like a lock 🔒)

3. **You'll see two authentication options:**
   ```
   HTTPBearer (http, Bearer)
   ├─ For JWT tokens
   └─ Enter: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   ApiKeyHeader (apiKey, Header)
   ├─ For API keys
   └─ Enter: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

4. **Enter your API key** in `ApiKeyHeader`:
   - Value: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`
   - Click "Authorize"
   - Click "Close"

5. **Test it works:**
   - Scroll to `GET /api/admin/stats`
   - Click "Try it out"
   - Click "Execute"
   - Should see statistics (not 401 error)

#### Test with cURL:

```bash
# Set your API key from .env
export API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Test authentication
curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "X-API-Key: $API_KEY"

# Expected: JSON with statistics
# Error: {"detail": "Authentication required"} means auth failed
```

#### Test with Python:

```python
import requests

API_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
headers = {"X-API-Key": API_KEY}

response = requests.get(
    "http://localhost:8000/api/admin/stats",
    headers=headers
)

if response.status_code == 200:
    print("✅ Authentication successful!")
    print(response.json())
elif response.status_code == 401:
    print("❌ Authentication failed - check your API key")
else:
    print(f"⚠️  Unexpected status: {response.status_code}")
```

---

### Authentication Quick Reference

**Which endpoints need auth?**

| Endpoint | Auth Required | Method |
|----------|---------------|--------|
| `GET /` | ❌ No | - |
| `GET /health` | ❌ No | - |
| `POST /api/ask` | ❌ No | - |
| `GET /api/session/{id}` | ❌ No | - |
| `POST /api/train` | ✅ Yes | API Key or JWT |
| `GET /api/embedding-inspector/{id}` | ✅ Yes | API Key or JWT |
| `POST /api/admin/sessions` | ✅ Yes | JWT only |
| `POST /api/admin/bulk-feedback` | ✅ Yes | JWT only |
| `POST /api/admin/chunk-edit` | ✅ Yes | JWT only |
| `GET /api/admin/stats` | ✅ Yes | API Key or JWT |
| `POST /api/workflows/search` | ✅ Yes | API Key or JWT |

**Common auth errors:**

```bash
# 401 Unauthorized
{"detail": "Authentication required"}
# Fix: Add authentication header

# 401 Unauthorized
{"detail": "Invalid API key"}
# Fix: Check your API key matches .env

# 401 Unauthorized
{"detail": "Could not validate credentials"}
# Fix: JWT token expired or invalid
```

---

## Basic Workflow

### The Complete Cycle

```
┌─────────────────────────────────────────────────────────┐
│                    USER WORKFLOW                        │
└─────────────────────────────────────────────────────────┘

1. ASK A QUESTION (Anyone can do this)
   └─> POST /api/ask
   └─> Returns: Answer + Session ID

2. REVIEW THE ANSWER (Admin only)
   └─> GET /api/embedding-inspector/{session_id}
   └─> See: What chunks were used, how relevant they were

3. PROVIDE FEEDBACK (Admin only)
   └─> POST /api/train
   └─> Mark: Correct/Incorrect, Which chunks were useful

4. SYSTEM LEARNS
   └─> Adjusts chunk weights
   └─> Creates workflow memory
   └─> Future similar questions get better answers
```

---

## Step-by-Step Guide

### Step 1: Ask a Question

**Anyone can ask questions - no authentication needed.**

#### Using Swagger UI:

1. Go to http://localhost:8000/docs
2. Find `POST /api/ask`
3. Click "Try it out"
4. Enter your question:
   ```json
   {
     "question": "How do I configure Docker in this project?",
     "include_trace": false
   }
   ```
5. Click "Execute"

#### Using cURL:

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I configure Docker in this project?",
    "include_trace": false
  }'
```

#### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/ask",
    json={
        "question": "How do I configure Docker in this project?",
        "include_trace": False
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Session ID: {data['session_id']}")
print(f"Sources: {', '.join(data['sources'])}")
```

#### What You Get Back:

```json
{
  "answer": "Docker can be configured in this project by...",
  "session_id": 42,
  "sources": [
    "infrastructure/docs/docker.md",
    "infrastructure/README.md"
  ],
  "reasoning_chain": null
}
```

**Important:** Save the `session_id` (42 in this example) - you'll need it for training!

---

### Step 2: Review the Answer

**Admin authentication required.**

Now you need to review whether the answer was good. Let's inspect what happened behind the scenes.

#### Using Swagger UI:

1. Click "Authorize" button at top
2. Enter your API key in `ApiKeyHeader`
3. Find `GET /api/embedding-inspector/{session_id}`
4. Click "Try it out"
5. Enter session_id: `42`
6. Click "Execute"

#### Using cURL:

```bash
export API_KEY="your-api-key-from-env"

curl -X GET "http://localhost:8000/api/embedding-inspector/42" \
  -H "X-API-Key: $API_KEY"
```

#### Using Python:

```python
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

response = requests.get(
    f"http://localhost:8000/api/embedding-inspector/42",
    headers=headers
)

inspection = response.json()

print(f"Query: {inspection['query']}")
print(f"Answer was: {inspection['response'][:200]}...")
print(f"\nChunks retrieved: {len(inspection['retrieved_chunks'])}")

for i, chunk in enumerate(inspection['retrieved_chunks'], 1):
    print(f"\n{i}. {chunk['repo_name']}/{chunk['file_path']}")
    print(f"   Similarity: {chunk['similarity_score']:.3f}")
    print(f"   Rank: {chunk['rank_position']}")
    print(f"   Weight: {chunk['accuracy_weight']}")
    print(f"   Preview: {chunk['content_preview'][:100]}...")
```

#### What You See:

```json
{
  "session_id": 42,
  "query": "How do I configure Docker in this project?",
  "response": "Docker can be configured in this project by...",

  "retrieved_chunks": [
    {
      "chunk_id": 123,
      "repo_name": "infrastructure",
      "file_path": "docs/docker.md",
      "section_title": "Configuration",
      "content_preview": "Docker configuration steps: 1. Create docker-compose.yml...",
      "similarity_score": 0.8765,
      "rank_position": 1,
      "was_useful": null,
      "accuracy_weight": 1.0
    },
    {
      "chunk_id": 124,
      "repo_name": "infrastructure",
      "file_path": "README.md",
      "section_title": "Setup",
      "content_preview": "To set up Docker, run docker compose up...",
      "similarity_score": 0.8234,
      "rank_position": 2,
      "was_useful": null,
      "accuracy_weight": 1.0
    }
  ],

  "retrieval_statistics": {
    "total_chunks_retrieved": 5,
    "avg_similarity_score": 0.7892,
    "min_similarity_score": 0.7123,
    "max_similarity_score": 0.8765
  }
}
```

#### What to Look For:

✅ **Good Answer Indicators:**
- High similarity scores (> 0.75)
- Relevant chunks from the right files
- Answer actually uses the retrieved content

❌ **Poor Answer Indicators:**
- Low similarity scores (< 0.6)
- Irrelevant chunks retrieved
- Answer doesn't match the documentation

---

### Step 3: Provide Feedback (Training)

**Admin authentication required.**

Now tell the system if the answer was good or bad, and which chunks were helpful.

#### Scenario A: Answer Was Correct

```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 42,
    "is_correct": true,
    "feedback_type": "correct",
    "chunk_feedback": [
      {"chunk_id": 123, "was_useful": true},
      {"chunk_id": 124, "was_useful": true},
      {"chunk_id": 125, "was_useful": false}
    ],
    "notes": "Perfect answer, very helpful!"
  }'
```

**What happens:**
- ✅ Chunks 123 and 124 get **weight increased** (1.0 → 1.1)
- ❌ Chunk 125 gets **weight decreased** (1.0 → 0.9)
- 💾 System creates a **workflow memory** of this successful pattern
- 🚀 Next time someone asks a similar question, chunks 123 & 124 will be **boosted**

#### Scenario B: Answer Was Wrong

```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 42,
    "is_correct": false,
    "feedback_type": "incorrect",
    "chunk_feedback": [
      {"chunk_id": 123, "was_useful": false},
      {"chunk_id": 124, "was_useful": false}
    ],
    "user_correction": "The answer should mention the environment variables in .env.example",
    "notes": "Missing important setup steps"
  }'
```

**What happens:**
- ❌ All marked chunks get **weight decreased**
- 📝 System stores the correction for analysis
- 🚫 No workflow memory created (only for correct answers)
- 📉 These chunks will be **less likely** to be retrieved for similar questions

#### Using Python:

```python
def provide_feedback(session_id, is_correct, chunk_feedback, notes=None):
    """Submit training feedback."""
    API_KEY = "your-api-key"
    headers = {"X-API-Key": API_KEY}

    payload = {
        "session_id": session_id,
        "is_correct": is_correct,
        "feedback_type": "correct" if is_correct else "incorrect",
        "chunk_feedback": chunk_feedback,
        "notes": notes
    }

    response = requests.post(
        "http://localhost:8000/api/train",
        json=payload,
        headers=headers
    )

    return response.json()

# Example: Mark answer as correct
result = provide_feedback(
    session_id=42,
    is_correct=True,
    chunk_feedback=[
        {"chunk_id": 123, "was_useful": True},
        {"chunk_id": 124, "was_useful": True},
        {"chunk_id": 125, "was_useful": False}
    ],
    notes="Great answer!"
)

print(f"Success: {result['success']}")
print(f"Chunks updated: {result['chunks_updated']}")
print(f"Workflow created: {result['workflow_embedding_created']}")
```

---

### Step 4: See the Impact

Watch how the system improves!

#### Check Statistics:

```bash
curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "X-API-Key: $API_KEY"
```

**You'll see:**

```json
{
  "accuracy_stats": {
    "total_sessions": 100,
    "sessions_with_feedback": 75,
    "correct_sessions": 65,
    "incorrect_sessions": 10,
    "pending_feedback": 25,
    "accuracy_rate": 86.67
  },

  "top_performing_chunks": [
    {
      "chunk_id": 123,
      "repo_name": "infrastructure",
      "file_path": "docs/docker.md",
      "accuracy_weight": 1.5,
      "times_retrieved": 45,
      "times_useful": 42,
      "usefulness_rate": 93.33
    }
  ]
}
```

**What this means:**
- Your accuracy is **86.67%** (65 correct out of 75 reviewed)
- Chunk 123 has been **boosted** to weight 1.5 (from 1.0)
- It was useful **93.33%** of the time (42 out of 45 times)
- It will now be **prioritized** in future searches

---

## Advanced Features

### Bulk Training (Train Multiple Sessions at Once)

If you have many sessions to review:

```python
import requests

API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

# Review multiple sessions efficiently
bulk_feedback = {
    "feedback_items": [
        {
            "session_id": 42,
            "is_correct": True,
            "feedback_type": "correct",
            "chunk_feedback": [
                {"chunk_id": 123, "was_useful": True}
            ]
        },
        {
            "session_id": 43,
            "is_correct": True,
            "feedback_type": "correct",
            "chunk_feedback": [
                {"chunk_id": 124, "was_useful": True}
            ]
        },
        {
            "session_id": 44,
            "is_correct": False,
            "feedback_type": "incorrect",
            "user_correction": "Should mention X instead of Y"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/admin/bulk-feedback",
    json=bulk_feedback,
    headers=headers
)

result = response.json()
print(f"Processed: {result['total_processed']}")
print(f"Successful: {result['successful']}")
print(f"Failed: {result['failed']}")
```

### Find Sessions Needing Review

List all sessions that haven't been reviewed yet:

```python
response = requests.post(
    "http://localhost:8000/api/admin/sessions",
    json={
        "page": 1,
        "page_size": 20,
        "sort_by": "created_at",
        "sort_order": "desc",
        "filters": {
            "has_feedback": False  # Only unreviewed sessions
        }
    },
    headers=headers
)

sessions = response.json()
print(f"Sessions needing review: {sessions['total_count']}")

for session in sessions['sessions']:
    print(f"\nSession {session['session_id']}:")
    print(f"  Query: {session['query']}")
    print(f"  Preview: {session['response_preview']}")
    print(f"  Chunks: {session['chunks_retrieved']}")
```

### Search for Similar Patterns

Find past answers to similar questions:

```python
response = requests.post(
    "http://localhost:8000/api/workflows/search",
    json={
        "query_text": "Docker configuration",
        "successful_only": True,  # Only successful answers
        "min_similarity": 0.75,
        "top_k": 5
    },
    headers=headers
)

results = response.json()
print(f"Found {results['total_found']} similar workflows")

for workflow in results['results']:
    print(f"\nSimilarity: {workflow['similarity_score']:.2f}")
    print(f"Query: {workflow['query']}")
    print(f"Successful: {workflow['is_successful']}")
    print(f"Chunks used: {workflow['chunks_used']}")
```

### Manual Chunk Weight Adjustment

If you know a chunk should be prioritized (or deprioritized):

```python
response = requests.post(
    "http://localhost:8000/api/admin/chunk-edit",
    json={
        "chunk_id": 123,
        "new_weight": 1.8,
        "reason": "This chunk consistently provides excellent Docker setup context"
    },
    headers=headers
)

result = response.json()
print(f"Adjusted chunk {result['chunk_id']}")
print(f"Old weight: {result['old_weight']}")
print(f"New weight: {result['new_weight']}")
```

**Weight guide:**
- `0.5`: Minimum weight (will rarely be retrieved)
- `1.0`: Default weight (neutral)
- `1.5`: Good chunk (1.5x more likely to be retrieved)
- `2.0`: Maximum weight (2x more likely to be retrieved)

---

## Complete Workflow Example

### Python Script: Review and Train Loop

```python
#!/usr/bin/env python3
"""
Complete training workflow script.
Run this daily to review and train on new sessions.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-from-env"
headers = {"X-API-Key": API_KEY}

def get_pending_sessions():
    """Get all sessions needing feedback."""
    response = requests.post(
        f"{BASE_URL}/api/admin/sessions",
        json={
            "page": 1,
            "page_size": 100,
            "filters": {"has_feedback": False}
        },
        headers=headers
    )
    return response.json()['sessions']

def inspect_session(session_id):
    """Get detailed session inspection."""
    response = requests.get(
        f"{BASE_URL}/api/embedding-inspector/{session_id}",
        headers=headers
    )
    return response.json()

def submit_feedback(session_id, is_correct, chunk_feedback, notes=None):
    """Submit training feedback."""
    payload = {
        "session_id": session_id,
        "is_correct": is_correct,
        "feedback_type": "correct" if is_correct else "incorrect",
        "chunk_feedback": chunk_feedback,
        "notes": notes
    }

    response = requests.post(
        f"{BASE_URL}/api/train",
        json=payload,
        headers=headers
    )
    return response.json()

def main():
    print("🔍 Cloudvelous Training Session")
    print("=" * 60)

    # Get sessions needing review
    pending = get_pending_sessions()
    print(f"\n📋 Found {len(pending)} sessions needing review\n")

    if not pending:
        print("✅ All sessions have been reviewed!")
        return

    # Review each session
    for i, session in enumerate(pending[:10], 1):  # Review up to 10
        print(f"\n[{i}/{min(10, len(pending))}] Session {session['session_id']}")
        print("-" * 60)

        # Get detailed inspection
        inspection = inspect_session(session['session_id'])

        print(f"❓ Query: {inspection['query']}")
        print(f"\n💬 Answer: {inspection['response'][:200]}...")
        print(f"\n📊 Retrieved {len(inspection['retrieved_chunks'])} chunks:")

        for j, chunk in enumerate(inspection['retrieved_chunks'][:3], 1):
            print(f"\n  {j}. {chunk['repo_name']}/{chunk['file_path']}")
            print(f"     Score: {chunk['similarity_score']:.3f} | Weight: {chunk['accuracy_weight']}")
            print(f"     {chunk['content_preview'][:80]}...")

        # Interactive review
        print("\n" + "=" * 60)
        correct = input("Was this answer correct? (y/n): ").lower().strip() == 'y'

        if correct:
            # Ask about each chunk
            chunk_feedback = []
            for chunk in inspection['retrieved_chunks']:
                useful = input(f"  Was chunk {chunk['chunk_id']} useful? (y/n/skip): ").lower().strip()
                if useful == 'y':
                    chunk_feedback.append({"chunk_id": chunk['chunk_id'], "was_useful": True})
                elif useful == 'n':
                    chunk_feedback.append({"chunk_id": chunk['chunk_id'], "was_useful": False})

            notes = input("Any notes? (optional): ").strip() or None

            # Submit feedback
            result = submit_feedback(
                session['session_id'],
                is_correct=True,
                chunk_feedback=chunk_feedback,
                notes=notes
            )

            print(f"\n✅ Feedback submitted!")
            print(f"   Chunks updated: {result['chunks_updated']}")
            print(f"   Workflow created: {result['workflow_embedding_created']}")
        else:
            correction = input("What should the answer have mentioned? ").strip()

            result = submit_feedback(
                session['session_id'],
                is_correct=False,
                chunk_feedback=[],
                notes=correction
            )

            print(f"\n❌ Marked as incorrect with correction")

        # Continue?
        if i < len(pending):
            continue_review = input("\nContinue to next session? (y/n): ").lower().strip() == 'y'
            if not continue_review:
                break

    # Show final stats
    print("\n" + "=" * 60)
    stats_response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    stats = stats_response.json()

    print(f"\n📈 Updated Statistics:")
    print(f"   Accuracy: {stats['accuracy_stats']['accuracy_rate']:.1f}%")
    print(f"   Total sessions: {stats['accuracy_stats']['total_sessions']}")
    print(f"   Pending review: {stats['accuracy_stats']['pending_feedback']}")
    print(f"\n✨ Training session complete!")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python train.py
```

---

## Troubleshooting

### "401 Unauthorized"

**Problem:** Authentication failed

**Solutions:**
1. Check your API key in `.env` file
2. Make sure you're using the header: `X-API-Key: your-key`
3. For Swagger UI: Click "Authorize" and enter key in `ApiKeyHeader`

### "404 Session Not Found"

**Problem:** Session ID doesn't exist

**Solutions:**
1. Double-check the session_id from the `/api/ask` response
2. List all sessions: `POST /api/admin/sessions`
3. Verify database has data

### Answer Quality Is Poor

**Problem:** AI gives irrelevant answers

**Solutions:**
1. **Add more documentation:** System needs content to search
2. **Provide more feedback:** Train on correct/incorrect answers
3. **Check chunk weights:** Use `/api/admin/stats` to see performance
4. **Manual boost:** Use `/api/admin/chunk-edit` for important chunks

### No Sessions to Review

**Problem:** `/api/admin/sessions` returns empty

**Solutions:**
1. Ask some questions first via `/api/ask`
2. Check if database is properly initialized
3. Verify Docker containers are running: `docker compose ps`

---

## Best Practices

### 1. Regular Training Schedule

**Recommendation:** Review sessions daily or weekly

```python
# Daily cron job
0 9 * * * cd /path/to/project && python train.py
```

### 2. Prioritize Recent Sessions

Always review newest sessions first - they're most relevant:

```python
{
    "sort_by": "created_at",
    "sort_order": "desc"  # Newest first
}
```

### 3. Be Consistent with Feedback

- ✅ **Mark useful chunks** even in correct answers
- ❌ **Mark not useful** when chunks were retrieved but not relevant
- 📝 **Add notes** to explain your reasoning
- 🎯 **Focus on borderline cases** - obvious ones matter less

### 4. Monitor Statistics

Check weekly:
```bash
curl -X GET "http://localhost:8000/api/admin/stats" -H "X-API-Key: $API_KEY"
```

Watch for:
- **Accuracy trend:** Should increase over time
- **Pending feedback:** Keep this number low
- **Top chunks:** Verify they're actually good content

### 5. Use Bulk Operations

If you have >10 sessions to review, use bulk feedback:
- Faster processing
- Single transaction
- Better performance

### 6. Leverage Workflow Search

Before answering repeated questions, search for past successful patterns:

```python
# Find similar questions before answering
results = requests.post(
    f"{BASE_URL}/api/workflows/search",
    json={
        "query_text": "new question here",
        "successful_only": True
    },
    headers=headers
)
```

---

## Understanding the Learning System

### How Weights Work

```
Initial State: All chunks start at weight 1.0

After positive feedback:
  Useful chunk in correct answer: 1.0 → 1.1 (+0.1)
  Do this 5 times: 1.0 → 1.5 (50% boost!)
  Maximum weight: 2.0 (2x more likely)

After negative feedback:
  Not useful chunk: 1.0 → 0.9 (-0.1)
  Do this 5 times: 1.0 → 0.5 (50% penalty)
  Minimum weight: 0.5 (half as likely)
```

### How Workflow Memory Works

```
When you mark an answer as CORRECT:
  1. System summarizes the reasoning:
     "For query about Docker config, retrieved chunks from
      infrastructure/docker.md and infrastructure/README.md,
      used chunks 123, 124, generated good answer"

  2. Converts summary to embedding (384-dim vector)

  3. Stores in database

  4. Next time someone asks similar question:
     - System finds this workflow memory
     - Boosts chunks 123, 124 by 1.2x
     - More likely to retrieve same good chunks
     - More likely to generate good answer
```

### Seeing It Work

```python
# Ask the same question twice, train after first time

# First time (before training)
response1 = requests.post(f"{BASE_URL}/api/ask",
    json={"question": "Docker setup?"})
# Might get OK answer

# Train it as correct
requests.post(f"{BASE_URL}/api/train",
    json={"session_id": response1.json()['session_id'], "is_correct": True},
    headers=headers)

# Second time (after training)
response2 = requests.post(f"{BASE_URL}/api/ask",
    json={"question": "How to setup Docker?"})
# Should get BETTER answer!
# - Same good chunks boosted
# - Workflow memory helps
```

---

## Quick Reference

### Essential Commands

```bash
# 1. Ask a question (public)
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "your question"}'

# 2. Inspect session (admin)
curl -X GET http://localhost:8000/api/embedding-inspector/{session_id} \
  -H "X-API-Key: $API_KEY"

# 3. Train (admin)
curl -X POST http://localhost:8000/api/train \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1, "is_correct": true}'

# 4. Get stats (admin)
curl -X GET http://localhost:8000/api/admin/stats \
  -H "X-API-Key: $API_KEY"
```

### Workflow Checklist

- [ ] Ask question → Get session_id
- [ ] Inspect session → Review chunks and answer
- [ ] Decide: Correct or incorrect?
- [ ] Mark chunks: Useful or not useful?
- [ ] Submit feedback
- [ ] Check stats to see improvement

---

## Next Steps

1. **Start using it:** Ask real questions about your repositories
2. **Review daily:** Set aside 10 minutes to review sessions
3. **Monitor accuracy:** Watch it improve over time
4. **Add content:** More documentation = better answers
5. **Phase 4+:** Enhanced retrieval and automation coming soon!

---

## Getting Help

- **API Docs:** http://localhost:8000/docs
- **Phase 3 API Guide:** See `PHASE3_API_GUIDE.md`
- **Technical Docs:** See `.cursor/phases/PHASE3_COMPLETE.md`

---

**Happy Training!** 🚀

The more feedback you provide, the smarter your chatbot becomes!
