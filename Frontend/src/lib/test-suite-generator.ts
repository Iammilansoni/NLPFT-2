/**
 * Generate a test suite from query results
 */
export function generateTestSuiteFromQuery(queryResult: any) {
  if (!queryResult) {
    return null
  }

  // Extract information from query result
  const intent = queryResult.intent || 'unknown'
  const entities = queryResult.entities || []
  const confidence = queryResult.confidence || 0

  // Generate test cases based on intent
  const tests = []

  // Basic test case
  tests.push({
    id: '1',
    method: 'POST',
    endpoint: `/api/${intent.toLowerCase()}`,
    description: `Test ${intent} functionality`,
    body: entities.reduce((acc: any, entity: any) => {
      acc[entity.type] = entity.value
      return acc
    }, {}),
    expectedStatus: 200,
  })

  // Edge case: empty input
  tests.push({
    id: '2',
    method: 'POST',
    endpoint: `/api/${intent.toLowerCase()}`,
    description: `Test ${intent} with empty input`,
    body: {},
    expectedStatus: 400,
  })

  // Edge case: invalid input
  tests.push({
    id: '3',
    method: 'POST',
    endpoint: `/api/${intent.toLowerCase()}`,
    description: `Test ${intent} with invalid input`,
    body: { invalid: 'data' },
    expectedStatus: 400,
  })

  return {
    name: `${intent} Test Suite`,
    description: `Auto-generated test suite for ${intent}`,
    confidence,
    tests,
    metadata: {
      generatedAt: new Date().toISOString(),
      queryResult,
    },
  }
}
