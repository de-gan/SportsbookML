import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import SportsbookHome from './pages/MLB.tsx'
import HomeLanding from './pages/LandingPage.tsx'
import Methodology from './pages/Methodology.tsx'
import About from './pages/About.tsx'
import Login from './pages/Login.tsx'
import Signup from './pages/Register.tsx'
import { AuthProvider } from './lib/auth'

const storedTheme = localStorage.getItem('theme')

if (storedTheme === 'dark' || (!storedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
}

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<HomeLanding />} />
      <Route path="/mlb" element={<SportsbookHome />} />
      <Route path="/methodology" element={<Methodology />} />
      <Route path="/about" element={<About />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
    </Routes>
  </BrowserRouter>
);

export default App;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
