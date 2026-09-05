from random import random, randint
import asyncio
import datetime
import logging

import nodriver as uc

# ── Configuration ────────────────────────────────────────────────────────────
BROWSER_PATH = (
    r"C:\Users\Administrator\Desktop\LinkedIn-Follower-Bot\Chrome\chrome.exe"
)
PROFILE_PATH = (
    r"C:\Users\Administrator\Desktop\LinkedIn-Follower-Bot\Users\LinkedIn\\"
)
LOG_FILE = "AccountLog.txt"
LOGGED_IN = True

MAX_WEEKLY_ACCOUNTS = 100
MAX_DAILY_CONNECTS = 25
LOOKBACK_DAYS = 7

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Log File Helpers ─────────────────────────────────────────────────────────
def parse_log_file() -> list[dict]:
    """
    Parse AccountLog.txt and return a list of records.
    Each record: {"count": int, "date": datetime}
    Silently skips malformed lines.
    """
    records = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # Expected format: "Accounts ran: 10 on 2024-05-01"
                    accounts_part, date_part = line.split(" on ")
                    count = int(accounts_part.split(": ")[1])
                    date = datetime.datetime.strptime(date_part, "%Y-%m-%d")
                    records.append({"count": count, "date": date})
                except (ValueError, IndexError):
                    log.warning(f"Skipping malformed log line: {line!r}")
    except FileNotFoundError:
        log.info(f"{LOG_FILE} not found — starting fresh.")
    return records


def get_weekly_total(records: list[dict]) -> int:
    """Sum account counts from the past LOOKBACK_DAYS days."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=LOOKBACK_DAYS)
    return sum(r["count"] for r in records if r["date"] >= cutoff)


def already_ran_today(records: list[dict], today: str) -> bool:
    """Return True if there is already an entry for today."""
    return any(
        r["date"].strftime("%Y-%m-%d") == today for r in records
    )


def append_log(count: int, date: str) -> None:
    """Append a run record to the log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"Accounts ran: {count} on {date}\n")


# ── Skip Logic ───────────────────────────────────────────────────────────────
def should_skip(records: list[dict], today: str) -> bool:
    """
    Returns True (and logs the reason) if the bot should not run.
    """
    weekly_total = get_weekly_total(records)

    if weekly_total >= MAX_WEEKLY_ACCOUNTS:
        log.info(
            f"Weekly limit reached ({weekly_total}/{MAX_WEEKLY_ACCOUNTS}). Skipping."
        )
        return True

    if already_ran_today(records, today):
        log.info(f"Already ran today ({today}). Skipping.")
        return True

    return False


# ── Browser Helpers ──────────────────────────────────────────────────────────
async def random_wait(min_s: float = 1.0, max_s: float = 6.0) -> None:
    """Non-blocking sleep for a random duration."""
    await asyncio.sleep(min_s + (max_s - min_s) * random())


async def get_load_more_button(tab):
    """
    Find the 'Load More' <span> button.
    Returns the element or None if not found.
    """
    try:
        candidates = await tab.find_all("Load More", timeout=25)
        for element in candidates:
            if element.tag == "span":
                return element
    except Exception as e:
        log.warning(f"Could not find 'Load More' button: {e}")
    return None


async def load_connect_bars(tab, load_more_btn) -> list:
    """
    Fetch invite/connect bar elements, clicking 'Load More' first
    if the initial count is below the daily target.
    """
    connect_bars = await tab.find_all("invite", timeout=25)

    if len(connect_bars) < MAX_DAILY_CONNECTS and load_more_btn:
        log.info("Fewer results than target — clicking 'Load More'.")
        await load_more_btn.click()
        await asyncio.sleep(1.5)
        connect_bars = await tab.find_all("invite", timeout=25)

    return connect_bars


# ── Core Bot Logic ───────────────────────────────────────────────────────────
async def run_bot() -> int:
    """
    Launch browser, navigate to LinkedIn, and send connection requests.
    Returns the number of accounts connected.
    """
    connected = 0
    driver = None
    tab = None

    try:
        driver = await uc.start(
            headless=False,
            browser_executable_path=BROWSER_PATH,
            user_data_dir=PROFILE_PATH,
            browser_args=[
                f"--window-size={randint(800, 1920)},{randint(600, 1080)}",
            ],
        )

        tab = await driver.get("https://www.linkedin.com/mynetwork/grow/")
        await random_wait(1.0, 3.0)

        if not LOGGED_IN:
            input("Log in manually, then press Enter to continue...")
            return connected

        # ── Find UI Elements ─────────────────────────────────────────────────
        load_more_btn = await get_load_more_button(tab)
        if load_more_btn is None:
            log.warning("'Load More' button not found; proceeding anyway.")

        connect_bars = await load_connect_bars(tab, load_more_btn)
        log.info(f"Found {len(connect_bars)} invite elements.")

        # ── Send Connection Requests ─────────────────────────────────────────
        for bar in connect_bars:
            if connected >= MAX_DAILY_CONNECTS:
                break

            try:
                await bar.scroll_into_view()
                await bar.click()
                await random_wait(2.0, 7.0)   # Human-like delay (async)
                connected += 1
                log.info(f"Connected: {connected}/{MAX_DAILY_CONNECTS}")
            except Exception as click_err:
                log.warning(f"Failed to click a connect button: {click_err}")

    except Exception as e:
        log.error(f"Bot encountered an error: {e}", exc_info=True)

    finally:
        if tab:
            try:
                await tab.close()
            except Exception:
                pass

    return connected


# ── Entry Point ──────────────────────────────────────────────────────────────
async def main() -> None:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    records = parse_log_file()

    if should_skip(records, today):
        return

    log.info("Starting LinkedIn connection bot...")
    connected = await run_bot()

    if connected > 0:
        append_log(connected, today)
        log.info(f"Run complete. Connected with {connected} account(s).")
    else:
        log.info("No connections were made; log not updated.")


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
