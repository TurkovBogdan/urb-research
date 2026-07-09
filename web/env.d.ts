/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Optional dev override: hit a backend on another origin directly (no Vite proxy).
  // Empty/undefined (default, and always in prod) → relative same-origin requests.
  readonly VITE_API_BASE?: string
}
