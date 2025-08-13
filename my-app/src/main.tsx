import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SportsbookHome from './Homepage.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SportsbookHome />
  </StrictMode>,
)
