import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';
import { api } from '../lib/api';
import { setUserId } from '../lib/user-session';

export default function OnboardingFlow() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    country: 'India',
    city: '',
    lifestyle_type: 'Urban',
    primary_transport: 'car_petrol',
    weekly_transport_km: 50,
    diet_type: 'Mixed',
    monthly_electricity_kwh: 120,
    heating_type: 'Electric',
    monthly_target_reduction_pct: 15.0
  });

  const inputRef = useRef<HTMLInputElement | HTMLSelectElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentStep]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name.endsWith('_km') || name.endsWith('_kwh') || name.endsWith('_pct')
        ? Math.max(0, parseFloat(value) || 0)
        : value
    }));
  };

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentStep === 0 && !formData.name.trim()) {
      setError('Name is required');
      return;
    }
    if (currentStep === 1 && formData.weekly_transport_km < 0) {
      setError('Distance must be a positive number');
      return;
    }
    setError(null);
    setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      // 1. Create user profile
      const userRes = await api.users.create({
        name: formData.name,
        country: formData.country,
        city: formData.city,
        lifestyle_type: formData.lifestyle_type,
        diet_type: formData.diet_type,
        primary_transport: formData.primary_transport,
        weekly_transport_km: formData.weekly_transport_km,
        monthly_electricity_kwh: formData.monthly_electricity_kwh,
        heating_type: formData.heating_type,
        monthly_target_reduction_pct: formData.monthly_target_reduction_pct
      });

      // 2. Save session
      setUserId(userRes.user_id);

      // 3. Trigger baseline calculation
      await api.onboarding.baseline({ user_id: userRes.user_id });

      // 4. Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to complete setup. Please try again.');
      setIsLoading(false);
    }
  };

  const stepsCount = 4;

  return (
    <div className="max-w-xl mx-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-1.5 bg-slate-100 dark:bg-slate-800">
        <div 
          className="h-full bg-emerald-600 transition-all duration-300"
          style={{ width: `${((currentStep + 1) / stepsCount) * 100}%` }}
        ></div>
      </div>

      {/* Progress Dots */}
      <div className="flex justify-between items-center mb-8 mt-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Step {currentStep + 1} of {stepsCount}
        </span>
        <div className="flex gap-1.5">
          {Array.from({ length: stepsCount }).map((_, idx) => (
            <div
              key={idx}
              className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${
                idx <= currentStep ? 'bg-emerald-600' : 'bg-slate-200 dark:bg-slate-800'
              }`}
            ></div>
          ))}
        </div>
      </div>

      {error && (
        <div role="alert" className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 rounded-2xl text-sm border border-rose-100 dark:border-rose-900/30">
          {error}
        </div>
      )}

      {isLoading ? (
        <div aria-live="polite" className="flex flex-col items-center justify-center py-12 space-y-4">
          <Loader2 className="w-12 h-12 text-emerald-600 animate-spin" />
          <h3 className="text-lg font-bold">Calculating your baseline...</h3>
          <p className="text-slate-500 dark:text-slate-400 text-sm">Gemini is analyzing your carbon footprint profile.</p>
        </div>
      ) : (
        <form onSubmit={currentStep === 3 ? handleSubmit : handleNext} className="space-y-6">
          {/* STEP 0: Personal Info */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Leaf className="text-emerald-600 fill-emerald-100/10" size={24} />
                <span>Tell us about yourself</span>
              </h2>
              
              <div className="space-y-1">
                <label htmlFor="name" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Name</label>
                <input
                  ref={inputRef as React.RefObject<HTMLInputElement>}
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label htmlFor="country" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Country</label>
                  <input
                    type="text"
                    id="country"
                    name="country"
                    value={formData.country}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                  />
                </div>
                <div className="space-y-1">
                  <label htmlFor="city" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">City</label>
                  <input
                    type="text"
                    id="city"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    placeholder="Enter city"
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Lifestyle Environment</label>
                <div className="grid grid-cols-3 gap-3">
                  {['Urban', 'Suburban', 'Rural'].map(type => (
                    <label 
                      key={type}
                      className={`flex flex-col items-center justify-center p-4 rounded-2xl border cursor-pointer transition-all duration-200 text-sm font-medium ${
                        formData.lifestyle_type === type
                          ? 'border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300'
                          : 'border-slate-200 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-950/40'
                      }`}
                    >
                      <input
                        type="radio"
                        name="lifestyle_type"
                        value={type}
                        checked={formData.lifestyle_type === type}
                        onChange={handleChange}
                        className="sr-only"
                      />
                      <span>{type}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 1: Transport */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Leaf className="text-emerald-600" size={24} />
                <span>Transportation habits</span>
              </h2>

              <div className="space-y-1">
                <label htmlFor="primary_transport" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Primary Transport Type</label>
                <select
                  ref={inputRef as React.RefObject<HTMLSelectElement>}
                  id="primary_transport"
                  name="primary_transport"
                  value={formData.primary_transport}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                >
                  <option value="car_petrol">Car (Petrol)</option>
                  <option value="car_diesel">Car (Diesel)</option>
                  <option value="car_electric">Car (Electric)</option>
                  <option value="bus">Bus</option>
                  <option value="train">Train</option>
                  <option value="motorcycle">Motorcycle</option>
                  <option value="bicycle">Bicycle</option>
                  <option value="walking">Walk</option>
                </select>
              </div>

              <div className="space-y-1">
                <label htmlFor="weekly_transport_km" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Estimated weekly distance (km)</label>
                <input
                  type="number"
                  id="weekly_transport_km"
                  name="weekly_transport_km"
                  value={formData.weekly_transport_km}
                  onChange={handleChange}
                  min="0"
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                />
              </div>
            </div>
          )}

          {/* STEP 2: Food */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Leaf className="text-emerald-600" size={24} />
                <span>Dietary habits</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { id: 'Vegan', label: '🌱 Vegan', hint: 'Lowest footprint (~1.5t/yr)' },
                  { id: 'Vegetarian', label: '🥗 Vegetarian', hint: 'Low footprint (~1.7t/yr)' },
                  { id: 'Mixed', label: '🍽️ Mixed', hint: 'Average footprint (~2.5t/yr)' },
                  { id: 'High Meat', label: '🥩 High Meat', hint: 'Highest footprint (~3.3t/yr)' }
                ].map(diet => (
                  <label 
                    key={diet.id}
                    className={`flex flex-col p-4 rounded-2xl border cursor-pointer transition-all duration-200 ${
                      formData.diet_type === diet.id
                        ? 'border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/20 shadow-sm'
                        : 'border-slate-200 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-950/40'
                    }`}
                  >
                    <input
                      type="radio"
                      name="diet_type"
                      value={diet.id}
                      checked={formData.diet_type === diet.id}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <span className="font-bold text-base">{diet.label}</span>
                    <span className="text-xs text-slate-450 mt-1 leading-relaxed">{diet.hint}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: Energy */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Leaf className="text-emerald-600" size={24} />
                <span>Home energy usage</span>
              </h2>

              <div className="space-y-1">
                <label htmlFor="monthly_electricity_kwh" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Monthly electricity usage (kWh)</label>
                <input
                  ref={inputRef as React.RefObject<HTMLInputElement>}
                  type="number"
                  id="monthly_electricity_kwh"
                  name="monthly_electricity_kwh"
                  value={formData.monthly_electricity_kwh}
                  onChange={handleChange}
                  min="0"
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label htmlFor="heating_type" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Heating Type</label>
                  <select
                    id="heating_type"
                    name="heating_type"
                    value={formData.heating_type}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                  >
                    <option value="Electric">Electric</option>
                    <option value="LPG">LPG</option>
                    <option value="None">None</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                
                <div className="space-y-1">
                  <label htmlFor="monthly_target_reduction_pct" className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Monthly Reduction Goal (%)</label>
                  <input
                    type="number"
                    id="monthly_target_reduction_pct"
                    name="monthly_target_reduction_pct"
                    value={formData.monthly_target_reduction_pct}
                    onChange={handleChange}
                    min="1"
                    max="100"
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-600 transition-all text-base"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            {currentStep > 0 && (
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center justify-center gap-1.5 px-6 py-3 border border-slate-200 dark:border-slate-800 font-semibold rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-950/40 transition-colors text-sm"
              >
                <ArrowLeft size={16} />
                <span>Back</span>
              </button>
            )}
            
            <button
              type="submit"
              className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-2xl shadow-md transition-colors text-sm"
            >
              <span>{currentStep === stepsCount - 1 ? 'Complete Setup' : 'Next Step'}</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
