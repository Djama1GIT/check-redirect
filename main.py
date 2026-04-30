import requests
import sys
import time
from urllib.parse import urlparse

def normalize_url(raw_url):
    """
    Приводит сырой ввод к стандартному виду для проверки HTTP -> HTTPS.
    """
    raw_url = raw_url.strip()
    parsed = urlparse(raw_url)
    
    # Если схема не указана, добавляем http://
    if not parsed.scheme:
        return f"http://{raw_url}"
    
    # Если схема уже есть, возвращаем как есть (но для теста будем использовать http:// вариант)
    return raw_url

def check_http_to_https_redirect(domain_input):
    """
    Проверяет, перенаправляет ли HTTP-версия сайта на HTTPS.
    Возвращает (статус, сообщение, итоговый URL)
    """
    # Приводим к стандартному виду
    normalized = normalize_url(domain_input)
    parsed = urlparse(normalized)
    
    # Формируем HTTP URL для проверки
    http_url = f"http://{parsed.netloc or parsed.path}"
    
    try:
        # Отключаем проверку SSL-сертификата и следуем редиректам
        response = requests.get(http_url, timeout=10, allow_redirects=True, verify=False)
        
        # Получаем финальный URL после всех редиректов
        final_url = response.url
        
        # Проверяем, ведёт ли финальный URL на HTTPS
        if final_url.startswith("https://"):
            return (True, f"✅ РЕДИРЕКТ: {http_url} -> {final_url}", final_url)
        else:
            return (False, f"❌ НЕТ РЕДИРЕКТА НА HTTPS: {http_url} -> {final_url}", final_url)
            
    except requests.exceptions.Timeout:
        return (False, f"⏱️ ТАЙМАУТ: {http_url} не отвечает за 10 секунд", None)
    except requests.exceptions.ConnectionError:
        return (False, f"🔌 ОШИБКА СОЕДИНЕНИЯ: {http_url} недоступен", None)
    except Exception as e:
        return (False, f"⚠️ ОШИБКА: {http_url} -> {str(e)}", None)

def main():
    print("=" * 70)
    print("ПРОВЕРКА ПЕРЕАДРЕСАЦИИ HTTP -> HTTPS")
    print("=" * 70)
    print("Вводите сайты по одному на каждой новой строке.")
    print("Для завершения ввода введите слово 'конец' (без кавычек)")
    print()
    print("Примеры ввода:")
    print("  google.ru")
    print("  http://yandex.ru")
    print("  https://www.github.com")
    print("  example.com")
    print()
    print("-" * 70)
    
    # Список для хранения введённых сайтов
    domains = []
    
    # Бесконечный цикл для построчного ввода
    line_number = 1
    while True:
        user_input = input(f"Сайт #{line_number}: ").strip()
        
        # Проверка на стоп-слово
        if user_input.lower() == "конец":
            break
        
        # Пропускаем пустые строки
        if not user_input:
            print("  ⚠️ Пустая строка игнорируется. Введите сайт или 'конец'")
            continue
        
        # Добавляем сайт в список
        domains.append(user_input)
        line_number += 1
    
    # Проверяем, есть ли вообще сайты для проверки
    if not domains:
        print("\n❌ Ошибка: не введено ни одного сайта для проверки.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"НАЧАЛО ПРОВЕРКИ (всего сайтов: {len(domains)})")
    print("=" * 70)
    
    results = []
    redirect_count = 0
    total = len(domains)
    
    for idx, domain in enumerate(domains, 1):
        print(f"\n[{idx}/{total}] Проверка: {domain}")
        status, message, final_url = check_http_to_https_redirect(domain)
        print(f"  {message}")
        
        if status:
            redirect_count += 1
        
        results.append({
            "original": domain,
            "has_redirect": status,
            "message": message,
            "final_url": final_url
        })
        
        time.sleep(0.5)
    
    # Вывод итоговой статистики
    print("\n" + "=" * 70)
    print("СТАТИСТИКА:")
    print("=" * 70)
    print(f"Всего сайтов: {total}")
    print(f"✅ Есть редирект HTTP -> HTTPS: {redirect_count}")
    print(f"❌ Нет редиректа / ошибка: {total - redirect_count}")
    
    if redirect_count == total:
        print("\n🎉 Отлично! Все сайты правильно перенаправляют с HTTP на HTTPS.")
    elif redirect_count > 0:
        print("\n⚠️ Некоторые сайты не перенаправляют на HTTPS. Рекомендуется исправить.")
    else:
        print("\n❌ Ни один сайт не перенаправляет с HTTP на HTTPS!")
    
    # Дополнительный вывод: список сайтов без редиректа
    failed_sites = [r["original"] for r in results if not r["has_redirect"]]

    if failed_sites:
        print("\n" + "-" * 70)
        print("САЙТЫ БЕЗ РЕДИРЕКТА НА HTTPS:")
        print("-" * 70)
        for result in results:
            if not result["has_redirect"]:
                print(f"  • {result['original']}")
                print(f"    {result['message']}")

    print("\n" + "=" * 70)

    if not failed_sites:
        return
    
    while True:
        command = input("\nВведите команду (re / stop): ").strip().lower()

        if command == "stop":
            print("⛔ Завершение программы.")
            break

        elif command == "re":
            if not failed_sites:
                print("✅ Нет сайтов для повторной проверки.")
                continue

            print("\n🔁 Повторная проверка сайтов без редиректа...")
            new_failed = []

            for idx, domain in enumerate(failed_sites, 1):
                print(f"\n[{idx}/{len(failed_sites)}] Проверка: {domain}")
                status, message, final_url = check_http_to_https_redirect(domain)
                print(f"  {message}")

                if not status:
                    new_failed.append(domain)

                time.sleep(0.5)

            failed_sites = new_failed

            if not failed_sites:
                print("\n🎉 Все сайты теперь имеют редирект на HTTPS!")
                return
            else:
                print("\n⚠️ Всё ещё без редиректа:")
                for site in failed_sites:
                    print(f"  • {site}")

        else:
            print("❓ Неизвестная команда. Используйте 're' или 'stop'.")

if __name__ == "__main__":
    # Отключаем предупреждения о небезопасных HTTPS-запросах (из-за verify=False)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Проверка прервана пользователем.")
        sys.exit(0)