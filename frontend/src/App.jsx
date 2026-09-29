import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PriceAlerts from './components/PriceAlerts';
import { Bell, Search } from 'lucide-react';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<PriceAlerts />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

function Navigation() {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
    <nav className="bg-white shadow-sm mb-8">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-2xl font-display font-bold text-slate-800">
            Travel Deal Finder
          </Link>
          
          <div className="flex items-center gap-3">
            <Link 
              to="/" 
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                isActive('/') 
                  ? 'bg-primary-600 text-white shadow-lg' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Search className="w-5 h-5" />
              Search Deals
            </Link>
            
            <Link 
              to="/alerts" 
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                isActive('/alerts') 
                  ? 'bg-primary-600 text-white shadow-lg' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Bell className="w-5 h-5" />
              Price Alerts
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default App;
