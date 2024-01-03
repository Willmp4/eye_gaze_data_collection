import { useCallback } from "react";
import sendImageToServer from "../utils/sendImageToServer";
import useCache from "../utils/useCache";

function useCacheManager() {
  const { cache, addToCache, removeFromCache, clearCache } = useCache();

  const processCache = useCallback(
    async (serverUrl) => {
      for (const item of cache) {
        try {
          await sendImageToServer([item], serverUrl);
          removeFromCache(item);
        } catch (error) {
          console.error("Error processing cache", error);
        }
      }
    },
    [cache, removeFromCache]
  );
  return { cache, addToCache, removeFromCache, clearCache, processCache };
}

export default useCacheManager;
