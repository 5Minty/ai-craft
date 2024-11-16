from bot import BuilderBot

def main():

    # Initialize and run the bot
    bot = BuilderBot()
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()