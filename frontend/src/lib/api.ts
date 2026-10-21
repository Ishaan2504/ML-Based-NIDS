export type ApiHealth = {
  status: 'online' | 'degraded'
  model_loaded: boolean
  mode: string
  version: string
  message: string | null
}

export type ModelInfo = {
  status: string
  model_name: string | null
  model_id: string | null
  threshold: number | null
  score_type: string | null
  feature_count: number | null
  selected_feature_count: number | null
  class_count: number | null
  test_accuracy: number | null
  test_accuracy_scope: string | null
  test_rows: number | null
  full_test_accuracy: number | null
  full_test_rows: number | null
  supported_families: string[]
  feature_names: string[]
  message?: string | null
}

export type CsvAnalysis = {
  source_file: string
  total_flows: number
  malicious_count: number
  benign_count: number
  model_id: string
  feature_count: number
  prediction_breakdown?: Array<{
    prediction: string
    category: string
    count: number
  }>
  preview: Array<{
    row_index: number
    score: number
    is_malicious_prediction: boolean
    attack_family: string
    predicted_label: string
    severity: string | null
  }>
}

const apiUrl = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error(`API returned HTTP ${response.status}`)
  return response.json() as Promise<T>
}

export async function getApiHealth(): Promise<ApiHealth> {
  return getJson<ApiHealth>('/health')
}

export async function getModelInfo(): Promise<ModelInfo> {
  return getJson<ModelInfo>('/model/info')
}

export async function analyzeCsv(file: File): Promise<CsvAnalysis> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`${apiUrl}/analyze/csv`, { method: 'POST', body: form })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.error?.message || `Analysis failed (HTTP ${response.status})`)
  }
  return payload as CsvAnalysis
}
