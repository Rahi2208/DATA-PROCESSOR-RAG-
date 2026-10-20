// files.ts: tebak jenis file dari ekstensinya (sama kayak classify() di backend)
export type FileKind = 'guide' | 'data'

const GUIDE_EXT = ['.pdf', '.png', '.jpg', '.jpeg', '.webp']
const DATA_EXT = ['.xlsx', '.csv']

export function fileKind(name: string): FileKind | null {
  const ext = name.slice(name.lastIndexOf('.')).toLowerCase()
  if (GUIDE_EXT.includes(ext)) return 'guide'
  if (DATA_EXT.includes(ext)) return 'data'
  return null
}

// balikin pesan kalau kombinasi file belum lengkap, null kalau udah oke
export function validateFiles(files: File[]): string | null {
  const guides = files.filter((f) => fileKind(f.name) === 'guide').length
  const datas = files.filter((f) => fileKind(f.name) === 'data').length
  if (guides === 0) return 'Tambahin minimal 1 file guide (PDF/gambar)'
  if (datas !== 1) return 'Butuh tepat 1 file data (.xlsx/.csv)'
  return null
}
