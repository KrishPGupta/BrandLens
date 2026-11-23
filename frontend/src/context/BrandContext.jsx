import { createContext, useContext, useEffect, useState } from "react";
import { API_URL } from "../config/site";

const BrandContext = createContext({ brands: [], brand: null, setBrand: () => {}, offline: false });
export const useBrand = () => useContext(BrandContext);

const KEY = "brandlens.brand";
const read = () => {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
};

export function BrandProvider({ children }) {
  const [brands, setBrands] = useState([]);
  const [brand, setBrandState] = useState(read);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/api/brands`, { signal: controller.signal })
      .then((res) => res.json())
      .then((d) => {
        setOffline(false);
        setBrands(d.brands);
        setBrandState((cur) => (cur && d.brands.includes(cur) ? cur : d.brands[0]));
      })
      .catch((err) => {
        if (err.name !== "AbortError") setOffline(true);
      });
    return () => controller.abort();
  }, []);

  const setBrand = (b) => {
    setBrandState(b);
    try {
      localStorage.setItem(KEY, b);
    } catch {
      /* private mode: selection just won't persist */
    }
  };

  return <BrandContext.Provider value={{ brands, brand, setBrand, offline }}>{children}</BrandContext.Provider>;
}
