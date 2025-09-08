import { useState } from 'react';
import { useUser } from '../contexts/UserContext';
import { formatDate, getCommonTimezones, getBrowserTimezone } from '../lib/date';
import { generateInitials, generateAvatarColor } from '../lib/avatar';
import { UserPreferences } from '../types/user';

export default function Settings() {
  const { user, preferences, updatePreferences, resetPreferences, signOutMock, signInMock, isSignedIn } = useUser();
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const timezones = getCommonTimezones();
  const browserTimezone = getBrowserTimezone();

  const handlePreferenceChange = (key: keyof UserPreferences, value: any) => {
    updatePreferences({ [key]: value });
  };

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate save delay
    await new Promise(resolve => setTimeout(resolve, 500));
    setIsSaving(false);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all preferences to defaults?')) {
      resetPreferences();
    }
  };

  if (!isSignedIn) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Not signed in (mock)</h2>
          <p className="text-gray-600 mb-6">Sign in to access your settings and preferences.</p>
          <button
            onClick={signInMock}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Sign In (Mock)
          </button>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const initials = generateInitials(user.name);
  const avatarColor = generateAvatarColor(user.name);

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your profile and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Profile Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile</h2>
          
          <div className="space-y-6">
            {/* Avatar */}
            <div className="flex items-center space-x-4">
              <div className={`w-16 h-16 ${avatarColor} rounded-full flex items-center justify-center text-white font-semibold text-lg`}>
                {initials}
              </div>
              <div>
                <p className="text-sm text-gray-500">Avatar</p>
                <p className="text-sm text-gray-600">Generated from your name</p>
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={user.name}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={user.email}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>

            {/* Joined Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Joined</label>
              <input
                type="text"
                value={formatDate(user.joinedAt, { timezone: preferences.timezone, format: preferences.dateFormat })}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>

            {/* User ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
              <input
                type="text"
                value={user.id}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Preferences Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Preferences</h2>
          
          <div className="space-y-6">
            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
              <select
                value={preferences.timezone}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={browserTimezone}>
                  Browser timezone ({browserTimezone})
                </option>
                {timezones.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Format</label>
              <select
                value={preferences.dateFormat}
                onChange={(e) => handlePreferenceChange('dateFormat', e.target.value as 'MMM d, yyyy' | 'yyyy-MM-dd')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="MMM d, yyyy">MMM d, yyyy (e.g., Jan 15, 2024)</option>
                <option value="yyyy-MM-dd">yyyy-MM-dd (e.g., 2024-01-15)</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                Preview: {formatDate(new Date(), { timezone: preferences.timezone, format: preferences.dateFormat })}
              </p>
            </div>

            {/* Experimental Features */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.experimentalFeatures}
                  onChange={(e) => handlePreferenceChange('experimentalFeatures', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">Experimental features</span>
              </label>
              <p className="text-sm text-gray-500 mt-1">
                Enable beta features and experimental functionality
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions Section */}
      <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Actions</h2>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          >
            {isSaving ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>

          <button
            onClick={handleReset}
            className="bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors"
          >
            Reset to Defaults
          </button>

          <div className="flex-1"></div>

          <button
            onClick={signOutMock}
            className="text-red-600 hover:text-red-700 text-sm underline"
          >
            Sign out
          </button>
        </div>

        {showSuccess && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">Settings saved successfully!</p>
          </div>
        )}
      </div>
    </div>
  );
}
