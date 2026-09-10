import { useState } from 'react';
import type { FormEvent } from 'react';
import { useCreateReview } from '../hooks/useCreateReview';
import styles from './ReviewForm.module.css';

interface ReviewFormProps {
  productId: string;
}

/**
 * Форма отправки отзыва на товар.
 *
 * Без аутентификации — только имя и email для связи (аккаунтов
 * покупателей в проекте нет, см. project_context). Отзыв уходит на
 * модерацию (`is_approved=false` по умолчанию) и не появляется в списке
 * сразу — форма явно сообщает об этом после отправки, чтобы не выглядело
 * так, будто отзыв потерялся.
 *
 * @param productId - Идентификатор товара, к которому относится отзыв.
 */
export function ReviewForm({ productId }: ReviewFormProps) {
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [description, setDescription] = useState('');
  const [rating, setRating] = useState(5);

  const createReview = useCreateReview(productId);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createReview.mutate(
      { product_id: productId, user_name: userName, user_email: userEmail, description, rating },
      {
        onSuccess: () => {
          setUserName('');
          setUserEmail('');
          setDescription('');
          setRating(5);
        },
      },
    );
  }

  if (createReview.isSuccess) {
    return (
      <p className={styles.success}>
        Спасибо! Отзыв отправлен и появится на странице после проверки модератором.
      </p>
    );
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <h3 className={styles.heading}>Оставить отзыв</h3>

      <label className={styles.field}>
        Имя
        <input type="text" required maxLength={100} value={userName} onChange={(e) => setUserName(e.target.value)} />
      </label>

      <label className={styles.field}>
        Email
        <input
          type="email"
          required
          maxLength={255}
          value={userEmail}
          onChange={(e) => setUserEmail(e.target.value)}
        />
      </label>

      <label className={styles.field}>
        Оценка
        <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {n} {n === 1 ? 'звезда' : n < 5 ? 'звезды' : 'звёзд'}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        Отзыв
        <textarea rows={4} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>

      {createReview.isError && <p className={styles.error}>Не получилось отправить отзыв: {createReview.error.message}</p>}

      <button type="submit" className={styles.submit} disabled={createReview.isPending}>
        {createReview.isPending ? 'Отправляем…' : 'Отправить отзыв'}
      </button>
    </form>
  );
}
