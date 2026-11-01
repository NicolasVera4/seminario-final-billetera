import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { alVencerSesion } from './api/cliente'
import Layout from './componentes/Layout'
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
        <Route
          path="/"
          element={
            <Layout>
              <Dashboard />
            </Layout>
          }
        />
        <Route
          path="/chat"
          element={
            <Layout>
              <Chat />
            </Layout>
          }
        />
        <Route
          path="/historial"
          element={
            <Layout>
              <Historial />
            </Layout>
          }
        />
        <Route
          path="/resumen"
          element={
            <Layout>
              <RevisionResumen />
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
