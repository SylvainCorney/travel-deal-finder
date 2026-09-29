import { useState } from 'react';
import { Sparkles, Send, AlertTriangle, Info, Search, HelpCircle } from 'lucide-react';
import { nlSearchAPI } from '../services/api';

const EXAMPLES = [
  'Adults-only 4.5★ all-inclusive in Punta Cana, direct flight, 7 nights in February, under $3,000 for two',
  'Tout inclus à Cancun, 2 semaines en avril, départ de Burlington ou Montréal',
];

const TRIP_LABELS = {
  all_inclusive: 'All-inclusive',
  flight_hotel: 'Flight + hotel',
  flight_only: 'Flight only',
  hotel_only: 'Hotel only',
};

const fmtDate = (iso) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' });

function criteriaChips(r) {
  const chips = [];
  if (r.trip_type) chips.push(TRIP_LABELS[r.trip_type]);
  const kids = r.children_ages?.length ? ` + ${r.children_ages.length} child (${r.children_ages.join(', ')})` : '';
  chips.push(`${r.adults} adult${r.adults > 1 ? 's' : ''}${kids}`);
  if (r.destinations?.length) chips.push(`To ${r.destinations.join(' / ')}`);
  chips.push(r.origin_airports?.length ? `From ${r.origin_airports.join(' / ')}` : `From any airport ≤ ${r.max_drive_hours} h`);
  if (r.depart_earliest) {
    chips.push(r.depart_earliest === r.depart_latest
      ? `Leave ${fmtDate(r.depart_earliest)}`
      : `Leave ${fmtDate(r.depart_earliest)} – ${fmtDate(r.depart_latest)}`);
  }
  if (r.nights_min) chips.push(r.nights_min === r.nights_max ? `${r.nights_min} nights` : `${r.nights_min}–${r.nights_max} nights`);
  if (r.min_stars) chips.push(`${r.min_stars}★+`);
  if (r.direct_flight_only) chips.push('Direct only');
  if (r.adults_only_resort) chips.push('Adults only');
  if (r.max_budget_total_cad) chips.push(`≤ $${r.max_budget_total_cad.toLocaleString('en-CA')} total`);
  r.preferences?.forEach((p) => chips.push(`“${p}”`));
  return chips;
}

export default function NaturalSearch({ onSearch, isLoading }) {
  const [text, setText] = useState('');
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState(null);

  const understand = async (query) => {
    if (!query || query.trim().length < 3) return;
    setParsing(true);
    setError(null);
    try {
      setResult(await nlSearchAPI.parse(query.trim()));
    } catch (err) {
      setResult(null);
      setError(err.response?.data?.detail || err.message || 'Could not understand the request');
    } finally {
      setParsing(false);
    }
  };

  const submitAnswer = (e) => {
    e.preventDefault();
    if (!answer.trim()) return;
    const combined = `${text.trim().replace(/[.\s]+$/, '')}. ${answer.trim()}`;
    setText(combined);
    setAnswer('');
    understand(combined);
  };

  const busy = parsing || isLoading;

  return (
    <div className="glass-card rounded-3xl p-8 animate-slide-up">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl shadow-lg">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-display font-bold text-slate-800">Describe your trip</h2>
          <p className="text-sm text-slate-500">In English or French — the local AI turns it into search criteria</p>
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); understand(text); }} className="space-y-3">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) understand(text); }}
          rows={3}
          placeholder="e.g. Adults-only all-inclusive, direct flight, a week in February, under $3,000 for two"
          className="input-field resize-none"
        />
        <div className="flex flex-wrap items-center gap-2">
          <button type="submit" disabled={busy || text.trim().length < 3}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            {parsing ? (
              <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />Understanding…</>
            ) : (
              <><Send className="w-5 h-5" />Understand</>
            )}
          </button>
          <span className="text-xs text-slate-400">⌘ + Enter</span>
          <div className="flex flex-wrap gap-2 ml-auto">
            {EXAMPLES.map((ex, i) => (
              <button key={i} type="button" onClick={() => setText(ex)}
                className="text-xs px-3 py-1 rounded-full bg-white/70 border border-slate-200 text-slate-600 hover:bg-white">
                Example {i + 1}
              </button>
            ))}
          </div>
        </div>
      </form>

      {error && (
        <div className="mt-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0" /><span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="flex flex-wrap gap-2">
            {criteriaChips(result.request).map((chip, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full bg-primary-50 border border-primary-100 text-sm text-primary-800">
                {chip}
              </span>
            ))}
          </div>

          {result.question && (
            <form onSubmit={submitAnswer} className="p-4 rounded-xl bg-blue-50 border border-blue-200 space-y-3">
              <p className="flex gap-2 text-blue-900 font-medium">
                <HelpCircle className="w-5 h-5 shrink-0" />{result.question}
              </p>
              <div className="flex gap-2">
                <input value={answer} onChange={(e) => setAnswer(e.target.value)} className="input-field"
                  placeholder={result.request.language === 'fr' ? 'Votre réponse…' : 'Your answer…'} />
                <button type="submit" disabled={busy || !answer.trim()} className="btn-primary disabled:opacity-50">
                  {result.request.language === 'fr' ? 'Répondre' : 'Reply'}
                </button>
              </div>
            </form>
          )}

          {result.warnings?.length > 0 && (
            <p className="text-xs text-slate-500 flex gap-1.5">
              <Info className="w-4 h-4 shrink-0" />{result.warnings.join(' · ')}
            </p>
          )}

          {result.legacy_note && (
            <p className="text-sm p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 flex gap-2">
              <Info className="w-5 h-5 shrink-0" />{result.legacy_note}
            </p>
          )}

          {result.legacy_search && (
            <button type="button" onClick={() => onSearch(result.legacy_search)} disabled={busy}
              className="btn-primary w-full disabled:opacity-50 flex items-center justify-center gap-2">
              <Search className="w-5 h-5" />
              Search {result.legacy_search.location}: {fmtDate(result.legacy_search.check_in_date)} → {fmtDate(result.legacy_search.check_out_date)}
            </button>
          )}

          <p className="text-xs text-slate-400 text-right">
            Understood in {result.seconds}s{result.attempts > 1 ? ` (${result.attempts} tries)` : ''}
          </p>
        </div>
      )}
    </div>
  );
}
