# Backend Integration Guide for Frontend

Complete reference for integrating NLPForge Frontend with Backend API.

## API Base Configuration

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

## Core API Endpoints

### 1. Query Processing

#### POST `/api/v1/query`
Process natural language queries and generate test cases.

**Request**:
```typescript
interface QueryRequest {
  query: string;
  generate_dataset?: boolean;
  num_examples?: number;
  top_k?: number;
}
```

**Example**:
```typescript
import { apiClient } from '@/lib/api';

const response = await apiClient.post('/api/v1/query', {
  query: "Login with username admin and password test123",
  generate_dataset: true,
  num_examples: 50,
  top_k: 5
});
```

**Response**:
```typescript
interface QueryResponse {
  query: string;
  intent: string;
  slots: Record<string, any>;
  confidence: number;
  best_matches: Array<{
    api: string;
    score: number;
    confidence: number;
  }>;
  dataset_generated: boolean;
  dataset_info?: {
    intent: string;
    num_variations: number;
    total_examples: number;
    paths: {
      csv: string;
      json: string;
    };
    redis_keys: number;
  };
  search_results: SearchResultItem[];
}
```

### 2. Statistics

#### GET `/api/v1/stats`
Get platform statistics.

**Response**:
```typescript
interface StatsResponse {
  total_vectors: number;
  intents: Record<string, number>;
  datasets_count: number;
  query_logs_count: number;
  templates_count: number;
}
```

### 3. Semantic Search

#### GET `/api/v1/search/search?query={query}&top_k={k}`
Search embeddings by semantic similarity.

**Parameters**:
- `query`: Search string
- `top_k`: Number of results (default: 5, max: 20)

**Response**:
```typescript
interface SearchResponse {
  input_query: string;
  top_k: number;
  results: Array<{
    query: string;
    api: string;
    endpoint: string;
    request: Record<string, any>;
    response: Record<string, any>;
    cosine_distance: number;
    cosine_similarity: number;
  }>;
}
```

### 4. Template Management

#### GET `/api/v1/templates/`
List all templates.

**Response**: `Template[]`

#### GET `/api/v1/templates/{intent}`
Get specific template.

#### POST `/api/v1/templates/`
Create new template.

**Request**:
```typescript
interface Template {
  intent: string;
  api_name: string;
  description: string;
  endpoint: string;
  method: string;
  intent_keywords: string[];
  parameters: TemplateParameter[];
  example_queries: string[];
  response_format?: Record<string, string>;
}
```

#### PUT `/api/v1/templates/{intent}`
Update template.

#### DELETE `/api/v1/templates/{intent}`
Delete template.

#### POST `/api/v1/templates/sync`
Sync templates from JSON file.

#### POST `/api/v1/templates/reload`
Hot reload templates without server restart.

#### GET `/api/v1/templates/stats`
Get template statistics.

### 5. Dataset Management

#### GET `/api/v1/dataset/list`
List all datasets.

**Response**:
```typescript
interface DatasetListResponse {
  datasets: string[];
}
```

#### POST `/api/v1/dataset/generate`
Generate dataset with AI.

**Request**:
```typescript
interface DatasetGenerateRequest {
  seed_prompt: string;
  examples: number;
  api_name: string;
  endpoint: string;
}
```

**Response**:
```typescript
interface DatasetGenerateResponse {
  message: string;
  csv_path: string;
  ingestion: {
    success: boolean;
    count: number;
  };
}
```

#### POST `/api/v1/dataset/upload`
Upload CSV dataset.

**Request**: `multipart/form-data` with file

**Response**:
```typescript
interface DatasetUploadResponse {
  message: string;
  file: string;
  rows: number;
  embedded: boolean;
}
```

#### GET `/api/v1/dataset/download?filename={name}`
Download dataset file.

**Response**: File blob (CSV)

## React Query Hooks

### Example: Fetch Statistics

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

function DashboardStats() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/stats');
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading stats</div>;

  return (
    <div>
      <p>Total Vectors: {data.total_vectors}</p>
      <p>Templates: {data.templates_count}</p>
    </div>
  );
}
```

### Example: Process Query (Mutation)

```typescript
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

function QueryForm() {
  const mutation = useMutation({
    mutationFn: async (data: QueryRequest) => {
      const response = await apiClient.post('/api/v1/query', data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Query processed:', data);
    },
  });

  const handleSubmit = (query: string) => {
    mutation.mutate({
      query,
      generate_dataset: true,
      num_examples: 50,
    });
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleSubmit(e.currentTarget.query.value);
    }}>
      <input name="query" />
      <button disabled={mutation.isPending}>
        {mutation.isPending ? 'Processing...' : 'Submit'}
      </button>
    </form>
  );
}
```

## Error Handling

The API client includes interceptors for error handling:

```typescript
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    if (error.response?.status === 500) {
      // Handle server error
    }
    return Promise.reject(error);
  }
);
```

## Type Safety

All API responses are typed. Import types from `@/lib/api-types`:

```typescript
import type {
  QueryRequest,
  QueryResponse,
  Template,
  SearchResultItem,
  StatsResponse,
} from '@/lib/api-types';
```

## CORS Configuration

Backend should allow requests from frontend origin:

```python
# Backend: app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variables

Frontend `.env`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Backend `.env`:
```env
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
```

## Request/Response Flow

1. **User Input** → Frontend component
2. **React Query** → Trigger mutation/query
3. **API Client** → Format request with axios
4. **Backend API** → Process request
5. **Response** → Type-checked and cached
6. **UI Update** → Render with optimistic updates

## WebSocket/SSE (Future Enhancement)

For real-time updates during long-running operations:

```typescript
const eventSource = new EventSource(
  `${API_BASE_URL}/api/v1/query/stream?query=${encodeURIComponent(query)}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateProgress(data);
};
```

## Best Practices

1. **Always use TypeScript types** for requests/responses
2. **Handle loading states** with `isLoading`, `isPending`
3. **Handle errors gracefully** with error boundaries
4. **Cache strategically** with React Query `staleTime`
5. **Optimistic updates** for better UX
6. **Debounce search** inputs (300-500ms)
7. **Virtualize large lists** with TanStack Virtual
8. **Lazy load heavy components** (charts, viewers)

## Testing API Integration

```typescript
// __tests__/api.test.ts
import { apiClient } from '@/lib/api';

jest.mock('@/lib/api-client');

describe('Query API', () => {
  it('should process query successfully', async () => {
    const mockResponse = {
      intent: 'login',
      confidence: 0.95,
      // ...
    };
    
    (apiClient.post as jest.Mock).mockResolvedValue({
      data: mockResponse,
    });

    const result = await apiClient.post('/api/v1/query', {
      query: 'Test query',
    });

    expect(result.data.intent).toBe('login');
  });
});
```

## Troubleshooting

### Issue: CORS errors
**Solution**: Check backend CORS configuration includes frontend URL

### Issue: 404 on API calls
**Solution**: Verify `NEXT_PUBLIC_API_URL` in `.env` and backend is running

### Issue: Type errors
**Solution**: Ensure `api-types.ts` matches backend response structure

### Issue: Stale data
**Solution**: Adjust React Query `staleTime` or invalidate queries manually

---

**Last Updated**: 2025-01-09
**Backend Version**: 1.0.0
**Frontend Version**: 1.0.0
