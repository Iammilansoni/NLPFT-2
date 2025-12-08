import { DictionaryFunction, HealthStatus, ConvertResponse } from './types';

// Mock data for development and testing
export const mockFunctions: DictionaryFunction[] = [
  {
    _id: '1',
    function_name: 'click_element',
    description: 'Click on a web element by selector',
    templates: [
      'click {selector}',
      'click on {selector}',
      'press {selector}',
      'tap {selector}'
    ],
    examples: [
      'click #submit-button',
      'click on the login button',
      'press .nav-item'
    ],
    args: {
      selector: {
        type: 'string',
        required: true,
        description: 'CSS selector for the element to click'
      }
    },
    tags: ['ui', 'interaction', 'click'],
    category: 'user_interface',
    confidence_threshold: 0.85,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-20T14:45:00Z'
  },
  {
    _id: '2',
    function_name: 'fill_input',
    description: 'Fill an input field with text',
    templates: [
      'fill {selector} with {text}',
      'enter {text} in {selector}',
      'type {text} into {selector}',
      'input {text} in {selector}'
    ],
    examples: [
      'fill #username with admin',
      'enter password in #password-field',
      'type hello world into .search-box'
    ],
    args: {
      selector: {
        type: 'string',
        required: true,
        description: 'CSS selector for the input field'
      },
      text: {
        type: 'string',
        required: true,
        description: 'Text to enter in the field'
      }
    },
    tags: ['ui', 'input', 'form'],
    category: 'user_interface',
    confidence_threshold: 0.90,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-18T09:15:00Z'
  },
  {
    _id: '3',
    function_name: 'wait_for_element',
    description: 'Wait for an element to appear or become visible',
    templates: [
      'wait for {selector}',
      'wait until {selector} appears',
      'wait for {selector} to be visible',
      'expect {selector} to appear'
    ],
    examples: [
      'wait for .loading-spinner',
      'wait until #modal appears',
      'wait for .success-message to be visible'
    ],
    args: {
      selector: {
        type: 'string',
        required: true,
        description: 'CSS selector for the element to wait for'
      },
      timeout: {
        type: 'number',
        required: false,
        description: 'Maximum time to wait in milliseconds',
        default: 5000
      }
    },
    tags: ['ui', 'wait', 'synchronization'],
    category: 'synchronization',
    confidence_threshold: 0.80,
    created_at: '2024-01-16T11:00:00Z',
    updated_at: '2024-01-16T11:00:00Z'
  },
  {
    _id: '4',
    function_name: 'assert_text',
    description: 'Assert that text is present on the page',
    templates: [
      'assert text {text}',
      'verify text {text}',
      'check that {text} is present',
      'expect to see {text}'
    ],
    examples: [
      'assert text "Welcome back"',
      'verify text Login successful',
      'check that Order confirmed is present'
    ],
    args: {
      text: {
        type: 'string',
        required: true,
        description: 'Text to look for on the page'
      },
      selector: {
        type: 'string',
        required: false,
        description: 'Optional CSS selector to search within'
      }
    },
    tags: ['assertion', 'verification', 'text'],
    category: 'verification',
    confidence_threshold: 0.75,
    created_at: '2024-01-17T13:20:00Z',
    updated_at: '2024-01-19T16:30:00Z'
  },
  {
    _id: '5',
    function_name: 'navigate_to',
    description: 'Navigate to a specific URL',
    templates: [
      'go to {url}',
      'navigate to {url}',
      'visit {url}',
      'open {url}'
    ],
    examples: [
      'go to https://example.com',
      'navigate to /login',
      'visit the homepage'
    ],
    args: {
      url: {
        type: 'string',
        required: true,
        description: 'URL to navigate to'
      }
    },
    tags: ['navigation', 'url'],
    category: 'navigation',
    confidence_threshold: 0.95,
    created_at: '2024-01-14T08:45:00Z',
    updated_at: '2024-01-14T08:45:00Z'
  }
];

export const mockHealthStatus: HealthStatus = {
  status: 'healthy',
  version: '1.0.0',
  timestamp: new Date().toISOString(),
  checks: {
    status: 'healthy',
    database: {
      status: 'healthy',
      response_time_ms: 12.5,
      connection_pool: 'active'
    },
    rule_engine: {
      status: 'healthy',
      response_time_ms: 8.3,
      active_patterns: 156,
      total_parses: 1247,
      successful_parses: 1094,
      failed_parses: 153,
      test_parse_successful: true
    },
    system: {
      status: 'healthy',
      memory: {
        status: 'healthy',
        usage_percent: 45.6,
        available_mb: 2048,
        total_mb: 4096
      },
      cpu: {
        status: 'healthy',
        usage_percent: 23.1
      },
      process_id: 12345
    },
    application: {
      status: 'healthy',
      version: '1.0.0',
      uptime_seconds: 86400,
      uptime_formatted: '1d 0h 0m 0s'
    },
    health_check: {
      duration_ms: 25.7,
      timestamp: new Date().toISOString()
    }
  }
};

export const mockConvertResponse: ConvertResponse = {
  steps: [
    {
      function: 'navigate_to',
      args: { url: 'https://example.com' },
      confidence: 0.95,
      provenance: 'template_match',
      template: 'go to {url}',
      matched_text: 'go to https://example.com',
      order: 1
    },
    {
      function: 'fill_input',
      args: { selector: '#username', text: 'admin' },
      confidence: 0.88,
      provenance: 'template_match',
      template: 'fill {selector} with {text}',
      matched_text: 'fill username field with admin',
      order: 2
    },
    {
      function: 'click_element',
      args: { selector: '#login-button' },
      confidence: 0.92,
      provenance: 'template_match',
      template: 'click {selector}',
      matched_text: 'click login button',
      order: 3
    }
  ],
  overall_confidence: 0.916,
  unresolved_tokens: [],
  processing_time_ms: 45.2,
  status: 'success'
};