import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { alVencerSesion } from './api/cliente'
import AdminDocumentos from './paginas/AdminDocumentos'
import AdminUsuarios from './paginas/AdminUsuarios'
import Chat from './paginas/Chat'
import Dashboard from './paginas/Dashboard'
import Historial from './paginas/Historial'
import Login from './paginas/Login'
import Registro from './paginas/Registro'
import RevisionResumen from './paginas/RevisionResumen'

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
        <Route path="/" element={<Chat />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/historial" element={<Historial />} />
        <Route path="/resumen" element={<RevisionResumen />} />
        <Route path="/admin/documentos" element={<AdminDocumentos />} />
        <Route path="/admin/usuarios" element={<AdminUsuarios />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
