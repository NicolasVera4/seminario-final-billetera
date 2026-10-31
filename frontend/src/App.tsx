import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { alVencerSesion } from './api/cliente'
import RutaProtegida from './componentes/RutaProtegida'
import Chat from './paginas/Chat'
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
        <Route
          path="/"
          element={
            <RutaProtegida>
              <Chat />
            </RutaProtegida>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
