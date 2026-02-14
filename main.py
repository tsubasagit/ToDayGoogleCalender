import sys
import os

# プロジェクトルートを基準にパスを設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from widget import CalendarWidget


def main():
    app = CalendarWidget()
    app.run()


if __name__ == "__main__":
    main()
