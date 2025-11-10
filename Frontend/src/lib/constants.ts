export const APP_NAME = 'NLPForge';
export const APP_VERSION = '1.0.0';
export const API_VERSION = 'v1';

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  NEW_RUN: '/run/new',
  RUNS: '/runs',
  RUN_DETAIL: (id: string) => `/runs/${id}`,
  SEARCH: '/search',
  TEMPLATES: '/templates',
  TEMPLATE_DETAIL: (intent: string) => `/templates/${intent}`,
  DATASETS: '/dataset',
  SETTINGS: '/settings',
  HEALTH: '/health',
} as const;

export const INTENTS = [
  'login',
  'signup',
  'update',
  'delete',
  'get_user',
  'list_users',
  'create_post',
  'update_post',
  'delete_post',
] as const;

export const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] as const;

export const DATASET_LIMITS = {
  MIN_EXAMPLES: 10,
  MAX_EXAMPLES: 200,
  DEFAULT_EXAMPLES: 50,
} as const;

export const SEARCH_LIMITS = {
  MIN_TOP_K: 1,
  MAX_TOP_K: 20,
  DEFAULT_TOP_K: 5,
} as const;

export const DEBOUNCE_DELAYS = {
  SEARCH: 300,
  INPUT: 500,
  RESIZE: 150,
} as const;

export const ANIMATION_DURATIONS = {
  FAST: 160,
  NORMAL: 200,
  SLOW: 260,
  STAGGER: 60,
} as const;

export const STATUS_COLORS = {
  pass: 'success',
  fail: 'danger',
  skip: 'warning',
  pending: 'muted',
  running: 'primary',
} as const;

export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.9,
  MEDIUM: 0.7,
  LOW: 0.5,
} as const;

export const SIMILARITY_THRESHOLDS = {
  HIGH: 0.85,
  MEDIUM: 0.65,
  LOW: 0.45,
} as const;
