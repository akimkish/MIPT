/**
 * Приближённо переводит цветовую температуру (в Кельвинах) в RGB —
 * реализация аппроксимации Таннера Хелланда излучения чёрного тела,
 * стандартный приём в графике и фотографии.
 *
 * Это не декоративный градиент: цвет свотча несёт реальную информацию
 * о товаре (`color_temperature_k`) — тёплый жёлтый около 2700К (как
 * лампа накаливания), нейтрально-белый около 4000К, холодный голубоватый
 * к 6500К+ (дневной свет) — ровно как отличается свет разных лампочек
 * в реальности.
 *
 * @param kelvin - Цветовая температура, 1000..10000 (диапазон CHECK
 *   для `products.color_temperature_k` в БД).
 * @returns CSS-цвет вида "rgb(r, g, b)".
 */
export function kelvinToRgb(kelvin: number): string {
  const temp = Math.min(400, Math.max(10, kelvin / 100));

  let r: number;
  let g: number;
  let b: number;

  if (temp <= 66) {
    r = 255;
    g = 99.4708025861 * Math.log(temp) - 161.1195681661;
  } else {
    r = 329.698727446 * (temp - 60) ** -0.1332047592;
    g = 288.1221695283 * (temp - 60) ** -0.0755148492;
  }

  if (temp >= 66) {
    b = 255;
  } else if (temp <= 19) {
    b = 0;
  } else {
    b = 138.5177312231 * Math.log(temp - 10) - 305.0447927307;
  }

  const clamp = (value: number) => Math.round(Math.min(255, Math.max(0, value)));

  return `rgb(${clamp(r)}, ${clamp(g)}, ${clamp(b)})`;
}
