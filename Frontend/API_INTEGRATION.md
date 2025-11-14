# Frontend-Backend API Integration

Complete guide for connecting the NLPForge Frontend with the Backend API.

## 🔧 Setup

### 1. Environment Variables

Create a `.env.local` file in the Frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Start Backend Server

```bash
cd Backend
python -m app.main
```

The backend will run on `http://localhost:8000`

### 3. Start Frontend

```bash
cd Frontend
npm run dev
```

## 📚 API Client Library

The API client is organized into modular services:

### Directory Structure

```
Frontend/src/lib/api/
├── client.ts      # Base HTTP client with error handling
├── types.ts       # TypeScript types matching backend models
├── query.ts       # Query processing API
├── templates.ts   # Template management API
├── search.ts      # Semantic search API
└── index.ts       # Main export
```

## 🎯 Usage Examples

### 1. Process Natural Language Query

```typescript
import { useProcessQuery } from '@/hooks/useQuery'

function MyComponent() {
  const { mutate: processQuery, isPending, data } = useProcessQuery()

  const handleQuery = () => {
    processQuery({
      query: 'Test login with email: user@example.com and password: P@ssw0rd',
      generate_dataset: true,
      num_examples: 50,
      top_k: 5,
    })
  }

  return (
    <div>
      <button onClick={handleQuery} disabled={isPending}>
        {isPending ? 'Processing...' : 'Process Query'}
      </button>
      {data && (
        <div>
          <p>Intent: {data.intent}</p>
          <p>Confidence: {data.confidence * 100}%</p>
        </div>
      )}
    </div>
  )
}
```

### 2. List API Templates

```typescript
import { useTemplates } from '@/hooks/useTemplates'

function TemplateList() {
  const { data: templates, isLoading } = useTemplates()

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      {templates?.map((template) => (
        <div key={template.api_name}>
          <h3>{template.api_name}</h3>
          <p>{template.description}</p>
        </div>
      ))}
    </div>
  )
}
```

### 3. Semantic Search

```typescript
import { useSemanticSearch } from '@/hooks/useSearch'

function SearchComponent() {
  const { mutate: search, data } = useSemanticSearch()

  const handleSearch = (query: string) => {
    search({ query, top_k: 5 })
  }

  return (
    <div>
      <input onChange={(e) => handleSearch(e.target.value)} />
      {data?.results.map((result, i) => (
        <div key={i}>
          <p>{result.api}</p>
          <p>Similarity: {result.cosine_similarity}</p>
        </div>
      ))}
    </div>
  )
}
```

### 4. Create New Template

```typescript
import { useCreateTemplate } from '@/hooks/useTemplates'

function CreateTemplate() {
  const { mutate: createTemplate } = useCreateTemplate()

  const handleCreate = () => {
    createTemplate({
      api_name: 'user_registration',
      description: 'Register a new user account',
      endpoint: '/api/v1/users/register',
      method: 'POST',
      intent_keywords: ['register', 'signup', 'create account'],
      parameters: [
        {
          name: 'email',
          type: 'string',
          required: true,
          description: 'User email address',
        },
        {
          name: 'password',
          type: 'string',
          required: true,
          description: 'User password',
        },
      ],
      example_queries: [
        'Register new user with email john@example.com',
        'Create account for jane.doe@email.com',
      ],
    })
  }

  return <button onClick={handleCreate}>Create Template</button>
}
```

## 🔄 React Query Hooks

All API calls use React Query for caching, refetching, and state management:

### Query Hooks

- `useProcessQuery()` - Process natural language query
- `useQueryStats()` - Get vector database statistics
- `useTemplates()` - List all templates
- `useTemplate(intent)` - Get specific template
- `useTemplateStats()` - Get template statistics
- `useSemanticSearch()` - Perform semantic search

### Mutation Hooks

- `useCreateTemplate()` - Create new template
- `useUpdateTemplate()` - Update existing template
- `useDeleteTemplate()` - Delete template
- `useSyncTemplates()` - Sync templates from JSON
- `useReloadTemplates()` - Hot reload services
- `useReindexIntent()` - Reindex specific intent

## 📦 API Response Types

All API responses are fully typed. Import from `@/lib/api/types`:

```typescript
import type {
  QueryRequest,
  QueryResponse,
  Template,
  SemanticSearchResponse,
  // ... and more
} from '@/lib/api/types'
```

## 🛠️ Error Handling

The API client includes comprehensive error handling:

```typescript
const { mutate, isError, error } = useProcessQuery()

// error.message contains user-friendly message
// error.status contains HTTP status code
// error.data contains full error response
```

## 🎨 Complete Dashboard Example

See `Frontend/src/components/dashboard/QueryProcessor.tsx` for a complete,
production-ready implementation with:

- ✅ Real-time query processing
- ✅ Intent detection display
- ✅ Confidence scoring
- ✅ Best matches visualization
- ✅ Semantic search results
- ✅ Loading states
- ✅ Error handling
- ✅ Smooth animations

## 🔗 Available Endpoints

### Query API
- `POST /api/v1/query` - Process natural language query
- `GET /api/v1/stats` - Get database statistics
- `POST /api/v1/reindex/{intent}` - Reindex specific intent

### Template API
- `GET /api/v1/templates` - List all templates
- `GET /api/v1/templates/{intent}` - Get specific template
- `POST /api/v1/templates` - Create template
- `PUT /api/v1/templates/{intent}` - Update template
- `DELETE /api/v1/templates/{intent}` - Delete template
- `POST /api/v1/templates/sync` - Sync from JSON
- `POST /api/v1/templates/reload` - Hot reload
- `GET /api/v1/templates/stats` - Get statistics

### Search API
- `GET /api/v1/search` - Semantic search

## 🚀 Next Steps

1. **Update HeroDemo**: Replace mock data with `useProcessQuery()` hook
2. **Build Dashboard**: Use `QueryProcessor` component as starting point
3. **Template Management**: Create admin interface using template hooks
4. **Search Page**: Implement semantic search interface
5. **Stats Dashboard**: Display analytics using stats hooks

## 🔒 Production Considerations

1. **Environment Variables**: Use different URLs for dev/staging/production
2. **Error Boundaries**: Wrap API components in error boundaries
3. **Loading States**: Always handle loading and error states
4. **Retry Logic**: React Query handles retries automatically
5. **Caching**: Adjust `staleTime` based on data freshness needs
6. **Rate Limiting**: Implement debouncing for search inputs
7. **Authentication**: Add auth tokens to API client when needed

## 📝 Testing

```typescript
// Mock API responses in tests
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

// Wrap component in test
render(
  <QueryClientProvider client={queryClient}>
    <YourComponent />
  </QueryClientProvider>
)
```

## 🎯 Migration Checklist

- [ ] Set up `.env.local` with `NEXT_PUBLIC_API_URL`
- [ ] Replace mock data in components with API hooks
- [ ] Add loading and error states to all API calls
- [ ] Test with backend running locally
- [ ] Update error handling UI
- [ ] Add success toast notifications
- [ ] Implement optimistic updates where needed
- [ ] Add request debouncing for search
- [ ] Configure CORS on backend if needed
- [ ] Set up API monitoring and logging
