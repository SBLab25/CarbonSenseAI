import React, { useState, useEffect } from 'react';
import { Leaf, Plus, CheckCircle2 } from 'lucide-react';
import { getUserId } from '../lib/user-session';
import { useActivities } from '../hooks/useActivities';

const factors: Record<string, Record<string, number>> = {
  transport: {
    car_petrol: 0.21,
    car_diesel: 0.17,
    car_electric: 0.05,
    bus: 0.089,
    train: 0.041,
    flight_domestic: 0.255,
    flight_international: 0.195,
    motorcycle: 0.114,
    bicycle: 0.0,
    walking: 0.0
  },
  energy: {
    electricity: 0.708,
    natural_gas: 0.202,
    lpg: 0.214
  },
  food: {
    beef: 27.0,
    lamb: 39.2,
    pork: 12.1,
    chicken: 6.9,
    fish: 6.1,
    dairy: 3.2,
    eggs: 4.8,
    vegetables: 2.0,
    fruits: 1.1,
    grains: 1.4,
    legumes: 0.9
  },
  shopping: {
    electronics: 70.0,
    clothing: 10.0,
    household_item: 15.0
  }
};

const defaultTypes: Record<string, string> = {
  transport: 'car_petrol',
  energy: 'electricity',
  food: 'beef',
  shopping: 'electronics'
};

const units: Record<string, string> = {
  transport: 'km',
  energy: 'kWh',
  food: 'kg',
  shopping: 'item'
};

export default function ActivityForm() {
  const userId = getUserId() || '';
  const { logActivity } = useActivities(userId);
  const [category, setCategory] = useState('transport');
  const [type, setType] = useState('car_petrol');
  const [amount, setAmount] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    setType(defaultTypes[category]);
    setAmount('');
  }, [category]);

  const previewCo2 = () => {
    const amt = typeof amount === 'number' ? amount : 0;
    if (amt <= 0) return 0;
    const factor = factors[category]?.[type] || 0;
    return (factor * amt);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId || amount === '' || amount <= 0) return;
    setIsSubmitting(true);
    setSuccessMessage(null);
    try {
      const co2 = previewCo2();
      await logActivity({
        user_id: userId,
        category,
        type,
        amount,
        unit: units[category],
        notes: notes.trim() || undefined
      });
      setSuccessMessage(`${co2.toFixed(1)} kg CO₂ logged successfully!`);
      setAmount('');
      setNotes('');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Error logging activity');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <Plus className="text-emerald-600" size={20} />
        <span>Quick Log Activity</span>
      </h2>

      {successMessage && (
        <div role="alert" className="p-3 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 rounded-2xl text-sm border border-emerald-100 dark:border-emerald-900/30 flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label htmlFor="category" className="text-xs font-semibold text-slate-500">Category</label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-sm"
          >
            <option value="transport">🚗 Transport</option>
            <option value="energy">⚡ Energy</option>
            <option value="food">🥗 Food</option>
            <option value="shopping">🛍️ Shopping</option>
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="type" className="text-xs font-semibold text-slate-500">Type</label>
          <select
            id="type"
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-sm"
          >
            {Object.keys(factors[category] || {}).map((k) => (
              <option key={k} value={k}>
                {k.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
        <div className="space-y-1">
          <label htmlFor="amount" className="text-xs font-semibold text-slate-500">Amount ({units[category]})</label>
          <div className="relative">
            <input
              type="number"
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value === '' ? '' : Math.max(0, parseFloat(e.target.value)))}
              placeholder={`Enter amount in ${units[category]}`}
              min="0"
              step="any"
              className="w-full pl-4 pr-12 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-sm"
              required
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              {units[category]}
            </span>
          </div>
        </div>

        {/* Live Preview */}
        <div className="p-3 bg-emerald-50/50 dark:bg-emerald-950/10 rounded-2xl border border-emerald-100/30 text-center flex items-center justify-between h-[42px] px-4">
          <span className="text-xs font-medium text-slate-500">Est. Impact:</span>
          <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400">
            {previewCo2().toFixed(2)} kg CO₂
          </span>
        </div>
      </div>

      <div className="space-y-1">
        <label htmlFor="notes" className="text-xs font-semibold text-slate-500">Notes (optional)</label>
        <textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g. commute to work, beef curry, heating"
          rows={2}
          className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting || amount === '' || amount <= 0}
        className="w-full flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 text-white font-semibold py-2.5 rounded-2xl shadow-sm transition-colors text-sm"
      >
        {isSubmitting ? 'Logging...' : 'Log Activity'}
      </button>
    </form>
  );
}
