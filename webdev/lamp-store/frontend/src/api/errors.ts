/** Форма тела ошибки, которую отдаёт FastAPI (422 — список, остальное — строка/объект). */
export interface ApiErrorBody {
  detail?: string | { msg: string; type: string }[] | { code: string; message: string; details: unknown };
}

/**
 * Единая ошибка HTTP-запроса к любому из трёх бэкенд-сервисов.
 *
 * Учитывает две разные формы `detail`, реально встречающиеся в бэкенде:
 * стандартную FastAPI-валидацию (список `{msg, type}`) и доменные ошибки
 * orders_service вида `{code, message, details}` (см. `create_order`
 * в orders.py: 409 при дубле/нехватке остатка, 503 при недоступности
 * products_service).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | undefined;

  constructor(status: number, body: ApiErrorBody | undefined, message?: string) {
    super(message ?? ApiError.extractMessage(body) ?? `Запрос завершился со статусом ${status}`);
    this.status = status;
    this.body = body;
    this.name = 'ApiError';
  }

  /**
   * Достаёт человекочитаемое сообщение из тела ошибки в любой из известных форм.
   *
   * @param body - Тело ответа, распарсенное как JSON, либо undefined.
   * @returns Сообщение об ошибке либо undefined.
   */
  private static extractMessage(body: ApiErrorBody | undefined): string | undefined {
    if (!body?.detail) return undefined;
    if (typeof body.detail === 'string') return body.detail;
    if ('message' in body.detail) return body.detail.message;
    return body.detail.map((e) => e.msg).join('; ');
  }
}
