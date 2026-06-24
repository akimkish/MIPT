import { API_CONFIG } from './config';

const TOKEN_KEY = 'gigachat_access_token';
const EXPIRES_AT_KEY = 'gigachat_token_expires_at';

const generateRqUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export const fetchAccessToken = async (): Promise<string> => {
  const authKey = import.meta.env.VITE_AUTH_KEY;

  if (!authKey) {
    throw new Error('VITE_AUTH_KEY is not defined in .env file');
  }

  const body = new URLSearchParams();
  body.append('scope', 'GIGACHAT_API_PERS');

  const response = await fetch(API_CONFIG.OAUTH_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'RqUID': generateRqUID(),
      'Authorization': `Basic ${authKey}`,
    },
    body: body.toString(),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OAuth error (${response.status}): ${errorText}`);
  }

  const data = await response.json();

  sessionStorage.setItem(TOKEN_KEY, data.access_token);
  sessionStorage.setItem(EXPIRES_AT_KEY, String(data.expires_at || Date.now() + 30 * 60 * 1000));

  return data.access_token;
};

export const getAccessToken = async (): Promise<string> => {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const expiresAt = sessionStorage.getItem(EXPIRES_AT_KEY);

  if (token && expiresAt && Number(expiresAt) > Date.now() + 60000) {
    return token;
  }

  return fetchAccessToken();
};

export const getStoredAccessToken = (): string | null => {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const expiresAt = sessionStorage.getItem(EXPIRES_AT_KEY);

  if (token && expiresAt && Number(expiresAt) > Date.now()) {
    return token;
  }

  return null;
};

export const clearAccessToken = (): void => {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(EXPIRES_AT_KEY);
};