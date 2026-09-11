import { useState } from 'react';
import type { FormEvent } from 'react';
import { useAdminLogin } from '../hooks/useAdminLogin';
import styles from './LoginPage.module.css';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

/**
 * Форма входа администратора.
 *
 * После серии неудачных попыток вход временно блокируется на бэкенде
 * (`failed_login_attempts`/`locked_until`, см. project_context) —
 * конкретное сообщение (401/403/423, см. `auth.py`) приходит в теле
 * ответа и показывается как есть через `ApiError`, без собственной
 * интерпретации на фронте.
 *
 * @param onLoginSuccess - Вызывается после успешного логина. Токен уже
 *   сохранён в `authStore` внутри `useAdminLogin` — здесь только навигация.
 */
export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const login = useAdminLogin();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    login.mutate({ email, password }, { onSuccess: onLoginSuccess });
  }

  return (
    <div className={styles.page}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <h1 className={styles.heading}>Вход в админку</h1>

        <label className={styles.field}>
          Email
          <input
            type="email"
            required
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>

        <label className={styles.field}>
          Пароль
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {login.isError && <p className={styles.error}>{login.error.message}</p>}

        <button type="submit" className={styles.submit} disabled={login.isPending}>
          {login.isPending ? 'Входим…' : 'Войти'}
        </button>
      </form>
    </div>
  );
}
