import { Hotel, Plane, ExternalLink, DollarSign, Star, Clock, MapPin, Package, Check } from 'lucide-react';
import { useState } from 'react';

export default function DealsTable({ deals, onExport }) {
  const [filter, setFilter] = useState('all');

  const filteredDeals = deals.filter(deal => {
    if (filter === 'all') return true;
    if (filter === 'hotels') return deal.deal_type === 'hotel';
    if (filter === 'flights') return deal.deal_type === 'flight';
    if (filter === 'packages') return deal.deal_type === 'package';
    if (filter === 'all_inclusive') return deal.deal_type === 'all_inclusive';
    return true;
  });

  const sortedDeals = [...filteredDeals].sort((a, b) => a.price - b.price);

  if (deals.length === 0) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center animate-fade-in">
        <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Search className="w-10 h-10 text-slate-400" />
        </div>
        <h3 className="text-xl font-display font-semibold text-slate-700 mb-2">No Results Yet</h3>
        <p className="text-slate-500">Start a search to find the best travel deals</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-3xl p-8 animate-slide-up">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-display font-bold text-slate-800 mb-1">
            Found {sortedDeals.length} Deals
          </h2>
          <p className="text-slate-500">Best prices from multiple sources</p>
        </div>
        
        {onExport && (
          <button
            onClick={onExport}
            className="btn-secondary flex items-center gap-2"
          >
            <DollarSign className="w-5 h-5" />
            Export to Excel
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-xl font-medium transition-all ${
            filter === 'all'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          All ({deals.length})
        </button>
        <button
          onClick={() => setFilter('hotels')}
          className={`px-4 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
            filter === 'hotels'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          <Hotel className="w-4 h-4" />
          Hotels ({deals.filter(d => d.deal_type === 'hotel').length})
        </button>
        <button
          onClick={() => setFilter('flights')}
          className={`px-4 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
            filter === 'flights'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          <Plane className="w-4 h-4" />
          Flights ({deals.filter(d => d.deal_type === 'flight').length})
        </button>
        <button
          onClick={() => setFilter('packages')}
          className={`px-4 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
            filter === 'packages'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          <Package className="w-4 h-4" />
          Packages ({deals.filter(d => d.deal_type === 'package').length})
        </button>
        <button
          onClick={() => setFilter('all_inclusive')}
          className={`px-4 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
            filter === 'all_inclusive'
              ? 'bg-green-600 text-white shadow-lg'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          <Package className="w-4 h-4" />
          All-Inclusive ({deals.filter(d => d.deal_type === 'all_inclusive').length})
        </button>
      </div>

      {/* Deals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedDeals.map((deal, index) => (
          <DealCard key={deal.id || index} deal={deal} />
        ))}
      </div>
    </div>
  );
}

function DealCard({ deal }) {
  const isHotel = deal.deal_type === 'hotel';
  const isFlight = deal.deal_type === 'flight';
  const isPackage = deal.deal_type === 'package';
  const isAllInclusive = deal.deal_type === 'all_inclusive';

  const getCardColor = () => {
    if (isAllInclusive) return 'border-green-200 bg-green-50/50';
    if (isPackage) return 'border-purple-200 bg-purple-50/50';
    if (isHotel) return 'border-blue-100';
    return 'border-orange-100';
  };

  const getIconBg = () => {
    if (isAllInclusive) return 'bg-green-100';
    if (isPackage) return 'bg-purple-100';
    if (isHotel) return 'bg-blue-100';
    return 'bg-orange-100';
  };

  const getIconColor = () => {
    if (isAllInclusive) return 'text-green-600';
    if (isPackage) return 'text-purple-600';
    if (isHotel) return 'text-blue-600';
    return 'text-orange-600';
  };

  return (
    <div className={`bg-white border-2 ${getCardColor()} rounded-2xl p-6 hover:shadow-xl transition-all duration-300 group`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl ${getIconBg()}`}>
            {(isPackage || isAllInclusive) ? (
              <Package className={`w-5 h-5 ${getIconColor()}`} />
            ) : isHotel ? (
              <Hotel className={`w-5 h-5 ${getIconColor()}`} />
            ) : (
              <Plane className={`w-5 h-5 ${getIconColor()}`} />
            )}
          </div>
          <div>
            <h3 className="font-display font-semibold text-slate-800 text-lg leading-tight">
              {deal.hotel_name || deal.airline || deal.name}
            </h3>
            <p className="text-sm text-slate-500 mt-0.5">{deal.source}</p>
            {isAllInclusive && (
              <span className="inline-block mt-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                All-Inclusive
              </span>
            )}
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-display font-bold text-primary-600">
            ${deal.price.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">{deal.currency}</div>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {/* Hotel/Package Info */}
        {(isHotel || isPackage || isAllInclusive) && (
          <>
            {deal.hotel_rating && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                <span className="font-medium">{deal.hotel_rating}/10</span>
              </div>
            )}
            {deal.room_type && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Hotel className="w-4 h-4" />
                <span>{deal.room_type}</span>
              </div>
            )}
            {deal.meal_plan && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-green-600" />
                <span className="font-medium">{deal.meal_plan}</span>
              </div>
            )}
          </>
        )}

        {/* Flight Info */}
        {(isFlight || isPackage || isAllInclusive) && deal.airline && (
          <>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Plane className="w-4 h-4" />
              <span>{deal.airline}</span>
            </div>
            {deal.departure_time && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Clock className="w-4 h-4" />
                <span>{deal.departure_time} → {deal.arrival_time}</span>
              </div>
            )}
          </>
        )}

        {/* Package Inclusions */}
        {(isPackage || isAllInclusive) && (
          <div className="flex flex-wrap gap-2 mt-2">
            {deal.includes_flight && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                <Check className="w-3 h-3" /> Flight
              </span>
            )}
            {deal.includes_hotel && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                <Check className="w-3 h-3" /> Hotel
              </span>
            )}
            {deal.includes_transfer && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                <Check className="w-3 h-3" /> Transfer
              </span>
            )}
            {deal.includes_meals && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                <Check className="w-3 h-3" /> Meals
              </span>
            )}
          </div>
        )}
        
        {deal.location && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <MapPin className="w-4 h-4" />
            <span>{deal.location}</span>
          </div>
        )}
        
        {deal.check_in_date && (
          <div className="text-sm text-slate-500">
            {deal.check_in_date} → {deal.check_out_date}
          </div>
        )}
      </div>

      {deal.url && (
        
         <a href={deal.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition-colors group-hover:bg-primary-50 group-hover:text-primary-700"
        >
          View Deal
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </div>
  );
}
