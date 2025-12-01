import uvicorn


def main() -> None:
    # backend ディレクトリ内で実行することを想定し、モジュール指定を app.* に統一
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
