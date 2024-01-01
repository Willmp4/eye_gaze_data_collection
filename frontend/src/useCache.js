import { useState, useCallback } from "react";

const useCache = () => {
  const [cache, setCache] = useState([]);

  const addToCache = useCallback((dataItem) => {
    setCache((currentCache) => [...currentCache, dataItem]);
  }, []);

  const clearCache = useCallback(() => {
    setCache([]);
  }, []);

  return { cache, addToCache, clearCache };
};

export default useCache;
