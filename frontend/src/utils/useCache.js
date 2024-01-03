import { useState, useCallback } from "react";

const useCache = () => {
  const [cache, setCache] = useState([]);

  const addToCache = useCallback((dataItem) => {
    setCache((currentCache) => [...currentCache, dataItem]);
  }, []);

  const removeFromCache = useCallback((dataItemToRemove) => {
    setCache((currentCache) => currentCache.filter((item) => item !== dataItemToRemove));
  }, []);

  const clearCache = useCallback(() => {
    setCache([]);
  }, []);

  return { cache, addToCache, removeFromCache, clearCache };
};

export default useCache;
