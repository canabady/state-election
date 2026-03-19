import { createFileRoute, redirect } from '@tanstack/react-router'
import { fetchStatesRegistry } from '../services/appConfig'

export const Route = createFileRoute('/')({
  loader: async () => {
    const states = await fetchStatesRegistry()
    const visibleState = states.find((s) => s.showInMenu)
    const state = visibleState?.id ?? states[0]?.id ?? 'tn'
    throw redirect({ to: '/$state/data', params: { state } })
  },
})
