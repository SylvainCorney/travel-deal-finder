import { Loader2 } from 'lucide-react';

export default function Loading({ progress = 0, message = 'Searching for deals...' }) {
  return (
    <div className="glass-card rounded-3xl p-12 text-center animate-fade-in">
      <div className="relative w-24 h-24 mx-auto mb-6">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-400 to-primary-600 rounded-full animate-pulse" />
        <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
        </div>
      </div>
      
      <h3 className="text-xl font-display font-semibold text-slate-800 mb-2">
        {message}
      </h3>
      
      {progress > 0 && (
        <div className="max-w-md mx-auto mt-6">
          <div className="flex justify-between text-sm text-slate-600 mb-2">
            <span>Progress</span>
            <span className="font-semibold">{progress}%</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      
      <p className="text-slate-500 mt-4 text-sm">
        This may take a few moments...
      </p>
    </div>
  );
}
