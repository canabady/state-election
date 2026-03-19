import { Link, createFileRoute, notFound } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { fetchStateConfig, stateExists, type AppConfig } from '../../../services/appConfig'
import { fetchElectorCsvRows, toInt, type ElectorCsvRow } from '../../../services/electors'

type DistrictSummary = {
  district: string
  acCount: number
  male: number
  female: number
  thirdGender: number
  totalVoters: number
}

type SortColumn = 'district' | 'acCount' | 'male' | 'female' | 'thirdGender' | 'totalVoters'
type SortDirection = 'asc' | 'desc'
type LoaderData = { config: AppConfig; districts: DistrictSummary[] }

function aggregateDistrictData(rows: ElectorCsvRow[]): DistrictSummary[] {
  const districtMap = new Map<
    string,
    { acNos: Set<string>; male: number; female: number; thirdGender: number; totalVoters: number }
  >()

  for (const row of rows) {
    const district = row.district_name?.trim()
    if (!district) continue

    const record = districtMap.get(district) ?? {
      acNos: new Set<string>(),
      male: 0,
      female: 0,
      thirdGender: 0,
      totalVoters: 0,
    }
    record.acNos.add(row.ac_no)
    record.male += toInt(row.male)
    record.female += toInt(row.female)
    record.thirdGender += toInt(row.third_gender)
    record.totalVoters += toInt(row.total)
    districtMap.set(district, record)
  }

  return Array.from(districtMap.entries())
    .map(([district, record]) => ({
      district,
      acCount: record.acNos.size,
      male: record.male,
      female: record.female,
      thirdGender: record.thirdGender,
      totalVoters: record.totalVoters,
    }))
    .sort((a, b) => a.district.localeCompare(b.district))
}

export const Route = createFileRoute('/$state/data/')({
  loader: async ({ params }) => {
    if (!(await stateExists(params.state))) {
      throw notFound()
    }
    const config = await fetchStateConfig(params.state)
    const rows = await fetchElectorCsvRows(config.elector_csv_path)
    return { config, districts: aggregateDistrictData(rows) } satisfies LoaderData
  },
  component: DataDashboard,
})

function DataDashboard() {
  const { config, districts } = Route.useLoaderData()
  const state = config.state_id
  const [sortColumn, setSortColumn] = useState<SortColumn>('district')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [selectedDistricts, setSelectedDistricts] = useState<string[]>([])
  const selectedDistrictSet = useMemo(() => new Set(selectedDistricts), [selectedDistricts])

  const districtsForSummary = useMemo(() => {
    if (selectedDistricts.length === 0) return districts
    return districts.filter((district) => selectedDistrictSet.has(district.district))
  }, [districts, selectedDistrictSet, selectedDistricts.length])

  const totalVoters = districtsForSummary.reduce((sum, d) => sum + d.totalVoters, 0)
  const totalAc = districtsForSummary.reduce((sum, d) => sum + d.acCount, 0)
  const totalMale = districtsForSummary.reduce((sum, d) => sum + d.male, 0)
  const totalFemale = districtsForSummary.reduce((sum, d) => sum + d.female, 0)
  const totalThirdGender = districtsForSummary.reduce((sum, d) => sum + d.thirdGender, 0)

  const sortedDistricts = useMemo(() => {
    const rows = [...districts]
    rows.sort((a, b) => {
      let result = 0
      if (sortColumn === 'district') result = a.district.localeCompare(b.district)
      if (sortColumn === 'acCount') result = a.acCount - b.acCount
      if (sortColumn === 'male') result = a.male - b.male
      if (sortColumn === 'female') result = a.female - b.female
      if (sortColumn === 'thirdGender') result = a.thirdGender - b.thirdGender
      if (sortColumn === 'totalVoters') result = a.totalVoters - b.totalVoters
      return sortDirection === 'asc' ? result : -result
    })
    return rows
  }, [districts, sortColumn, sortDirection])

  const handleSort = (column: SortColumn) => {
    if (column === sortColumn) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortColumn(column)
    setSortDirection('asc')
  }

  const toggleDistrictSelection = (district: string) => {
    setSelectedDistricts((prev) =>
      prev.includes(district) ? prev.filter((item) => item !== district) : [...prev, district],
    )
  }
  const allSelected = selectedDistricts.length === districts.length && districts.length > 0
  const toggleSelectAll = () => setSelectedDistricts(allSelected ? [] : districts.map((d) => d.district))

  return (
    <section className="space-y-6 select-none caret-transparent">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold text-slate-900">{config.state_name}</h2>
        <p className="text-sm text-slate-600">
          Overview of {config.district_label.toLowerCase()}-wise electors information
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label={selectedDistricts.length > 0 ? 'Districts (Selected)' : 'Districts'}
          value={districtsForSummary.length.toLocaleString('en-IN')}
        />
        <StatCard label={`No. of ${config.ac_short_label}`} value={totalAc.toLocaleString('en-IN')} />
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
                <th className="w-12 px-4 py-3 text-center font-semibold">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    aria-label={`Select all ${config.district_label.toLowerCase()}s`}
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/20"
                  />
                </th>
                <SortableHeader
                  align="left"
                  label={config.district_label}
                  active={sortColumn === 'district'}
                  direction={sortDirection}
                  onClick={() => handleSort('district')}
                />
                <SortableHeader
                  align="right"
                  label={`No. of ${config.ac_short_label}`}
                  active={sortColumn === 'acCount'}
                  direction={sortDirection}
                  onClick={() => handleSort('acCount')}
                />
                <SortableHeader
                  align="right"
                  label="Male"
                  active={sortColumn === 'male'}
                  direction={sortDirection}
                  onClick={() => handleSort('male')}
                />
                <SortableHeader
                  align="right"
                  label="Female"
                  active={sortColumn === 'female'}
                  direction={sortDirection}
                  onClick={() => handleSort('female')}
                />
                <SortableHeader
                  align="right"
                  label="Third Gender"
                  active={sortColumn === 'thirdGender'}
                  direction={sortDirection}
                  onClick={() => handleSort('thirdGender')}
                />
                <SortableHeader
                  align="right"
                  label="Total Voters"
                  active={sortColumn === 'totalVoters'}
                  direction={sortDirection}
                  onClick={() => handleSort('totalVoters')}
                />
              </tr>
            </thead>
            <tbody>
              {sortedDistricts.map((row) => (
                <tr
                  key={row.district}
                  className={`border-t border-slate-100 hover:bg-slate-50/70 ${
                    selectedDistrictSet.has(row.district) ? 'font-semibold text-slate-900' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-center">
                    <input
                      type="checkbox"
                      checked={selectedDistrictSet.has(row.district)}
                      onChange={() => toggleDistrictSelection(row.district)}
                      aria-label={`Select ${row.district}`}
                      className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/20"
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900">
                    <Link
                      to="/$state/data/$district"
                      params={{ state, district: row.district }}
                      className="text-blue-700 hover:text-blue-900 hover:underline"
                    >
                      {row.district}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700">{row.acCount.toLocaleString('en-IN')}</td>
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
  const arrow = active ? (direction === 'asc' ? '↑' : '↓') : '↕'
  return (
    <th className={`px-4 py-3 ${alignClass} font-semibold`}>
      <button
        type="button"
        onClick={onClick}
        className="inline-flex items-center gap-1 text-slate-700 hover:text-slate-900 select-none caret-transparent"
      >
        <span>{label}</span>
        <span className="text-xs">{arrow}</span>
      </button>
    </th>
  )
}
