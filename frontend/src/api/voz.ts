import { solicitar } from './cliente'

export interface TranscripcionRespuesta {
  texto: string
}

export function transcribirAudio(audio: Blob): Promise<TranscripcionRespuesta> {
  const formData = new FormData()
  formData.append('archivo', audio, 'audio.webm')
  return solicitar<TranscripcionRespuesta>('/voz/transcribir', {
    method: 'POST',
    body: formData,
  })
}
