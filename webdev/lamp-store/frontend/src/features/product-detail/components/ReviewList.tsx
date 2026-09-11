import type { Review } from '../../../types/review';
import styles from './ReviewList.module.css';

interface ReviewListProps {
  reviews: Review[];
}

/**
 * Список опубликованных отзывов товара.
 *
 * Модерация (одобрение/удаление) сюда не входит — она делается в
 * админке, эта версия компонента только читает и показывает.
 *
 * @param reviews - Опубликованные отзывы (`is_approved === true`).
 */
export function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return <p className={styles.empty}>Отзывов пока нет — будьте первым.</p>;
  }

  return (
    <ul className={styles.list}>
      {reviews.map((review) => (
        <li key={review.review_id} className={styles.item}>
          <div className={styles.header}>
            <span className={styles.author}>{review.user_name}</span>
            <span className={styles.rating} aria-label={`Оценка ${review.rating} из 5`}>
              {'★'.repeat(review.rating)}
              {'☆'.repeat(5 - review.rating)}
            </span>
          </div>
          {review.description && <p className={styles.text}>{review.description}</p>}
        </li>
      ))}
    </ul>
  );
}
