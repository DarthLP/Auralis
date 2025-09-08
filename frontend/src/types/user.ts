export interface User {
  id: string;
  name: string;
  email: string;
  joinedAt: string; // ISO date string
  avatar?: string; // URL to avatar image
}

export interface UserPreferences {
  timezone: string;
  dateFormat: 'MMM d, yyyy' | 'yyyy-MM-dd';
  experimentalFeatures: boolean;
}

export interface UserSession {
  user: User;
  preferences: UserPreferences;
}

export const DEFAULT_PREFERENCES: UserPreferences = {
  timezone: 'Europe/Berlin',
  dateFormat: 'MMM d, yyyy',
  experimentalFeatures: false,
};

export const MOCK_USER: User = {
  id: 'mock-user-1',
  name: 'Alex Johnson',
  email: 'alex.johnson@example.com',
  joinedAt: '2024-01-15T10:30:00Z',
};
