import { useUser } from '../contexts/UserContext';
import { formatDate, formatDateTime } from '../lib/date';

/**
 * Hook that provides date formatting functions using the user's preferences
 */
export function useDateFormat() {
  const { preferences } = useUser();

  const formatDateWithPreferences = (date: string | Date) => {
    return formatDate(date, {
      timezone: preferences.timezone,
      format: preferences.dateFormat,
    });
  };

  const formatDateTimeWithPreferences = (date: string | Date) => {
    return formatDateTime(date, {
      timezone: preferences.timezone,
      format: preferences.dateFormat,
    });
  };

  return {
    formatDate: formatDateWithPreferences,
    formatDateTime: formatDateTimeWithPreferences,
    preferences,
  };
}
