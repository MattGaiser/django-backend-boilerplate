# API Endpoints Documentation

This document inventories all API endpoints that the frontend currently relies on via Supabase. This serves as a reference for rebuilding these endpoints in Django REST Framework.

## Base Configuration

**Supabase URL:** `https://dlpcnhzzxexpaaiajvdw.supabase.co`
**API Base:** `https://dlpcnhzzxexpaaiajvdw.supabase.co/rest/v1/`
**Auth Base:** `https://dlpcnhzzxexpaaiajvdw.supabase.co/auth/v1/`
**Storage Base:** `https://dlpcnhzzxexpaaiajvdw.supabase.co/storage/v1/`
**Functions Base:** `https://dlpcnhzzxexpaaiajvdw.supabase.co/functions/v1/`

## Authentication Endpoints

### 1. Sign Up
- **Method:** POST
- **URL:** `/auth/v1/signup`
- **Authentication:** Public (API key only)
- **Request Headers:**
  ```
  Content-Type: application/json
  apikey: {supabase_anon_key}
  ```
- **Request Body:**
  ```json
  {
    "email": "string",
    "password": "string",
    "options": {
      "emailRedirectTo": "string",
      "data": {
        "full_name": "string"
      }
    }
  }
  ```
- **Response:** 
  ```json
  {
    "user": {
      "id": "uuid",
      "email": "string",
      "user_metadata": {
        "full_name": "string"
      }
    },
    "session": {
      "access_token": "string",
      "refresh_token": "string",
      "expires_in": number,
      "token_type": "bearer"
    }
  }
  ```
- **Status Codes:** 200 (success), 400 (validation error), 422 (email already exists)

### 2. Sign In
- **Method:** POST
- **URL:** `/auth/v1/token?grant_type=password`
- **Authentication:** Public (API key only)
- **Request Headers:**
  ```
  Content-Type: application/json
  apikey: {supabase_anon_key}
  ```
- **Request Body:**
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response:** Same as Sign Up
- **Status Codes:** 200 (success), 400 (invalid credentials)

### 3. Sign Out
- **Method:** POST
- **URL:** `/auth/v1/logout`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  apikey: {supabase_anon_key}
  ```
- **Response:** Empty
- **Status Codes:** 204 (success)

### 4. Get Session
- **Method:** GET
- **URL:** `/auth/v1/user`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  apikey: {supabase_anon_key}
  ```
- **Response:**
  ```json
  {
    "id": "uuid",
    "email": "string",
    "user_metadata": {
      "full_name": "string"
    }
  }
  ```
- **Status Codes:** 200 (success), 401 (unauthorized)

## Database Table Endpoints

### Organizations

#### 1. List Organizations (via memberships)
- **Method:** GET
- **URL:** `/rest/v1/organization_memberships?select=organization:organizations(*)&user_id=eq.{user_id}`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  apikey: {supabase_anon_key}
  ```
- **Response:**
  ```json
  [
    {
      "organization": {
        "id": "uuid",
        "name": "string",
        "description": "string",
        "created_at": "timestamp",
        "updated_at": "timestamp"
      }
    }
  ]
  ```

#### 2. Create Organization
- **Method:** POST
- **URL:** `/rest/v1/organizations`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  apikey: {supabase_anon_key}
  Content-Type: application/json
  Prefer: return=representation
  ```
- **Request Body:**
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Response:**
  ```json
  {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
  ```

### Projects

#### 1. List Projects
- **Method:** GET
- **URL:** `/rest/v1/projects?organization_id=eq.{organization_id}`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "name": "string",
      "description": "string",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
  ```

#### 2. Create Project
- **Method:** POST
- **URL:** `/rest/v1/projects`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "organization_id": "uuid",
    "name": "string",
    "description": "string"
  }
  ```

### Evidence Sources

