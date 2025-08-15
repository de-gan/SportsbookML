import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SportsbookHome from './pages/Sportsbook.tsx'
import HomeLanding from './pages/LandingPage.tsx'

if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

const App = () => {
  return window.location.pathname === '/mlb'
    ? <SportsbookHome />
    : <HomeLanding />;
};

export default App;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
