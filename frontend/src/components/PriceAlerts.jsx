import { useState, useEffect } from 'react';
import { Bell, BellOff, Plus, X, Edit2, Trash2, DollarSign, MapPin, Hotel, Calendar, Mail } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function PriceAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || '');
  const [loading, setLoading] = useState(false);

  // Load alerts on mount
  useEffect(() => {
    if (userEmail) {
      loadAlerts();
    }
  }, [userEmail]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/alerts/alerts?email=${userEmail}`);
      setAlerts(response.data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteAlert = async (alertId) => {
    if (!confirm('Are you sure you want to delete this price alert?')) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/alerts/alerts/${alertId}`);
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Error deleting alert:', error);
      alert('Failed to delete alert');
    }
  };

  const toggleAlert = async (alert) => {
    try {
      const endpoint = alert.is_active ? 'pause' : 'resume';
      const response = await axios.post(`${API_BASE_URL}/alerts/alerts/${alert.id}/${endpoint}`);
      
      setAlerts(alerts.map(a => a.id === alert.id ? response.data : a));
    } catch (error) {
      console.error('Error toggling alert:', error);
      alert('Failed to toggle alert');
    }
  };

  if (!userEmail) {
    return <EmailPrompt onEmailSet={(email) => {
      setUserEmail(email);
      localStorage.setItem('userEmail', email);
    }} />;
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-slate-800 flex items-center gap-3">
            <Bell className="w-8 h-8 text-primary-600" />
            Price Alerts
          </h1>
          <p className="text-slate-500 mt-2">Get notified when your dream vacation hits your target price</p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Create Alert
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard 
          label="Total Alerts" 
          value={alerts.length} 
          icon={Bell}
          color="blue"
        />
        <StatCard 
          label="Active" 
          value={alerts.filter(a => a.is_active).length} 
          icon={Bell}
          color="green"
        />
        <StatCard 
          label="Triggered" 
          value={alerts.filter(a => a.notification_sent).length} 
          icon={DollarSign}
          color="purple"
        />
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Loading alerts...</p>
        </div>
      ) : alerts.length === 0 ? (
        <EmptyState onCreateClick={() => setShowCreateModal(true)} />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {alerts.map(alert => (
            <AlertCard 
              key={alert.id} 
              alert={alert} 
              onDelete={deleteAlert}
              onToggle={toggleAlert}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateAlertModal 
          userEmail={userEmail}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            loadAlerts();
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}

function EmailPrompt({ onEmailSet }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email && email.includes('@')) {
      onEmailSet(email);
      if (name) localStorage.setItem('userName', name);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20">
      <div className="glass-card rounded-3xl p-8 text-center">
        <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Mail className="w-10 h-10 text-primary-600" />
        </div>
        
        <h2 className="text-2xl font-display font-bold text-slate-800 mb-2">
          Set Up Price Alerts
        </h2>
        <p className="text-slate-500 mb-6">
          Enter your email to receive notifications when prices drop
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your Name (optional)"
            className="input-field"
          />
          
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            className="input-field"
            required
          />
          
          <button type="submit" className="btn-primary w-full">
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500 mb-1">{label}</p>
          <p className="text-3xl font-display font-bold text-slate-800">{value}</p>
        </div>
        <div className={`p-4 rounded-xl ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

function AlertCard({ alert, onDelete, onToggle }) {
  const statusColor = alert.is_active 
    ? 'bg-green-100 text-green-700' 
    : alert.notification_sent 
    ? 'bg-purple-100 text-purple-700'
    : 'bg-slate-100 text-slate-600';

  const statusText = alert.is_active 
    ? 'Active' 
    : alert.notification_sent 
    ? 'Triggered'
    : 'Paused';

  return (
    <div className="glass-card rounded-2xl p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-display font-semibold text-slate-800">
              {alert.hotel_names.join(', ')}
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor}`}>
              {statusText}
            </span>
          </div>
          
          <div className="flex flex-wrap gap-4 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              {alert.destination}
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Target: ${alert.target_price} {alert.currency}
            </div>
            {alert.last_price_found && (
              <div className="flex items-center gap-2 text-blue-600 font-medium">
                <DollarSign className="w-4 h-4" />
                Last: ${alert.last_price_found}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggle(alert)}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            title={alert.is_active ? 'Pause alert' : 'Resume alert'}
          >
            {alert.is_active ? (
              <BellOff className="w-5 h-5 text-slate-600" />
            ) : (
              <Bell className="w-5 h-5 text-slate-600" />
            )}
          </button>
          
          <button
            onClick={() => onDelete(alert.id)}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete alert"
          >
            <Trash2 className="w-5 h-5 text-red-600" />
          </button>
        </div>
      </div>

      {alert.preferred_check_in_start && (
        <div className="flex items-center gap-2 text-sm text-slate-500 mt-2">
          <Calendar className="w-4 h-4" />
          {alert.preferred_check_in_start} to {alert.preferred_check_in_end || 'Flexible'}
        </div>
      )}

      {alert.notification_sent && alert.triggered_at && (
        <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-sm text-purple-700">
            🎉 Alert triggered on {new Date(alert.triggered_at).toLocaleDateString()}
          </p>
        </div>
      )}
    </div>
  );
}

function EmptyState({ onCreateClick }) {
  return (
    <div className="glass-card rounded-3xl p-12 text-center">
      <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <BellOff className="w-10 h-10 text-slate-400" />
      </div>
      <h3 className="text-xl font-display font-semibold text-slate-700 mb-2">
        No Price Alerts Yet
      </h3>
      <p className="text-slate-500 mb-6">
        Create your first alert and we'll notify you when prices drop
      </p>
      <button onClick={onCreateClick} className="btn-primary">
        <Plus className="w-5 h-5 inline mr-2" />
        Create Your First Alert
      </button>
    </div>
  );
}

function CreateAlertModal({ userEmail, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    email: userEmail,
    name: localStorage.getItem('userName') || '',
    hotel_names: [],
    destination: '',
    origin: '',
    target_price: '',
    currency: 'CAD',
    preferred_check_in_start: '',
    preferred_check_in_end: '',
    deal_type: 'all_inclusive',
  });

  const [hotelInput, setHotelInput] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const addHotel = () => {
    if (hotelInput.trim() && !formData.hotel_names.includes(hotelInput.trim())) {
      setFormData({
        ...formData,
        hotel_names: [...formData.hotel_names, hotelInput.trim()]
      });
      setHotelInput('');
    }
  };

  const removeHotel = (index) => {
    setFormData({
      ...formData,
      hotel_names: formData.hotel_names.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.hotel_names.length === 0) {
      alert('Please add at least one hotel');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_BASE_URL}/alerts/alerts`, {
        ...formData,
        target_price: parseFloat(formData.target_price),
      });
      onCreated();
    } catch (error) {
      console.error('Error creating alert:', error);
      alert('Failed to create alert');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="glass-card rounded-3xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-display font-bold text-slate-800">
            Create Price Alert
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Hotels */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Hotels/Resorts to Monitor *
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={hotelInput}
                onChange={(e) => setHotelInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addHotel())}
                placeholder="e.g., Riu Palace, Breathless"
                className="input-field flex-1"
              />
              <button
                type="button"
                onClick={addHotel}
                className="px-4 py-2 bg-primary-100 text-primary-700 rounded-xl hover:bg-primary-200"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
            {formData.hotel_names.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.hotel_names.map((hotel, index) => (
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

          {/* Destination */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Destination *
            </label>
            <input
              type="text"
              value={formData.destination}
              onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
              placeholder="e.g., Cancun, Punta Cana"
              className="input-field"
              required
            />
          </div>

          {/* Target Price */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Target Price *
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.target_price}
                onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                placeholder="2500"
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Currency
              </label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="input-field"
              >
                <option value="CAD">CAD</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          {/* Optional: Date Range */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Preferred Travel Dates (Optional)
            </label>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="date"
                value={formData.preferred_check_in_start}
                onChange={(e) => setFormData({ ...formData, preferred_check_in_start: e.target.value })}
                className="input-field"
              />
              <input
                type="date"
                value={formData.preferred_check_in_end}
                onChange={(e) => setFormData({ ...formData, preferred_check_in_end: e.target.value })}
                className="input-field"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
