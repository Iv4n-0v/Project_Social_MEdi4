import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { venturesApi } from '../api/ventures';
import { useAuth } from './AuthContext';

const FavoritesContext = createContext(null);

export function FavoritesProvider({ children }) {
  const { account } = useAuth();
  const [ids, setIds] = useState([]);
  const accountId = account ? account.id : null;

  useEffect(() => {
    let alive = true;
    if (!accountId) {
      setIds([]);
      return undefined;
    }
    venturesApi
      .favoriteIds()
      .then((r) => alive && setIds(r.ids))
      .catch(() => {}); // si falla, simplemente no se marcan
    return () => {
      alive = false;
    };
  }, [accountId]);

  const toggle = useCallback(
    async (id) => {
      if (ids.includes(id)) {
        await venturesApi.removeFavorite(id);
        setIds((cur) => cur.filter((x) => x !== id));
      } else {
        await venturesApi.addFavorite(id);
        setIds((cur) => [id, ...cur]);
      }
    },
    [ids]
  );

  const value = useMemo(() => ({ ids, isFavorite: (id) => ids.includes(id), toggle }), [ids, toggle]);
  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext);
  if (!ctx) throw new Error('useFavorites debe usarse dentro de FavoritesProvider');
  return ctx;
}
