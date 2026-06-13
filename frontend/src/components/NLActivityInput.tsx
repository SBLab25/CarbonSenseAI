import React, { useState } from 'react';
import { Sparkles, Loader2, Undo, Check, RotateCcw } from 'lucide-react';
import { getUserId } from '../lib/user-session';
import { useActivities } from '../hooks/useActivities';

export default function NLActivityInput() {
  const userId = getUserId() || '';
  const { parseNL, deleteActivity } = useActivities(userId);
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastParsed, setLastParsed] = useState<{
    activityId: number;
    co2: number;
    category: string;
    type: string;
    amount: number;
    unit: string;
    confidence: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId || !description.trim()) return;
    setIsSubmitting(true);
    setLastParsed(null);
    try {
      const res = await parseNL({
        user_id: userId,
        description: description.trim()
      });

      setLastParsed({
        activityId: res.activity_id,
        co2: res.co2_kg,
        category: res.parsed.category,
        type: res.parsed.type,
        amount: res.parsed.amount,
        unit: res.parsed.unit,
        confidence: res.parsed.confidence
      });
    } catch (err: any) {
      alert(err.message || 'Parsing failed. Please describe the activity details (e.g., transport type and distance).');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirm = () => {
    setDescription('');
    setLastParsed(null);
  };

  const handleUndo = async () => {
    if (!lastParsed) return;
    try {
      await deleteActivity(lastParsed.activityId);
      // Keep description so user can edit and re-enter
      setLastParsed(null);
    } catch (err: any) {
      alert(err.message || 'Failed to undo logged activity.');
    }
  };

  return (
    <div className="space-y-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <Sparkles className="text-emerald-600 fill-emerald-100/10 animate-pulse" size={20} />
        <span>Natural Language Logger</span>
      </h2>

      {!lastParsed ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="description" className="text-xs font-semibold text-slate-500">Describe your activity</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. 'I drove 25km in a petrol car to work' or 'We ate beef burger and drank milk'"
              rows={3}
              maxLength={250}
              className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-sm resize-none"
              required
            />
            <div className="flex justify-end text-xs text-slate-400">
              {description.length} / 250 characters
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !description.trim()}
            className="w-full flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 text-white font-semibold py-2.5 rounded-2xl shadow-sm transition-colors text-sm"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>AI Parsing...</span>
              </>
            ) : (
              <span>Parse & Log</span>
            )}
          </button>
        </form>
      ) : (
        <div className="p-5 border-2 border-emerald-500 bg-emerald-50/10 dark:bg-emerald-950/10 rounded-2xl space-y-4 animate-in zoom-in-95 duration-200">
          <div>
            <h3 className="font-bold text-sm text-slate-500 uppercase tracking-wider">AI Parsed Result</h3>
            <p className="text-base font-semibold mt-1">
              Logged as:{' '}
              <span className="text-emerald-700 dark:text-emerald-400 capitalize">
                {lastParsed.type.replace('_', ' ')}
              </span>{' '}
              ({lastParsed.amount} {lastParsed.unit})
            </p>
            <div className="flex gap-4 items-center mt-2.5">
              <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                {lastParsed.co2.toFixed(2)} kg CO₂
              </span>
              <span className={`px-2 py-0.5 text-2xs rounded-full font-bold uppercase ${
                lastParsed.confidence === 'high' 
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30' 
                  : lastParsed.confidence === 'medium'
                  ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30'
                  : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30'
              }`}>
                {lastParsed.confidence} confidence
              </span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={handleUndo}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-400 font-semibold rounded-xl hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors text-xs"
            >
              <RotateCcw size={14} />
              <span>Wrong / Re-enter</span>
            </button>
            <button
              onClick={handleConfirm}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-500 transition-colors text-xs"
            >
              <Check size={14} />
              <span>Confirm</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
