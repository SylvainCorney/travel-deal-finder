import { useState } from 'react';
import { Search, MapPin, Calendar, Hotel, Plane, Plus, X, Navigation, Package } from 'lucide-react';

export default function SearchForm({ onSearch, isLoading }) {
  const [formData, setFormData] = useState({
    origin: '',
    location: '',
    check_in_date: '',
    check_out_date: '',
    hotels: [],
    airlines: [],
    sources: [],
  });
  
  const [hotelInput, setHotelInput] = useState('');
  const [airlineInput, setAirlineInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(formData);
  };

  const addHotel = () => {
    if (hotelInput.trim()) {
      setFormData({ ...formData, hotels: [...formData.hotels, hotelInput.trim()] });
      setHotelInput('');
    }
  };

  const removeHotel = (index) => {
    setFormData({
      ...formData,
      hotels: formData.hotels.filter((_, i) => i !== index),
    });
  };

  const addAirline = () => {
    if (airlineInput.trim()) {
      setFormData({ ...formData, airlines: [...formData.airlines, airlineInput.trim()] });
      setAirlineInput('');
    }
  };

  const removeAirline = (index) => {
    setFormData({
      ...formData,
      airlines: formData.airlines.filter((_, i) => i !== index),
    });
  };

  const toggleSource = (source) => {
    if (formData.sources.includes(source)) {
      setFormData({
        ...formData,
        sources: formData.sources.filter(s => s !== source),
      });
    } else {
      setFormData({
        ...formData,
        sources: [...formData.sources, source],
      });
    }
  };

  return (
    <div className="glass-card rounded-3xl p-8 animate-slide-up">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl shadow-lg">
          <Search className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-display font-bold text-slate-800">Search Travel Deals</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Origin */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
            <Navigation className="w-4 h-4 text-primary-600" />
            From (Origin)
          </label>
          <input
            type="text"
            value={formData.origin}
            onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
            placeholder="e.g., Montreal, Toronto, YUL"
            className="input-field"
          />
        </div>

        {/* Destination */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary-600" />
            Destination
          </label>
          <input
            type="text"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="e.g., Cancun, Paris, Tokyo"
            className="input-field"
            required
          />
        </div>

        {/* Dates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-primary-600" />
              Departure Date
            </label>
            <input
              type="date"
              value={formData.check_in_date}
              onChange={(e) => setFormData({ ...formData, check_in_date: e.target.value })}
              className="input-field"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-primary-600" />
              Return Date
            </label>
            <input
              type="date"
              value={formData.check_out_date}
              onChange={(e) => setFormData({ ...formData, check_out_date: e.target.value })}
              className="input-field"
              required
            />
          </div>
        </div>

        {/* Source Selection - UPDATED WITH PACKAGES */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">
            Search For
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <button
              type="button"
              onClick={() => toggleSource('hotels')}
              className={`p-4 rounded-xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-2 ${
                formData.sources.includes('hotels')
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
              }`}
            >
              <Hotel className="w-5 h-5" />
              <span className="font-medium text-sm">Hotels Only</span>
            </button>
            <button
              type="button"
              onClick={() => toggleSource('flights')}
              className={`p-4 rounded-xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-2 ${
                formData.sources.includes('flights')
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
              }`}
            >
              <Plane className="w-5 h-5" />
              <span className="font-medium text-sm">Flights Only</span>
            </button>
            <button
              type="button"
              onClick={() => toggleSource('packages')}
              className={`p-4 rounded-xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-2 ${
                formData.sources.includes('packages')
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
              }`}
            >
              <Package className="w-5 h-5" />
              <span className="font-medium text-sm">Flight + Hotel</span>
            </button>
            <button
              type="button"
              onClick={() => toggleSource('all_inclusive')}
              className={`p-4 rounded-xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-2 ${
                formData.sources.includes('all_inclusive')
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
              }`}
            >
              <Package className="w-5 h-5" />
              <span className="font-medium text-sm">All-Inclusive</span>
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            💡 Packages include flights + hotel. All-Inclusive adds meals + transfers.
          </p>
        </div>

        {/* Optional: Specific Hotels */}
        {(formData.sources.includes('hotels') || formData.sources.includes('packages') || formData.sources.includes('all_inclusive')) && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Specific Hotels (Optional)
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={hotelInput}
                onChange={(e) => setHotelInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addHotel())}
                placeholder="e.g., Hilton, Riu, Hyatt"
                className="input-field"
              />
              <button
                type="button"
                onClick={addHotel}
                className="px-4 py-2 bg-primary-100 text-primary-700 rounded-xl hover:bg-primary-200 transition-colors"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
            {formData.hotels.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.hotels.map((hotel, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg text-sm"
                  >
                    {hotel}
                    <button
                      type="button"
                      onClick={() => removeHotel(index)}
                      className="hover:text-primary-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Optional: Specific Airlines */}
        {(formData.sources.includes('flights') || formData.sources.includes('packages') || formData.sources.includes('all_inclusive')) && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Specific Airlines (Optional)
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={airlineInput}
                onChange={(e) => setAirlineInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAirline())}
                placeholder="e.g., Air Canada, Sunwing"
                className="input-field"
              />
              <button
                type="button"
                onClick={addAirline}
                className="px-4 py-2 bg-primary-100 text-primary-700 rounded-xl hover:bg-primary-200 transition-colors"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
            {formData.airlines.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.airlines.map((airline, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg text-sm"
                  >
                    {airline}
                    <button
                      type="button"
                      onClick={() => removeAirline(index)}
                      className="hover:text-primary-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || formData.sources.length === 0}
          className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Find Best Deals
            </>
          )}
        </button>
      </form>
    </div>
  );
}
