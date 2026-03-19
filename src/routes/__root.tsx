import { createRootRouteWithContext, Outlet, Link, useLocation, useNavigate } from '@tanstack/react-router';
import type { QueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react';
import { Search, LayoutGrid, Map as MapIcon } from 'lucide-react';
import Logo from '../assets/logo.png';
import { DisclaimerModal } from '../components/common/DisclaimerModal';
import { fetchStateConfig, fetchStatesRegistry, normalizeStateId, stateExists, type AppConfig, type StateRegistryItem } from '../services/appConfig';
import { fetchElectorCsvRows, type ElectorCsvRow } from '../services/electors';

interface RouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

function RootComponent() {
    const [isDisclaimerOpen, setIsDisclaimerOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [config, setConfig] = useState<AppConfig | null>(null);
    const [states, setStates] = useState<StateRegistryItem[]>([]);
    const [electorRows, setElectorRows] = useState<ElectorCsvRow[]>([]);
    const [loadedStateId, setLoadedStateId] = useState<string | null>(null);
    const location = useLocation();
    const navigate = useNavigate();

    const routeStateId = normalizeStateId(location.pathname.split('/').filter(Boolean)[0] ?? null);
    const routeStateExists = routeStateId ? states.some((state) => state.id === routeStateId) : false;
    const activeStateId = routeStateExists ? routeStateId : (states[0]?.id ?? routeStateId ?? null);
    const menuStates = useMemo(() => states.filter((state) => state.showInMenu), [states]);
    const selectedMenuStateId =
        activeStateId && menuStates.some((state) => state.id === activeStateId)
            ? activeStateId
            : (menuStates[0]?.id ?? '');

    useEffect(() => {
        let active = true;
        fetchStatesRegistry()
            .then((registryStates) => {
                if (active) setStates(registryStates);
            })
            .catch(() => {
                if (active) {
                    setStates([]);
                }
            });
        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        if (!activeStateId) return;
        let active = true;

        stateExists(activeStateId)
            .then((exists) => {
                if (!exists) {
                    if (active) {
                        setConfig(null);
                        setElectorRows([]);
                        setLoadedStateId(activeStateId);
                    }
                    return null;
                }
                return fetchStateConfig(activeStateId);
            })
            .then((cfg) => {
                if (!cfg) return null;
                if (active) setConfig(cfg);
                return fetchElectorCsvRows(cfg.elector_csv_path);
            })
            .then((rows) => {
                if (!rows) return;
                if (active) {
                    setElectorRows(rows);
                    setLoadedStateId(activeStateId);
                }
            })
            .catch(() => {
                if (active) {
                    setElectorRows([]);
                    setLoadedStateId(activeStateId);
                }
            });

        return () => {
            active = false;
        };
    }, [activeStateId]);

    const filteredSearchRows = useMemo(() => {
        const q = searchTerm.trim().toLowerCase();
        if (!q) return [];
        if (!activeStateId || loadedStateId !== activeStateId) return [];

        return electorRows
            .filter((row) => {
                const district = row.district_name?.toLowerCase() ?? '';
                const ac = row.ac_name?.toLowerCase() ?? '';
                const acNo = row.ac_no?.toLowerCase() ?? '';
                return district.includes(q) || ac.includes(q) || acNo.includes(q);
            })
            .slice(0, 10);
    }, [activeStateId, electorRows, loadedStateId, searchTerm]);

    const handleSelectSearchRow = (row: ElectorCsvRow) => {
        if (!activeStateId) return;
        setSearchTerm('');
        navigate({
            to: '/$state/data/$district',
            params: { state: activeStateId, district: row.district_name },
        });
    };

    const handleStateSwitch = (nextStateId: string) => {
        const normalized = normalizeStateId(nextStateId);
        if (!normalized) return;
        setSearchTerm('');
        navigate({
            to: '/$state/data',
            params: { state: normalized },
        });
    };

    const isSearchLoading = !activeStateId || loadedStateId !== activeStateId;
    const searchPlaceholder = `Search ${config?.district_label ?? 'district'} / ${config?.ac_label ?? 'AC name'} / ${config?.ac_short_label ?? 'AC'} no...`;
    const electionTitle = config?.election_title ?? 'State Election Dashboard';
    const electionSubtitle = config?.election_subtitle ?? 'Election Analysis';


    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 flex flex-col">
            <DisclaimerModal
                isOpen={isDisclaimerOpen}
                onClose={() => setIsDisclaimerOpen(false)}
            />

            {/* Header */}
            <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
                    <Link
                        to="/"
                        className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
                    >
                        <div className="w-18 h-18 bg-white-500 rounded-xl flex items-center justify-center text-white font-bold text-xl">
                            <img src={Logo} alt="Logo" className="w-18 h-18" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-slate-900 tracking-tight leading-none">
                                {electionTitle}
                            </h1>
                            <p className="text-s text-slate-500 font-medium mt-1">
                                {electionSubtitle}
                            </p>
                        </div>
                    </Link>

                    <div className="hidden md:block min-w-[220px]">
                        <select
                            value={selectedMenuStateId}
                            onChange={(e) => handleStateSwitch(e.target.value)}
                            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        >
                            {menuStates.map((state) => (
                                <option key={state.id} value={state.id}>
                                    {state.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Main Tabs (Desktop) */}
                        <div className="hidden md:flex bg-slate-100 p-1 rounded-xl">
                            <Link
                                to="/$state/data"
                                params={{ state: activeStateId ?? 'tn' }}
                                activeProps={{
                                    className: 'bg-white text-blue-600 shadow-sm',
                                }}
                                inactiveProps={{
                                    className: 'text-slate-500 hover:text-slate-700',
                                }}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
                            >
                                <LayoutGrid size={18} />
                                Data
                            </Link>
                            <Link
                                to="/$state/map"
                                params={{ state: activeStateId ?? 'tn' }}
                                activeProps={{
                                    className: 'bg-white text-blue-600 shadow-sm',
                                }}
                                inactiveProps={{
                                    className: 'text-slate-500 hover:text-slate-700',
                                }}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
                            >
                                <MapIcon size={18} />
                                Map
                            </Link>
                        </div>

                        <div className="relative w-full max-w-xs hidden md:block">
                            <div className="relative group">
                                <Search
                                    className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"
                                    size={18}
                                />
                                <input
                                    type="text"
                                    placeholder={searchPlaceholder}
                                    className="w-full pl-10 pr-4 py-2.5 bg-slate-100 border-transparent focus:bg-white border focus:border-blue-500 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 transition-all"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>

                            <div className="flex items-center justify-end gap-3 mt-1.5 px-1">
                                <p className="text-[10px] text-slate-400 font-medium">
                                    Source Code:
                                    <a
                                        href="https://github.com/electionin/state-election"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-slate-500 hover:text-blue-600 transition-colors"
                                    >
                                        Election in India
                                    </a>
                                </p>
                                <span className="text-[10px] text-slate-300">•</span>
                                <button
                                    onClick={() => setIsDisclaimerOpen(true)}
                                    className="text-[10px] text-slate-400 hover:text-blue-600 font-medium transition-colors"
                                >
                                    Disclaimer
                                </button>
                            </div>

                            {searchTerm && (
                                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-50">
                                    {isSearchLoading ? (
                                        <div className="p-4 text-center text-slate-500 text-sm">Loading...</div>
                                    ) : filteredSearchRows.length > 0 ? (
                                        filteredSearchRows.map((row) => (
                                            <button
                                                type="button"
                                                key={`${row.district_no}-${row.ac_no}`}
                                                onClick={() => handleSelectSearchRow(row)}
                                                className="w-full text-left px-4 py-3 hover:bg-slate-50 border-b border-slate-50 last:border-0"
                                            >
                                                <p className="font-medium text-slate-800">{row.ac_name}</p>
                                                <p className="text-xs text-slate-500">
                                                    AC {row.ac_no} • {row.district_name}
                                                </p>
                                            </button>
                                        ))
                                    ) : (
                                        <div className="p-4 text-center text-slate-500 text-sm">No results found</div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Mobile Search and Tabs */}
            <div className="md:hidden bg-white border-b border-slate-200">
                <div className="flex p-2 gap-2 border-b border-slate-100">
                    <Link
                        to="/$state/data"
                        params={{ state: activeStateId ?? 'tn' }}
                        activeProps={{
                            className: 'bg-blue-50 text-blue-600',
                        }}
                        inactiveProps={{
                            className: 'text-slate-500',
                        }}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                        <LayoutGrid size={16} />
                        Data
                    </Link>
                    <Link
                        to="/$state/map"
                        params={{ state: activeStateId ?? 'tn' }}
                        activeProps={{
                            className: 'bg-blue-50 text-blue-600',
                        }}
                        inactiveProps={{
                            className: 'text-slate-500',
                        }}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                        <MapIcon size={16} />
                        Map
                    </Link>
                </div>

                <div className="p-4">
                    <div className="relative">
                        <Search
                            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400"
                            size={18}
                        />
                        <input
                            type="text"
                            placeholder={searchPlaceholder}
                            className="w-full pl-10 pr-4 py-2.5 bg-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        <div className="mt-2">
                            <select
                                value={selectedMenuStateId}
                                onChange={(e) => handleStateSwitch(e.target.value)}
                                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                            >
                                {menuStates.map((state) => (
                                    <option key={state.id} value={state.id}>
                                        {state.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        {searchTerm && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-50">
                                {isSearchLoading ? (
                                    <div className="p-4 text-center text-slate-500 text-sm">Loading...</div>
                                ) : filteredSearchRows.length > 0 ? (
                                    filteredSearchRows.map((row) => (
                                        <button
                                            type="button"
                                            key={`m-${row.district_no}-${row.ac_no}`}
                                            onClick={() => handleSelectSearchRow(row)}
                                            className="w-full text-left px-4 py-3 hover:bg-slate-50 border-b border-slate-50 last:border-0"
                                        >
                                            <p className="font-medium text-slate-800">{row.ac_name}</p>
                                            <p className="text-xs text-slate-500">
                                                AC {row.ac_no} • {row.district_name}
                                            </p>
                                        </button>
                                    ))
                                ) : (
                                    <div className="p-4 text-center text-slate-500 text-sm">No results found</div>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="flex items-center justify-between px-1 mt-3">
                        <p className="text-[10px] text-slate-400 font-medium">
                            Source Code:
                            <a
                                href="https://github.com/electionin/state-election"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-slate-500 hover:text-blue-600 transition-colors"
                            >
                                Indian State Election
                            </a>
                        </p>
                        <button
                            onClick={() => setIsDisclaimerOpen(true)}
                            className="text-[10px] text-slate-400 hover:text-blue-600 font-medium transition-colors"
                        >
                            Disclaimer
                        </button>
                    </div>
                </div>
            </div>

            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
                <Outlet />
            </main>
            {/* <TanStackRouterDevtools /> */}
        </div>
    );
}

// function RootComponent() {
//   return <Outlet />
// }
