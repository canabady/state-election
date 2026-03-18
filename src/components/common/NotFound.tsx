import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import React from 'react';
import { Link, useRouter } from '@tanstack/react-router';

export const NotFound: React.FC = () => {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center animate-in fade-in duration-500">
      <div className="bg-slate-50 p-6 rounded-full mb-6 relative group">
        <div className="absolute inset-0 bg-blue-100 rounded-full scale-0 group-hover:scale-110 transition-transform duration-300 opacity-50"></div>
        <FileQuestion className="h-16 w-16 text-slate-400 group-hover:text-blue-500 transition-colors relative z-10" />
      </div>

      <h2 className="text-3xl font-bold text-slate-900 mb-2">Page Not Found</h2>
      <p className="max-w-md text-slate-500 mb-8 leading-relaxed">
        The page you are looking for doesn't exist.
        Please check the URL or try navigating back.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
        <button
          onClick={() => router.history.back()}
          className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300 transition-all focus:outline-none focus:ring-4 focus:ring-slate-100"
        >
          <ArrowLeft size={18} />
          Go Back
        </button>

        <Link
          to="/"
          className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 shadow-sm hover:shadow-md transition-all focus:outline-none focus:ring-4 focus:ring-blue-500/20"
        >
          <Home size={18} />
          Go Home
        </Link>
      </div>
    </div>
  );
};

