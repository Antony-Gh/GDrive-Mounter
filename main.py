from core.logging_config import setup_logging


def main():

    setup_logging()

    import logging
    from gui.app import App

    app = App()

    from core.logging_config import add_gui_handler
    add_gui_handler(app.write_log)

    logging.info(
        "Application started."
    )

    app.mainloop()


if __name__ == "__main__":

    main()
