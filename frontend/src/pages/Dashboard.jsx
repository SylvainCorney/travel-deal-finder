import { useState, useEffect } from 'react';
import { Sparkles, TrendingDown } from 'lucide-react';
import SearchForm from '../components/SearchForm';
import DealsTable from '../components/DealsTable';
import PriceAlerts from '../components/PriceAlerts';  // Add this
import { Bell, Search } from 'lucide-react';  // Add icons
import Loading from '../components/Loading';
import { searchAPI, dealsAPI, exportAPI } from '../services/api';

export default function Dashboard() {
  const [searchId, setSearchId] = useState(null);
  const [searchStatus, setSearchStatus] = useState(null);
  const [deals, setDeals] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (searchData) => {
    try {
      setError(null);
      setIsLoading(true);
      setDeals([]);
      
      const response = await searchAPI.createSearch(searchData);
      setSearchId(response.search_id);
      
      pollSearchStatus(response.search_id);
    } catch (err) {
      setError(err.message || 'Failed to start search');
      setIsLoading(false);
    }
  };

  const pollSearchStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const status = await searchAPI.getSearchStatus(id);
        setSearchStatus(status);
        
        if (status.status === 'completed') {
          clearInterval(interval);
          const dealsData = await dealsAPI.getDealsBySearch(id);
          setDeals(dealsData.deals || []);
          setIsLoading(false);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setError(status.error_message || 'Search failed');
          setIsLoading(false);
        }
      } catch (err) {
        clearInterval(interval);
        setError('Failed to get search status');
        setIsLoading(false);
      }
    }, 2000);

    setTimeout(() => clearInterval(interval), 120000);
  };

  const handleExport = async () => {
    if (searchId) {
      try {
        await exportAPI.exportToExcel(searchId);
      } catch (err) {
        alert('Failed to export: ' + err.message);
      }
    }
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center gap-3 bg-white/60 backdrop-blur-sm px-6 py-3 rounded-full border border-white/40 shadow-lg mb-6">
            <Sparkles className="w-5 h-5 text-primary-600" />
            <span className="text-sm font-medium text-slate-700">AI-Powered Deal Finder</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-display font-bold text-slate-900 mb-4 tracking-tight">
            Travel Deal
            <span className="bg-gradient-to-r from-primary-600 to-primary-700 bg-clip-text text-transparent"> Scraper</span>
          </h1>
          
          <p className="text-xl text-slate-600 max-w-2xl mx-auto text-balance">
            Find the best hotel and flight deals across multiple booking sites in seconds
          </p>
        </header>

        <div className="space-y-8">
          <SearchForm onSearch={handleSearch} isLoading={isLoading} />

          {error && (
            <div className="glass-card rounded-2xl p-6 border-l-4 border-red-500 animate-slide-up">
              <h3 className="font-semibold text-red-800 mb-1">Error</h3>
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {isLoading && (
            <Loading 
              progress={searchStatus?.progress || 0}
              message="Searching multiple sites for the best deals..."
            />
          )}

          {!isLoading && deals.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in">
                <div className="glass-card rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <TrendingDown className="w-5 h-5 text-primary-600" />
                    </div>
                    <span className="text-sm font-medium text-slate-600">Best Price</span>
                  </div>
                  <div className="text-3xl font-display font-bold text-slate-900">
                    ${Math.min(...deals.map(d => d.price)).toFixed(2)}
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Sparkles className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium text-slate-600">Total Deals</span>
                  </div>
                  <div className="text-3xl font-display font-bold text-slate-900">
                    {deals.length}
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-orange-100 rounded-lg">
                      <TrendingDown className="w-5 h-5 text-orange-600" />
                    </div>
                    <span className="text-sm font-medium text-slate-600">Avg Price</span>
                  </div>
                  <div className="text-3xl font-display font-bold text-slate-900">
                    ${(deals.reduce((sum, d) => sum + d.price, 0) / deals.length).toFixed(2)}
                  </div>
                </div>
              </div>

              <DealsTable deals={deals} onExport={handleExport} />
            </>
          )}
        </div>

        <footer className="text-center mt-16 pb-8">
          <p className="text-slate-500 text-sm">
            Built with React, FastAPI, and Playwright • Scrapes multiple travel sites for the best deals
          </p>
        </footer>
      </div>
    </div>
  );
}
