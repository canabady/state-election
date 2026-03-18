import { Link, createFileRoute } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { fetchElectorCsvRows, toInt } from '../../services/electors'

type DistrictAcRow = {
  district: string
  districtNo: number
  acNo: number
  acName: string
  male: number
  female: number
  thirdGender: number
  totalVoters: number
}

type SortColumn = 'acNo' | 'acName' | 'male' | 'female' | 'thirdGender' | 'totalVoters'
type SortDirection = 'asc' | 'desc'

export const Route = createFileRoute('/data/$district')({
  loader: async ({ params }) => {
    const parsed = await fetchElectorCsvRows()

    const districtParam = decodeURIComponent(params.district).trim().toLowerCase()
    const rows: DistrictAcRow[] = parsed
      .filter((row) => row.district_name?.trim().toLowerCase() === districtParam)
      .map((row) => ({
        district: row.district_name,
        districtNo: toInt(row.district_no),
        acNo: toInt(row.ac_no),
        acName: row.ac_name,
        male: toInt(row.male),
        female: toInt(row.female),
        thirdGender: toInt(row.third_gender),
        totalVoters: toInt(row.total),
      }))
      .sort((a, b) => a.acNo - b.acNo)

    if (rows.length === 0) {
      throw new Error(`No elector data found for district: ${params.district}`)
    }

    return rows
  },
  component: DistrictDetail,
})

function DistrictDetail() {
  const rows = Route.useLoaderData()
  const [sortColumn, setSortColumn] = useState<SortColumn>('acNo')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const district = rows[0].district
  const totalVoters = rows.reduce((sum, row) => sum + row.totalVoters, 0)
  const totalMale = rows.reduce((sum, row) => sum + row.male, 0)
  const totalFemale = rows.reduce((sum, row) => sum + row.female, 0)
  const totalThirdGender = rows.reduce((sum, row) => sum + row.thirdGender, 0)
  const sortedRows = useMemo(() => {
    const copy = [...rows]
    copy.sort((a, b) => {
      let result = 0
      if (sortColumn === 'acNo') result = a.acNo - b.acNo
      if (sortColumn === 'acName') result = a.acName.localeCompare(b.acName)
      if (sortColumn === 'male') result = a.male - b.male
      if (sortColumn === 'female') result = a.female - b.female
      if (sortColumn === 'thirdGender') result = a.thirdGender - b.thirdGender
      if (sortColumn === 'totalVoters') result = a.totalVoters - b.totalVoters
      return sortDirection === 'asc' ? result : -result
    })
    return copy
  }, [rows, sortColumn, sortDirection])

  const handleSort = (column: SortColumn) => {
    if (column === sortColumn) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortColumn(column)
    setSortDirection('asc')
  }

  return (
    <section className="space-y-6 select-none caret-transparent">
      <div className="flex items-start gap-3">
        <Link
          to="/data"
          className="mt-1 rounded-xl border border-slate-300 bg-white p-2.5 text-slate-600 transition-all hover:bg-slate-50 hover:text-slate-900"
        >
          <ArrowLeft size={20} />
        </Link>
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-slate-900">{district}</h2>
          <p className="text-sm text-slate-600">Assembly constituency-wise information in {district} district</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="No. of AC" value={rows.length.toLocaleString('en-IN')} />
        <StatCard label="Male" value={totalMale.toLocaleString('en-IN')} />
        <StatCard label="Female" value={totalFemale.toLocaleString('en-IN')} />
        <StatCard label="Third Gender" value={totalThirdGender.toLocaleString('en-IN')} />
        <StatCard label="Total Voters" value={totalVoters.toLocaleString('en-IN')} />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-slate-700">
              <tr>
                <SortableHeader
                  label="AC No."
                  align="left"
                  active={sortColumn === 'acNo'}
                  direction={sortDirection}
                  onClick={() => handleSort('acNo')}
                />
                <SortableHeader
                  label="Assembly Constituency"
                  align="left"
                  active={sortColumn === 'acName'}
                  direction={sortDirection}
                  onClick={() => handleSort('acName')}
                />
                <SortableHeader
                  label="Male"
                  align="right"
                  active={sortColumn === 'male'}
                  direction={sortDirection}
                  onClick={() => handleSort('male')}
                />
                <SortableHeader
                  label="Female"
                  align="right"
                  active={sortColumn === 'female'}
                  direction={sortDirection}
                  onClick={() => handleSort('female')}
                />
                <SortableHeader
                  label="Third Gender"
                  align="right"
                  active={sortColumn === 'thirdGender'}
                  direction={sortDirection}
                  onClick={() => handleSort('thirdGender')}
                />
                <SortableHeader
                  label="Total Voters"
                  align="right"
                  active={sortColumn === 'totalVoters'}
                  direction={sortDirection}
                  onClick={() => handleSort('totalVoters')}
                />
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr key={`${row.districtNo}-${row.acNo}`} className="border-t border-slate-100 hover:bg-slate-50/70">
                  <td className="px-4 py-3 text-slate-700">{row.acNo}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{row.acName}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{row.male.toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{row.female.toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{row.thirdGender.toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{row.totalVoters.toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  )
}

function SortableHeader({
  label,
  active,
  direction,
  align,
  onClick,
}: {
  label: string
  active: boolean
  direction: SortDirection
  align: 'left' | 'right'
  onClick: () => void
}) {
  const alignClass = align === 'right' ? 'text-right' : 'text-left'
  const buttonAlignClass = align === 'right' ? 'ml-auto justify-end' : ''
  const arrow = active ? (direction === 'asc' ? '↑' : '↓') : '↕'

  return (
    <th className={`px-4 py-3 ${alignClass} font-semibold`}>
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex w-full items-center gap-1 leading-none text-slate-700 hover:text-slate-900 select-none caret-transparent ${buttonAlignClass}`}
      >
        <span>{label}</span>
        <span className="text-xs leading-none">{arrow}</span>
      </button>
    </th>
  )
}
