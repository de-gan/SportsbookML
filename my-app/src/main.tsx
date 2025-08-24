import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SportsbookHome from './pages/MLB.tsx'
import HomeLanding from './pages/LandingPage.tsx'
import Methodology from './pages/Methodology.tsx'
import About from './pages/About.tsx'

if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

const App = () => {
  switch (window.location.pathname) {
    case '/mlb':
      return <SportsbookHome />;
    case '/methodology':
      return <Methodology />;
    case '/about':
      return <About />
    default:
      return <HomeLanding />;
  }
};

export default App;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