#### 1. List Evidence Sources
- **Method:** GET
- **URL:** `/rest/v1/evidence_sources?project_id=eq.{project_id}&order=created_at.desc`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "user_id": "uuid",
      "project_id": "uuid",
      "name": "string",
      "type": "document|video|audio|text|image",
      "file_path": "string",
      "content": "string",
      "file_size": number,
      "mime_type": "string",
      "processing_status": "pending|processing|completed|failed",
      "upload_date": "timestamp",
      "created_at": "timestamp",
      "updated_at": "timestamp",
      "metadata": {},
      "summary": "string",
      "notes": "string"
    }
  ]
  ```

#### 2. Create Evidence Source
- **Method:** POST
- **URL:** `/rest/v1/evidence_sources`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "user_id": "uuid",
    "project_id": "uuid", 
    "name": "string",
    "type": "document|video|audio|text|image",
    "file_path": "string",
    "content": "string",
    "file_size": number,
    "mime_type": "string",
    "processing_status": "pending",
    "metadata": {}
  }
  ```

#### 3. Update Evidence Source Status
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_sources?id=eq.{source_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "processing_status": "pending|processing|completed|failed"
  }
  ```

#### 4. Update Evidence Source Metadata (for tags)
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_sources?id=eq.{source_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "metadata": {
      "tags": ["string"]
    }
  }
  ```

### Evidence Facts

#### 1. List Evidence Facts
- **Method:** GET
- **URL:** `/rest/v1/evidence_facts?project_id=eq.{project_id}&order=extracted_at.desc`
- **Authentication:** Bearer token required
- **Query Parameters:**
  - `source_id=eq.{source_id}` (optional filter)
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "source_id": "uuid",
      "user_id": "uuid",
      "project_id": "uuid",
      "content": "string",
      "title": "string",
      "notes": "string",
      "confidence_score": number,
      "tags": ["string"],
      "participant": "string",
      "sentiment": "positive|neutral|negative",
      "extracted_at": "timestamp",
      "created_at": "timestamp",
      "embedding": "string"
    }
  ]
  ```

#### 2. Create Evidence Facts (Bulk)
- **Method:** POST
- **URL:** `/rest/v1/evidence_facts`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  [
    {
      "source_id": "uuid",
      "user_id": "uuid",
      "project_id": "uuid",
      "content": "string",
      "confidence_score": number,
      "tags": ["string"]
    }
  ]
  ```

#### 3. Update Evidence Fact Tags
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_facts?id=eq.{fact_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "tags": ["string"]
  }
  ```

#### 4. Update Evidence Fact (General)
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_facts?id=eq.{fact_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "title": "string",
    "content": "string", 
    "notes": "string",
    "participant": "string",
    "sentiment": "string"
  }
  ```

#### 5. Update Evidence Fact Embedding
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_facts?id=eq.{fact_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "embedding": "[0.1,0.2,0.3,...]"
  }
  ```

#### 6. Count Facts by Tags
- **Method:** GET
- **URL:** `/rest/v1/evidence_facts?project_id=eq.{project_id}&tags=cs.{["tag_name"]}&select=*`
- **Authentication:** Bearer token required
- **Headers:**
  ```
  Prefer: count=exact
  Range: 0-0
  ```

### Evidence Insights

#### 1. List Evidence Insights
- **Method:** GET
- **URL:** `/rest/v1/evidence_insights?project_id=eq.{project_id}&order=created_at.desc`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "project_id": "uuid",
      "user_id": "uuid",
      "title": "string",
      "description": "string",
      "priority": "low|medium|high",
      "tags": ["string"],
      "related_facts": ["uuid"],
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
  ```

#### 2. Update Evidence Insight Tags
- **Method:** PATCH
- **URL:** `/rest/v1/evidence_insights?id=eq.{insight_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "tags": ["string"]
  }
  ```

#### 3. Count Insights by Tags
- **Method:** GET
- **URL:** `/rest/v1/evidence_insights?project_id=eq.{project_id}&tags=cs.{["tag_name"]}&select=*`
- **Authentication:** Bearer token required
- **Headers:**
  ```
  Prefer: count=exact
  Range: 0-0
  ```

