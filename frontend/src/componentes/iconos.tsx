interface IconoProps {
  className?: string
}

function Base({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <svg className={className ?? 'icono'} viewBox="0 0 24 24" aria-hidden="true">
      {children}
    </svg>
  )
}

export function IconoLogo(props: IconoProps) {
  return (
    <Base {...props}>
      <rect x="2.5" y="5" width="19" height="14" rx="2.5" />
      <path d="M2.5 10h19M6.5 15h4" />
    </Base>
  )
}

export function IconoDashboard(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M4 20V11M10 20V4M16 20v-6M22 20H2" />
    </Base>
  )
}

export function IconoChat(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M20 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z" />
    </Base>
  )
}

export function IconoHistorial(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" />
    </Base>
  )
}

export function IconoSalir(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
    </Base>
  )
}

export function IconoCheck(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M20 6 9 17l-5-5" />
    </Base>
  )
}

export function IconoAlerta(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01" />
    </Base>
  )
}

export function IconoEditar(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
    </Base>
  )
}

export function IconoDescartar(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M18 6 6 18M6 6l12 12" />
    </Base>
  )
}

export function IconoChevronAbajo(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="m6 9 6 6 6-6" />
    </Base>
  )
}

export function IconoCalendario(props: IconoProps) {
  return (
    <Base {...props}>
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </Base>
  )
}

export function IconoBuscar(props: IconoProps) {
  return (
    <Base {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </Base>
  )
}

export function IconoMas(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M12 5v14M5 12h14" />
    </Base>
  )
}

export function IconoMicrofono(props: IconoProps) {
  return (
    <Base {...props}>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </Base>
  )
}

export function IconoEnviar(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4z" />
    </Base>
  )
}

export function IconoAdjuntar(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M21 11.5 12.5 20a5 5 0 0 1-7-7L14 4.5a3.3 3.3 0 0 1 4.7 4.7l-8.5 8.5a1.7 1.7 0 0 1-2.4-2.4L15.5 7.6" />
    </Base>
  )
}

export function IconoFlechaAtras(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="m15 18-6-6 6-6" />
    </Base>
  )
}

export function IconoFlechaAdelante(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="m9 18 6-6-6-6" />
    </Base>
  )
}

export function IconoDocumento(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5z" />
      <path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" />
    </Base>
  )
}

export function IconoArchivo(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M8 13h8M8 17h5" />
    </Base>
  )
}

export function IconoUsuarios(props: IconoProps) {
  return (
    <Base {...props}>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </Base>
  )
}

export function IconoDesbloquear(props: IconoProps) {
  return (
    <Base {...props}>
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 9.9-1" />
    </Base>
  )
}
