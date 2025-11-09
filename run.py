"""
Скрипт для запуска FastAPI приложения.
Использование: python run.py
"""
import uvicorn

if __name__ == "__main__":
    print("Запуск FastAPI приложения...")
    print("API документация будет доступна по адресу: http://127.0.0.1:8000/docs")
    print("Нажмите Ctrl+C для остановки")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

