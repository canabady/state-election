import Papa from 'papaparse'

export type ElectorCsvRow = {
  district_no: string
  district_name: string
  ac_no: string
  ac_name: string
  male: string
  female: string
  third_gender: string
  total: string
}

export function toInt(value: string): number {
  const normalized = (value ?? '').replace(/[,\s]/g, '')
  const n = Number.parseInt(normalized, 10)
  return Number.isNaN(n) ? 0 : n
}

export async function fetchElectorCsvRows(
  csvPath: string = '/data/tn_ac_wise_electors.csv',
): Promise<ElectorCsvRow[]> {
  const response = await fetch(csvPath)
  if (!response.ok) {
    throw new Error(`Failed to load electors CSV (${response.status})`)
  }

  const csvText = await response.text()
  const parsed = Papa.parse<ElectorCsvRow>(csvText, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: false,
  })

  if (parsed.errors.length > 0) {
    throw new Error(parsed.errors[0].message)
  }

  return parsed.data
}