### Evidence Chunks

#### 1. Evidence chunks are created automatically by the system during document processing
- **URL Pattern:** `/rest/v1/evidence_chunks`
- **Authentication:** Bearer token required
- **Structure:**
  ```json
  {
    "id": "uuid",
    "source_id": "uuid",
    "user_id": "uuid",
    "project_id": "uuid",
    "chunk_index": number,
    "chunk_text": "string",
    "embedding": "string",
    "metadata": {},
    "created_at": "timestamp"
  }
  ```

### Recommendations

#### 1. List Recommendations
- **Method:** GET
- **URL:** `/rest/v1/recommendations?project_id=eq.{project_id}&order=created_at.desc`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "user_id": "uuid",
      "project_id": "uuid",
      "title": "string",
      "description": "string",
      "effort": "low|medium|high",
      "impact": "low|medium|high",
      "tags": ["string"],
      "related_insights": ["uuid"],
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
  ```

### Tags

#### 1. List Tags
- **Method:** GET
- **URL:** `/rest/v1/tags?project_id=eq.{project_id}&order=created_at.desc`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "user_id": "uuid",
      "project_id": "uuid",
      "name": "string",
      "category": "string",
      "description": "string",
      "color": "string",
      "status": "pending|approved|rejected",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
  ```

#### 2. Create Tag
- **Method:** POST
- **URL:** `/rest/v1/tags`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "name": "string",
    "category": "string",
    "description": "string",
    "color": "string",
    "project_id": "uuid",
    "user_id": "uuid",
    "status": "pending|approved"
  }
  ```

#### 3. Update Tag
- **Method:** PATCH
- **URL:** `/rest/v1/tags?id=eq.{tag_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "name": "string",
    "category": "string", 
    "description": "string",
    "color": "string",
    "status": "pending|approved|rejected"
  }
  ```

#### 4. Delete Tag
- **Method:** DELETE
- **URL:** `/rest/v1/tags?id=eq.{tag_id}&project_id=eq.{project_id}`
- **Authentication:** Bearer token required

### Organization Memberships

#### 1. Get User Role in Organization
- **Method:** GET
- **URL:** `/rest/v1/organization_memberships?organization_id=eq.{org_id}&user_id=eq.{user_id}&select=role`
- **Authentication:** Bearer token required
- **Response:**
  ```json
  {
    "role": "super_user|regular_user"
  }
  ```

## Storage Endpoints

### File Upload
- **Method:** POST
- **URL:** `/storage/v1/object/evidence-files/{user_id}/{timestamp}.{extension}`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  apikey: {supabase_anon_key}
  Content-Type: {file_mime_type}
  ```
- **Request Body:** File binary data
- **Response:**
  ```json
  {
    "Key": "string",
    "Id": "uuid"
  }
  ```

## RPC Functions (Stored Procedures)

### 1. Search Similar Facts
- **Method:** POST
- **URL:** `/rest/v1/rpc/search_similar_facts`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "query_embedding": "[0.1,0.2,0.3,...]",
    "project_id_param": "uuid",
    "similarity_threshold": 0.7,
    "match_count": 10
  }
  ```
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "content": "string",
      "confidence_score": number,
      "tags": ["string"],
      "similarity": number
    }
  ]
  ```

### 2. Debug Auth Context
- **Method:** POST
- **URL:** `/rest/v1/rpc/debug_auth_context`
- **Authentication:** Bearer token required
- **Request Body:** `{}`
- **Response:**
  ```json
  {
    "user_id": "uuid",
    "role": "string"
  }
  ```

## Edge Functions (Custom APIs)

### 1. Process Document
- **Method:** POST
- **URL:** `/functions/v1/process-document`
- **Authentication:** Bearer token required
- **Request Headers:**
  ```
  Authorization: Bearer {access_token}
  Content-Type: application/json
  ```
