import requests
import re
from collections import Counter

def get_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе {url}: {e}")
        return

def count_word_frequencies(url, words):
    text = get_text(url)
    if not text:
        return {word: 0 for word in words}
    all_words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', text.lower())
    words_count = Counter(all_words)
    return {word: words_count.get(word.lower(), 0) for word in words}

def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return [word.strip() for word in file if word.strip()]
    except FileNotFoundError:
        print(f'Файл {filename} не найден')
        return
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return

def main():
    words_file = "words.txt"
    url = "https://eng.mipt.ru/why-mipt/"

    words_to_count = read_file(words_file)
    if not words_to_count:
        print("Файл пуст или возникла ошибка при чтении файла")

    frequencies = count_word_frequencies(url, words_to_count)
    
    print(frequencies)

if __name__ == "__main__":
    main()