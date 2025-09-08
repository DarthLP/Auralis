import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, UserPreferences, UserSession, DEFAULT_PREFERENCES, MOCK_USER } from '../types/user';

interface UserContextType {
  user: User | null;
  preferences: UserPreferences;
  isSignedIn: boolean;
  signInMock: () => void;
  signOutMock: () => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  resetPreferences: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

const STORAGE_KEY = 'auralis-user-session';

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);

  // Load session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const session: UserSession = JSON.parse(stored);
        setUser(session.user);
        setPreferences(session.preferences);
      } catch (error) {
        console.error('Failed to parse stored user session:', error);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  // Save session to localStorage whenever user or preferences change
  useEffect(() => {
    if (user) {
      const session: UserSession = { user, preferences };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
  }, [user, preferences]);

  const signInMock = () => {
    setUser(MOCK_USER);
    // Keep existing preferences or use defaults
    if (!preferences) {
      setPreferences(DEFAULT_PREFERENCES);
    }
  };

  const signOutMock = () => {
    setUser(null);
    setPreferences(DEFAULT_PREFERENCES);
    localStorage.removeItem(STORAGE_KEY);
  };

  const updatePreferences = (newPreferences: Partial<UserPreferences>) => {
    setPreferences(prev => ({ ...prev, ...newPreferences }));
  };

  const resetPreferences = () => {
    setPreferences(DEFAULT_PREFERENCES);
  };

  const value: UserContextType = {
    user,
    preferences,
    isSignedIn: !!user,
    signInMock,
    signOutMock,
    updatePreferences,
    resetPreferences,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
