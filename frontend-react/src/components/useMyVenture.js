import { useCallback, useEffect, useState } from 'react';
import { ApiError, friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';

// Carga "mi emprendimiento". venture: undefined = cargando, null = aun no existe.
export function useMyVenture() {
  const [venture, setVenture] = useState(undefined);
  const [error, setError] = useState('');
  const reload = useCallback(async () => {
    try {
      setVenture(await venturesApi.mine());
      setError('');
    } catch (e) {
      setVenture(null);
      if (!(e instanceof ApiError && e.status === 404)) setError(friendlyMessage(e));
    }
  }, []);
  useEffect(() => {
    reload();
  }, [reload]);
  return { venture, setVenture, error, reload };
}
