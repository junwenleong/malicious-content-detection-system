export type PredictionResult = {
  text: string
  label: string
  probability_malicious: number
  threshold: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  recommended_action: 'ALLOW' | 'REVIEW' | 'BLOCK'
  latency_ms?: number
}

export type PredictResponse = {
  predictions: PredictionResult[]
  metadata: {
    total_items: number
    malicious_count: number
    benign_count: number
    total_latency_ms: number
    model_version?: string
  }
}
