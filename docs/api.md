# API Documentation

## Authentication

APFA uses JWT (JSON Web Tokens) for authentication. All protected endpoints require a valid Bearer token.

### Obtaining a Token

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### GET /health

**Purpose:** Health check endpoint for monitoring service availability.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
- 200: Service is healthy
- 503: Service unavailable

### GET /metrics

**Purpose:** Exposes Prometheus metrics for monitoring.

**Authentication:** None required (should be restricted in production)

**Response:** Prometheus-formatted metrics text

### POST /generate-advice

**Purpose:** Generate personalized loan advice using AI agents.

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "query": "What loan options are available for a $200,000 home purchase?"
}
```

**Validation Rules:**
- Query length: 5-500 characters
- Must contain financial keywords (loan, credit, finance, etc.)
- No profanity (detected automatically)
- No HTML/script content
- Reasonable financial amounts and rates
- No excessive repetition

**Response:**
```json
{
  "advice": "Based on current market conditions...",
  "user": "admin"
}
```

**Error Responses:**
```json
{
  "detail": "Invalid API key"
}
```
```json
{
  "detail": "Query contains inappropriate content"
}
```
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**Status Codes:**
- 200: Success
- 401: Authentication failed
- 422: Validation error
- 429: Rate limit exceeded
- 500: Internal server error
- 502: External service error
- 503: Service unavailable

## Rate Limiting

- **Global:** 10 requests per minute per IP address
- **Authentication:** 10 login attempts per minute per IP
- **Advice Generation:** 10 requests per minute per authenticated user

## Input Validation

The system performs comprehensive input validation:

- **Content Filtering:** Profanity detection using ML models
- **Financial Validation:** Ensures queries are finance-related
- **Amount Validation:** Validates monetary amounts ($0-10M range)
- **Rate Validation:** Validates interest rates (0-50% range)
- **Sanitization:** Removes HTML, scripts, and malicious content
- **Length Checks:** Prevents extremely short/long queries
- **Repetition Detection:** Flags queries with excessive word repetition

## Error Handling

The API provides detailed error messages and appropriate HTTP status codes:

- **400-499:** Client errors (authentication, validation)
- **500-599:** Server errors (service failures, external API issues)

All errors are logged with appropriate severity levels for monitoring.