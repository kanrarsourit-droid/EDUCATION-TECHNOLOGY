/**
 * Frontend API client for the Learning Debugger FastAPI backend.
 * Automatically injects the active Supabase JWT Bearer token into authenticated requests.
 */

import { supabase } from './supabase';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface StudentProfile {
  id: string;
  auth_user_id: string | null;
  email: string;
  full_name: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SubjectItem {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
}

export interface TopicItem {
  id: string;
  subject_id: string;
  name: string;
  description: string | null;
  order_index: number;
  created_at: string;
}

export interface ConceptItem {
  id: string;
  topic_id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface QuestionChoice {
  label?: string;
  text?: string;
}

export interface SafeQuestion {
  id: string;
  concept_id: string;
  title: string;
  prompt: string;
  question_type: 'multiple_choice' | 'open_response' | 'code';
  difficulty: string;
  rubric: {
    choices?: QuestionChoice[];
    options?: QuestionChoice[];
  } | null;
  created_at: string;
}

export interface AttemptSubmission {
  question_id: string;
  student_answer: string;
  student_reasoning?: string;
  confidence_score?: number;
  parent_attempt_id?: string;
}

export interface AttemptResult {
  id: string;
  question_id: string;
  attempt_number: number;
  parent_attempt_id: string | null;
  student_answer: string;
  student_reasoning: string | null;
  is_correct: boolean | null;
  confidence_score: number | null;
  detected_misconception_id: string | null;
  analysis_reasoning: string | null;
  created_at: string;
}

/**
 * Helper to retrieve the current Supabase session access token.
 */
async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token || null;
}

/**
 * General fetch wrapper that handles auth headers and JSON parsing.
 */
async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {},
  requireAuth = true
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (requireAuth) {
    const token = await getAccessToken();
    if (!token) {
      throw new Error('Not authenticated. Please log in.');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const errorDetail = data?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
    throw new Error(errorDetail);
  }

  return data as T;
}

// ============================================================================
// AUTH & PROFILE APIS
// ============================================================================

export async function getMe(): Promise<any> {
  return fetchWithAuth('/auth/me');
}

export async function getProfile(): Promise<StudentProfile> {
  return fetchWithAuth<StudentProfile>('/auth/profile');
}

export async function provisionProfile(fullName?: string): Promise<StudentProfile> {
  return fetchWithAuth<StudentProfile>('/auth/profile', {
    method: 'POST',
    body: JSON.stringify({ full_name: fullName || null }),
  });
}

// ============================================================================
// KNOWLEDGE DOMAIN APIS (PUBLIC)
// ============================================================================

export async function getSubjects(): Promise<SubjectItem[]> {
  return fetchWithAuth<SubjectItem[]>('/subjects', {}, false);
}

export async function getTopicsBySubject(subjectId: string): Promise<TopicItem[]> {
  return fetchWithAuth<TopicItem[]>(`/subjects/${subjectId}/topics`, {}, false);
}

export async function getConceptsByTopic(topicId: string): Promise<ConceptItem[]> {
  return fetchWithAuth<ConceptItem[]>(`/topics/${topicId}/concepts`, {}, false);
}

// ============================================================================
// LEARNING WORKFLOW APIS (AUTHENTICATED)
// ============================================================================

export async function getConceptQuestions(conceptId: string): Promise<SafeQuestion[]> {
  return fetchWithAuth<SafeQuestion[]>(`/learning/concepts/${conceptId}/questions`);
}

export async function submitAttempt(payload: AttemptSubmission): Promise<AttemptResult> {
  return fetchWithAuth<AttemptResult>('/learning/attempts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getStudentAttempts(params?: {
  question_id?: string;
  concept_id?: string;
  limit?: number;
}): Promise<AttemptResult[]> {
  const query = new URLSearchParams();
  if (params?.question_id) query.append('question_id', params.question_id);
  if (params?.concept_id) query.append('concept_id', params.concept_id);
  if (params?.limit) query.append('limit', String(params.limit));

  const qs = query.toString();
  return fetchWithAuth<AttemptResult[]>(`/learning/attempts${qs ? `?${qs}` : ''}`);
}

export interface MisconceptionItem {
  id: string;
  concept_id: string;
  name: string;
  description: string;
  canonical_example: string | null;
  severity: string;
  created_at: string;
}

export interface InterventionItem {
  id: string;
  misconception_id: string;
  title: string;
  intervention_type: string;
  content: string;
  created_at: string;
}

export async function getMisconceptionsByConcept(conceptId: string): Promise<MisconceptionItem[]> {
  return fetchWithAuth<MisconceptionItem[]>(`/concepts/${conceptId}/misconceptions`, {}, false);
}

export async function getInterventionsByMisconception(misconceptionId: string): Promise<InterventionItem[]> {
  return fetchWithAuth<InterventionItem[]>(`/misconceptions/${misconceptionId}/interventions`, {}, false);
}

export interface DiagnosticResult {
  attempt_id: string;
  is_correct: boolean | null;
  diagnostic_status: 'correct' | 'misconception_detected' | 'insufficient_evidence' | 'retry_required' | 'repaired';
  detected_misconception: boolean;
  misconception_id: string | null;
  misconception_name: string | null;
  misconception_description: string | null;
  severity: string | null;
  intervention: boolean;
  intervention_id: string | null;
  intervention_type: string | null;
  intervention_content: string | null;
  mastery_score: number;
  mastery_status: string;
  next_action: string;
}

export async function diagnoseAttempt(attemptId: string): Promise<DiagnosticResult> {
  return fetchWithAuth<DiagnosticResult>(`/learning/attempts/${attemptId}/diagnose`, {
    method: 'POST',
  });
}

