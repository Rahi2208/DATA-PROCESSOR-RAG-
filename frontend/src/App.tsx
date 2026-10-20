// App.tsx: halaman utama: upload -> Enter -> tunggu -> tabel hasil
import { useEffect, useState } from 'react'
import { Download, Loader2, RotateCcw } from 'lucide-react'
import { exportUrl } from '@/api/client'
import { validateFiles } from '@/api/files'
import { FileDropzone } from '@/components/FileDropzone'
import { ResultTable } from '@/components/ResultTable'
import { ReviewList } from '@/components/ReviewList'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useJob } from '@/hooks/useJob'

export default function App() {
  const [files, setFiles] = useState<File[]>([])
  const { start, reset, eventId, isRunning, uploadError, job, pollError } = useJob()

  const problem = validateFiles(files)
  const canSubmit = !problem && !isRunning
  const submit = () => canSubmit && start(files)

  // pencet Enter di mana aja = proses (kecuali lagi ngetik di input)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === 'Enter' && !typing) submit()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const startOver = () => {
    setFiles([])
    reset()
  }

  const error = uploadError?.message ?? pollError?.message ?? (job?.status === 'failed' ? job.error : null)
  const result = job?.status === 'completed' ? job.result : null

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-2xl font-bold">Data Process Agent</h1>
        <p className="text-muted-foreground">
          Masukin guide + data mentah, pencet <kbd className="rounded border px-1 text-xs">Enter</kbd>,
          dapat tabel sesuai format guide.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>1 · File</CardTitle>
          <CardDescription>{problem ?? 'Siap diproses'}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileDropzone files={files} onChange={setFiles} disabled={isRunning} />
          <div className="flex gap-2">
            <Button onClick={submit} disabled={!canSubmit}>
              {isRunning && <Loader2 className="animate-spin" />}
              {isRunning ? 'Memproses…' : 'Proses (Enter)'}
            </Button>
            {(eventId || files.length > 0) && !isRunning && (
              <Button variant="outline" onClick={startOver}>
                <RotateCcw /> Mulai ulang
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Gagal</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && eventId && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">2 · Hasil ({result.tables.length} tabel)</h2>
            <Button variant="outline" asChild>
              <a href={exportUrl(eventId)}>
                <Download /> Download Excel
              </a>
            </Button>
          </div>
          {result.tables.map((t) => (
            <ResultTable key={t.id} table={t} />
          ))}
          <ReviewList items={result.review.items} />
        </section>
      )}
    </main>
  )
}
