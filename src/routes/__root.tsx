import { createRootRouteWithContext, Outlet, Link, useNavigate } from '@tanstack/react-router';
import type { QueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react';
import { Search, LayoutGrid, Map as MapIcon } from 'lucide-react';
import Logo from '../assets/logo.png';
import { DisclaimerModal } from '../components/common/DisclaimerModal';
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
    const [electorRows, setElectorRows] = useState<ElectorCsvRow[]>([]);
    const [isSearchLoading, setIsSearchLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        let active = true;
        fetchElectorCsvRows()
            .then((rows) => {
                if (active) {
                    setElectorRows(rows);
                }
            })
            .catch(() => {
                if (active) {
                    setElectorRows([]);
                }
            })
            .finally(() => {
                if (active) {
                    setIsSearchLoading(false);
                }
            });
        return () => {
            active = false;
        };
    }, []);

    const filteredSearchRows = useMemo(() => {
        const q = searchTerm.trim().toLowerCase();
        if (!q) return [];

        return electorRows
            .filter((row) => {
                const district = row.district_name?.toLowerCase() ?? '';
                const ac = row.ac_name?.toLowerCase() ?? '';
                const acNo = row.ac_no?.toLowerCase() ?? '';
                return district.includes(q) || ac.includes(q) || acNo.includes(q);
            })
            .slice(0, 10);
    }, [electorRows, searchTerm]);

    const handleSelectSearchRow = (row: ElectorCsvRow) => {
        setSearchTerm('');
        navigate({
            to: '/data/$district',
            params: { district: row.district_name },
        });
    };


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
                                2026 Tamil Nadu State Election
                            </h1>
                            <p className="text-s text-slate-500 font-medium mt-1">
                                Assembly Election Analysis
                            </p>
                        </div>
                    </Link>

                    <div className="flex items-center gap-4">
                        {/* Main Tabs (Desktop) */}
                        <div className="hidden md:flex bg-slate-100 p-1 rounded-xl">
                            <Link
                                to="/data"
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
                                to="/map"
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
                                    placeholder="Search district / AC name / AC no..."
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
                        to="/data"
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
                        to="/map"
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
                            placeholder="Search district / AC name / AC no..."
                            className="w-full pl-10 pr-4 py-2.5 bg-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
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
                            Crafted with :) by{' '}
                            <a
                                href="https://gnoeee.github.io"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-slate-500 hover:text-blue-600 transition-colors"
                            >
                                Opendata Kerala
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
