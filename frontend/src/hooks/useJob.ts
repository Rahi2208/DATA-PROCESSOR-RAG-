// useJob.ts: kirim job + pantau statusnya sampai selesai
import { useMutation, useQuery } from '@tanstack/react-query'
import { createJob, getJobStatus } from '@/api/client'

const POLL_MS = 1500 // cek status tiap 1,5 detik

export function useJob() {
  // useMutation = buat aksi yang "ngubah sesuatu" (upload file)
  const upload = useMutation({ mutationFn: createJob })
  const eventId = upload.data?.event_id

  // useQuery = buat "ngambil data"; refetchInterval bikin dia nanya ulang terus
  const status = useQuery({
    queryKey: ['job', eventId],
    queryFn: () => getJobStatus(eventId!),
    enabled: Boolean(eventId), // baru jalan setelah upload sukses
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'completed' || s === 'failed' ? false : POLL_MS // berhenti kalau udah selesai
    },
  })

  const isRunning =
    upload.isPending || (Boolean(eventId) && (!status.data || status.data.status === 'running'))

  return {
    start: upload.mutate,
    reset: upload.reset,
    eventId,
    isRunning,
    uploadError: upload.error,
    job: status.data,
    pollError: status.error,
  }
}
