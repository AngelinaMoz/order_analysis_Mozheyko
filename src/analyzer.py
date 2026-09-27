import csv
import logging
from pathlib import Path
from datetime import datetime

from config import (
  data_dir, logs_dir, reports_dir,
  log_filename, report_filename,
  target_status, expected_header
)

class OrderAnalyzer:

  def __init__(self):

    self.data_dir = data_dir
    self.logs_dir = logs_dir
    self.reports_dir = reports_dir
    self.logger = self._setup_logger()
    self.results = {}
    self.expected_header = expected_header
    self.target_status = target_status

  def _setup_logger(self):

    self.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = self.logs_dir / log_filename

    with open(log_file, 'w', encoding='utf-8') as f:
      f.write(f"=== Лог-файл создан: {datetime.now()} ===\n")

    logger = logging.getLogger("OrderAnalyzer")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
      logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

  def get_csv_files(self):

    if not self.data_dir.exists():
      return []
    return list(self.data_dir.glob("*.csv"))

  def read_and_validate_data(self, file_path):

    data = []
    errors = []
    path = Path(file_path)

    if not path.exists():
      msg = f"Файл не найден: {file_path}"
      print(f" {msg}")
      self.logger.error(msg)
      return data, errors

    try:
      with open(path, mode='r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        data = list(reader)

        actual_header = reader.fieldnames
        missing_columns = []
        for col in self.expected_header:
          if col not in actual_header:
            missing_columns.append(col)

        if missing_columns:
          msg = f"Отсутствуют колонки {missing_columns}"
          print(f" {msg}")
          self.logger.error(f"{path.name}: {msg}")
          return data, errors

        numeric_columns = ['order_id', 'person_id', 'total_amount']
        for index, row in enumerate(data, start=2):
          for column in numeric_columns:
            value = row.get(column, '').strip()

            if value == '':
              errors.append({
                'row_number': index,
                'column': column,
                'value': value,
                'error_type': 'пустое значение'
              })
              continue

            try:
              if column in ['order_id', 'person_id']:
                int(value)
              else:
                float(value)
            except ValueError:
              errors.append({
                'row_number': index,
                'column': column,
                'value': value,
                'error_type': 'некорректное числовое значение'
              })

      if errors:
        for error in errors:
          self.logger.error(
            f"{path.name}, строка {error['row_number']}: "
            f"{error['column']} = '{error['value']}' — {error['error_type']}"
          )

      print(f"Файл прочитан: {len(data)} строк, найдено ошибок: {len(errors)}")
      return data, errors

    except UnicodeDecodeError:
      msg = f"Ошибка кодировки: {path.name} — файл неверного формата"
      print(f" {msg}")
      self.logger.error(msg)
      return data, errors
    except Exception as e:
      msg = f"Неизвестная ошибка при чтении файла: {e}"
      print(f" {msg}")
      self.logger.error(msg)
      return data, errors

  def clean_data(self, data):

    critical_columns = ['order_id', 'person_id', 'total_amount']
    cleaned = []
    skipped_rows = []
    error_details_by_row = []

    for row in data:
      row_has_critical_error = False
      error_details = []

      for col in critical_columns:
        value = row.get(col, '').strip()

        if value == '':
          row_has_critical_error = True
          error_details.append(f"{col}: пустое значение")
          continue

        try:
          if col in ['order_id', 'person_id']:
            int(value)
          else:
            float(value)
        except (ValueError, TypeError) as e:
          row_has_critical_error = True
          error_details.append(f"{col}: {value} — {str(e)}")

      if row_has_critical_error:
        skipped_rows.append(row)
        error_details_by_row.append(error_details)
        continue

      row['order_id'] = int(row['order_id'])
      row['person_id'] = int(row['person_id'])
      row['total_amount'] = float(row['total_amount'])

      cleaned.append(row)

    if skipped_rows:
      self.logger.warning(f"Пропущено строк с критическими ошибками: {len(skipped_rows)}")
      for i, details in enumerate(error_details_by_row, 1):
        self.logger.warning(f"Строка {i}: {details}")

    return cleaned

  def filter_delivered_orders(self, data):

    delivered = []
    for row in data:
      if row.get('status', '').strip() == self.target_status:
        delivered.append(row)
    return delivered

  def calculate_metrics(self, delivered_orders):

    total = len(delivered_orders)
    print(f"Всего строк в delivered_orders: {total}")

    if total == 0:
      return {
        'total_revenue': 0.0,
        'avg_order_value': 0.0,
        'orders_count': 0
      }

    total_revenue = 0.0
    for row in delivered_orders:
      val = row.get('total_amount', 0.0)
      total_revenue += val

    avg_order_value = total_revenue / total

    print(f"Общая выручка: {total_revenue}")

    return {
      'total_revenue': total_revenue,
      'avg_order_value': avg_order_value,
      'orders_count': total
    }

  def process_file(self, file_path):

    print(f"Обработка: {file_path.name}")

    data, errors = self.read_and_validate_data(file_path)

    if errors:
      print(f"Найдено ошибок: {len(errors)}")
      for error in errors:
        print(f"- Строка {error['row_number']}: {error['column']} = '{error['value']}' ({error['error_type']})")
      print(f"{file_path.name} — файл пропущен из-за ошибок")
      return None

    if not data:
      print(f"{file_path.name} — данные не загружены")
      return None

    cleaned_data = self.clean_data(data)
    if not cleaned_data:
      print(f"{file_path.name} — после очистки нет данных")
      return None

    delivered = self.filter_delivered_orders(cleaned_data)
    metrics = self.calculate_metrics(delivered)

    print(f"{file_path.name} обработан (очищено: {len(cleaned_data)} записей)")
    print(f"Доставленных заказов: {metrics['orders_count']}")
    print(f"Общая выручка: {metrics['total_revenue']:.2f}")
    print(f"Средний чек: {metrics['avg_order_value']:.2f}")

    return metrics

  def process_all_files(self):

    csv_files = self.get_csv_files()

    if not csv_files:
      self.logger.error(f"В папке {self.data_dir} не найдено CSV-файлов.")
      print(f"Ошибка: в папке {self.data_dir} нет CSV-файлов.")
      return self.results

    print(f"Найдено CSV-файлов: {len(csv_files)}")

    for file_path in csv_files:
      metrics = self.process_file(file_path)
      self.results[file_path.name] = metrics

    return self.results

  def save_report(self):

    self.reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = self.reports_dir / report_filename

    with open(report_file, mode='w', encoding='utf-8', newline='') as f:
      writer = csv.writer(f)
      writer.writerow(['filename', 'delivered_orders', 'total_revenue', 'avg_order_value'])

      for filename, metrics in self.results.items():
        if metrics is None:
          writer.writerow([filename, 'error', 'error', 'error'])
        else:
          writer.writerow([
            filename,
            metrics['orders_count'],
            f"{metrics['total_revenue']:.2f}",
            f"{metrics['avg_order_value']:.2f}"
          ])

    print(f"\n Отчёт сохранён: {report_file}")

  def print_summary(self):

    print("ИТОГОВАЯ СВОДКА:")

    success_count = 0
    error_count = 0

    for filename, metrics in self.results.items():
      if metrics is None:
        print(f"{filename} — ошибка обработки")
        error_count += 1
      else:
        print(f"{filename}")
        print(f"Доставленных: {metrics['orders_count']}")
        print(f"Выручка: {metrics['total_revenue']:.2f}")
        print(f"Средний чек: {metrics['avg_order_value']:.2f}")
        success_count += 1

    print()
    print(f"Успешно обработано файлов: {success_count}")
    print(f"Файлов с ошибками: {error_count}")