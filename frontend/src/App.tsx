import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { alVencerSesion } from './api/cliente'
import Login from './paginas/Login'
import Registro from './paginas/Registro'

function ManejadorSesion() {
  const navegar = useNavigate()

  useEffect(() => {
    alVencerSesion(() => navegar('/login'))
  }, [navegar])

  return null
}

function App() {
  return (
    <BrowserRouter>
      <ManejadorSesion />
      <Routes>
        <Route path="/registro" element={<Registro />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<h1>Qash</h1>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
