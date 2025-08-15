import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SportsbookHome from './pages/Sportsbook.tsx'

if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SportsbookHome />
  </StrictMode>,
)
