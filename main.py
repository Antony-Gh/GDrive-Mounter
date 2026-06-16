import sys

from core.logging_config import setup_logging


def main():

    setup_logging()

    from gui.app import App

    app = App()

    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        app.shutdown()


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        pass

    sys.exit(0)
