from pathlib import Path

# Пути к папкам
base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"
logs_dir = base_dir / "logs"
reports_dir = base_dir / "reports"

# Имена файлов
log_filename = "errors.log"
report_filename = "summary_report.csv"

# Статус для фильтрации
target_status = "Delivered"

# Ожидаемые заголовки
expected_header = [
  'order_id', 'person_id', 'order_date', 'status',
  'total_amount', 'currency', 'payment_method',
  'shipping_method', 'notes'
]