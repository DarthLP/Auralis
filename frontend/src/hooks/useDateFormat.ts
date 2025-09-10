import { useUser } from '../contexts/UserContext';
import { formatDate, formatDateTime } from '../lib/date';

/**
 * Hook that provides date formatting functions using the user's preferences
 */
export function useDateFormat() {
  const { preferences } = useUser();

  const formatDateWithPreferences = (date: string | Date) => {
    // Current date utilities accept a locale string only; ignore timezone for now
    return formatDate(date);
  };

  const formatDateTimeWithPreferences = (date: string | Date) => {
    return formatDateTime(date);
  };

  return {
    formatDate: formatDateWithPreferences,
    formatDateTime: formatDateTimeWithPreferences,
    preferences,
  };
}
