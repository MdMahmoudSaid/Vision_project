import '@testing-library/jest-dom';
import { server } from './msw/server';

// Node's own experimental localStorage global can shadow jsdom's working
// implementation with a non-functional stub (getItem missing), depending on
// Node version. Force a deterministic in-memory implementation for tests.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();
  get length() { return this.store.size; }
  clear() { this.store.clear(); }
  getItem(key: string) { return this.store.has(key) ? this.store.get(key)! : null; }
  key(index: number) { return Array.from(this.store.keys())[index] ?? null; }
  removeItem(key: string) { this.store.delete(key); }
  setItem(key: string, value: string) { this.store.set(key, String(value)); }
}

if (typeof window.localStorage?.getItem !== 'function') {
  Object.defineProperty(window, 'localStorage', { value: new MemoryStorage(), configurable: true });
}
if (typeof window.sessionStorage?.getItem !== 'function') {
  Object.defineProperty(window, 'sessionStorage', { value: new MemoryStorage(), configurable: true });
}

// jsdom does not implement matchMedia; ThemeContext uses it to detect the
// system color-scheme preference on first load.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as unknown as MediaQueryList;
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
