import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from analyzer import OrderAnalyzer


def main():

  print("АНАЛИЗ ЗАКАЗОВ СО СТАТУСОМ 'ДОСТАВЛЕН'")

  analyzer = OrderAnalyzer()
  analyzer.process_all_files()
  analyzer.print_summary()
  analyzer.save_report()

  for handler in analyzer.logger.handlers:
    handler.flush()


if __name__ == "__main__":
  main()
