import axios, { AxiosError } from 'axios'
import { useNotifyStore } from '../stores/notify'

// Create a singleton axios instance
// Let Vite proxy /api to backend; baseURL left empty so relative URLs work
// Default to a generous timeout (e.g., 5 minutes) so large DB queries aren't cut off locally.
// Override via VITE_HTTP_TIMEOUT (ms). Use 0 to disable.
const parsed = Number((import.meta as any).env?.VITE_HTTP_TIMEOUT)
const timeout = Number.isFinite(parsed) ? parsed : 300_000
export const http = axios.create({ timeout })

// Helper to safely access store outside of setup by importing on demand
function notifyError(message: string) {
  try {
    const store = useNotifyStore()
    store.error(message)
  } catch {
    // Pinia not ready yet; fall back
    // eslint-disable-next-line no-alert
    if (typeof window !== 'undefined') window.alert(message)
    // else ignore
  }
}

http.interceptors.response.use(
  (res) => res,
  (err: AxiosError<any>) => {
    // Prefer FastAPI-style detail if provided
    const status = err.response?.status
    const detail = (err.response?.data as any)?.detail
    const message = detail
      || (err.message || 'Network error')
    const prefix = status ? `[${status}] ` : ''
    notifyError(prefix + String(message))
    return Promise.reject(err)
  }
)

export default http
