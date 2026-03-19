import { createFileRoute, notFound } from '@tanstack/react-router'
import { stateExists } from '../../services/appConfig'

export const Route = createFileRoute('/$state/map')({
  loader: async ({ params }) => {
    if (!(await stateExists(params.state))) {
      throw notFound()
    }
    return null
  },
  component: MapPlaceholder,
})

function MapPlaceholder() {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-xl font-bold text-slate-900">Map View</h2>
      <p className="mt-2 text-sm text-slate-600">Map dashboard will be added here.</p>
    </section>
  )
}
