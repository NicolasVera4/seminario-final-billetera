import { Link } from 'react-router-dom'

export default function BarraLateral() {
  return (
    <nav>
      <Link to="/">Dashboard</Link>
      <Link to="/chat">Chat</Link>
      <Link to="/historial">Historial</Link>
    </nav>
  )
}
