export type AppConfig = {
  state_id: string
  state_name: string
  election_title: string
  election_subtitle: string
  elector_csv_path: string
  district_label: string
  ac_label: string
  ac_short_label: string
}

export type StateRegistryItem = {
  id: string
  name: string
  showInMenu: boolean
}

type StateRegistryRawItem = {
  id?: string
  code?: string
  name?: string
  show_in_menu?: boolean
}

const DEFAULT_CONFIG: AppConfig = {
  state_id: 'tn',
  state_name: 'State Election',
  election_title: 'State Election Dashboard',
  election_subtitle: 'Election Analysis',
  elector_csv_path: '/data/states/tn/electors.csv',
  district_label: 'District',
  ac_label: 'Assembly Constituency',
  ac_short_label: 'AC',
}

const DEFAULT_STATES: StateRegistryItem[] = [{ id: 'tn', name: 'Tamil Nadu', showInMenu: true }]

export function normalizeStateId(stateId: string | null | undefined): string {
  return (stateId ?? '').trim().toLowerCase()
}

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path)
    if (!response.ok) return null

    const contentType = response.headers.get('content-type')?.toLowerCase() ?? ''
    if (!contentType.includes('application/json')) return null

    return (await response.json()) as T
  } catch {
    return null
  }
}

function normalizeConfig(data: Partial<AppConfig>): AppConfig {
  return {
    state_id: data.state_id ?? DEFAULT_CONFIG.state_id,
    state_name: data.state_name ?? DEFAULT_CONFIG.state_name,
    election_title: data.election_title ?? DEFAULT_CONFIG.election_title,
    election_subtitle: data.election_subtitle ?? DEFAULT_CONFIG.election_subtitle,
    elector_csv_path: data.elector_csv_path ?? DEFAULT_CONFIG.elector_csv_path,
    district_label: data.district_label ?? DEFAULT_CONFIG.district_label,
    ac_label: data.ac_label ?? DEFAULT_CONFIG.ac_label,
    ac_short_label: data.ac_short_label ?? DEFAULT_CONFIG.ac_short_label,
  }
}

export async function fetchStatesRegistry(path: string = '/data/states.json'): Promise<StateRegistryItem[]> {
  const data = await fetchJson<{ states?: StateRegistryRawItem[] }>(path)
  if (!data) return DEFAULT_STATES

  const states =
    data.states
      ?.filter((s) => (s.code || s.id) && s.name)
      .map((s) => ({
        id: normalizeStateId(s.code ?? s.id ?? ''),
        name: (s.name ?? '').trim(),
        showInMenu: s.show_in_menu ?? false,
      }))
      .filter((s) => s.id.length > 0 && s.name.length > 0) ?? []
  return states.length > 0 ? states : DEFAULT_STATES
}

export async function stateExists(stateId: string): Promise<boolean> {
  const normalized = normalizeStateId(stateId)
  if (!normalized) return false
  const states = await fetchStatesRegistry()
  const listed = states.some((s) => s.id === normalized)
  if (!listed) return false

  const config = await fetchJson<Partial<AppConfig>>(`/data/states/${normalized}/config.json`)
  if (!config) return false

  const configStateId = normalizeStateId(config.state_id)
  const csvPath = (config.elector_csv_path ?? '').trim()
  return configStateId === normalized && csvPath.length > 0
}

export async function fetchStateConfig(stateId: string): Promise<AppConfig> {
  const safeStateId = normalizeStateId(stateId) || DEFAULT_CONFIG.state_id
  const configPath = `/data/states/${safeStateId}/config.json`

  try {
    const response = await fetch(configPath)
    if (!response.ok) {
      return {
        ...DEFAULT_CONFIG,
        state_id: safeStateId,
      }
    }

    const data = (await response.json()) as Partial<AppConfig>
    return normalizeConfig({ ...data, state_id: data.state_id ?? safeStateId })
  } catch {
    return {
      ...DEFAULT_CONFIG,
      state_id: safeStateId,
    }
  }
}