- **Request Body:**
  ```json
  {
    "sourceId": "uuid",
    "fileName": "string",
    "filePath": "string"
  }
  ```
- **Response:**
  ```json
  {
    "facts": [
      {
        "content": "string",
        "confidence_score": number,
        "tags": ["string"]
      }
    ]
  }
  ```

### 2. AI Conversation
- **Method:** POST
- **URL:** `/functions/v1/ai-conversation`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "message": "string",
    "context": "string",
    "project_id": "uuid"
  }
  ```
- **Response:**
  ```json
  {
    "response": "string",
    "suggestions": ["string"]
  }
  ```

### 3. Generate Recommendations
- **Method:** POST
- **URL:** `/functions/v1/generate-recommendations`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "insights": [
      {
        "id": "uuid",
        "title": "string",
        "description": "string",
        "tags": ["string"],
        "related_facts": ["uuid"]
      }
    ],
    "project_id": "uuid"
  }
  ```
- **Response:**
  ```json
  {
    "recommendations": [
      {
        "title": "string",
        "description": "string",
        "notes": "string",
        "related_insight_ids": ["uuid"],
        "tags": ["string"],
        "type": "opportunity|solution",
        "effort": "low|medium|high",
        "impact": "low|medium|high"
      }
    ]
  }
  ```

### 4. Generate Insights
- **Method:** POST
- **URL:** `/functions/v1/generate-insights`
- **Authentication:** Bearer token required
- **Request Body:**
  ```json
  {
    "facts": [
      {
        "id": "uuid",
        "content": "string",
        "tags": ["string"],
        "source_id": "uuid"
      }
    ],
    "project_id": "uuid"
  }
  ```
- **Response:**
  ```json
  {
    "insights": [
      {
        "title": "string",
        "description": "string",
        "priority": "low|medium|high",
        "tags": ["string"],
        "related_fact_ids": ["uuid"]
      }
    ]
  }
  ```

## Authentication Requirements Summary

### Public Endpoints (API key only)
- Sign Up
- Sign In

### Protected Endpoints (Bearer token required)
- All database operations
- All storage operations
- All Edge Functions
- All RPC functions
- Sign Out
- Get Session

## Known Frontend Workarounds and Edge Cases

### 1. Organization Auto-Selection
- Frontend automatically selects "testkjnknihhwerewerwrw" as default organization if it exists
- Falls back to first available organization
- Located in: `src/contexts/OrganizationContext.tsx`

### 2. Tag Usage Counting
- Tags usage count is calculated by querying multiple tables and summing results
- Includes evidence_facts, evidence_insights, evidence_sources (in metadata.tags)
- Performance consideration for large datasets

### 3. Evidence Source Metadata Tags
- Tags for evidence sources are stored in `metadata.tags` JSON field
- Requires special handling compared to other entities where tags are direct arrays

### 4. Error Handling for Organization Creation
- Frontend includes retry logic and delayed checking for organization creation
- Handles race conditions where organization exists despite initial error response

### 5. Embedding Storage Format
- Embeddings are stored as JSON string arrays: `"[0.1,0.2,0.3,...]"`
- Generated client-side with placeholder random values (needs real embedding service)

### 6. File Upload Flow
- Files uploaded to storage first, then evidence source record created with file path
- Processing status tracked through evidence source updates
- AI processing happens asynchronously via Edge Function

### 7. Tag Cascade Operations
- Tag deletion requires removing from all related entities across multiple tables
- Tag merging replaces tag names across all entities before deleting source tag
- No database-level cascade constraints

## Request Headers Standard

All authenticated requests require:
```
Authorization: Bearer {access_token}
apikey: {supabase_anon_key}
Content-Type: application/json (for JSON requests)
```

Response requests with data modification use:
```
Prefer: return=representation
```

Count-only requests use:
```
Prefer: count=exact
Range: 0-0
```