import time
import threading
import os
import json
import keyboard
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify

def set_cmd_title(title):
    os.system(f'title {title}')

class UserActivityTracker:
    def __init__(self, site_name):
        self.driver = webdriver.Chrome()
        self.site_name = site_name
        self.driver.get(f"http://{site_name}")
        self.actions = ActionChains(self.driver)
        self.driver.maximize_window()

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self.script_dir, f"{site_name}_activity_log.txt")

        print(f"\033[94mLog file path: {self.log_file}\033[0m")

        self.is_tracking = True
        self.setup_event_listeners()
        self.setup_flask_server()

    def setup_event_listeners(self):
        self.driver.execute_script("""
        document.addEventListener('click', function(event) {
            const element = event.target;
            const elementDetails = {
                tag: element.tagName,
                id: element.id,
                class: element.className,
                text: element.innerText
            };
            window.trackClick(JSON.stringify(elementDetails));
        });

        document.addEventListener('keydown', function(event) {
            const keyDetails = {
                key: event.key,
                code: event.code
            };
            window.trackKeyPress(JSON.stringify(keyDetails));
        });
        """)

        self.driver.execute_script("""
        window.trackClick = function(details) {
            if (window.external.loggingEnabled) {
                const now = new Date().toISOString();
                const logEntry = now + " CLICK: " + details;
                window.external.log(logEntry);
            }
        };

        window.trackKeyPress = function(details) {
            if (window.external.loggingEnabled) {
                const now = new Date().toISOString();
                const logEntry = now + " KEYPRESS: " + details;
                window.external.log(logEntry);
            }
        };
        """)

    def setup_flask_server(self):
        app = Flask(__name__)

        @app.route('/log', methods=['POST'])
        def log_route():
            log_data = request.json
            if log_data and "log" in log_data:
                self.log(log_data["log"])
            return jsonify(success=True)

        def run_flask():
            app.run(port=5000)

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

    def log(self, entry):
        try:
            with open(self.log_file, "a") as file:
                file.write(entry + "\n")
            print(f"\033[92mLog entry added: {entry}\033[0m")
        except Exception as e:
            print(f"\033[91mError writing to log file: {e}\033[0m")

    def start_tracking(self):
        self.driver.execute_script("""
        window.external = {
            loggingEnabled: true
        };
        window.external.log = function(logEntry) {
            const logData = {log: logEntry};
            fetch("http://localhost:5000/log", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(logData)
            });
        };
        """)

        while self.is_tracking:
            time.sleep(1)

    def stop_tracking(self):
        self.is_tracking = False
        self.driver.quit()
        if os.path.isfile(self.log_file):
            print(f"\033[92mTracking stopped. Log file saved as {self.log_file}\033[0m")
        else:
            print(f"\033[91mTracking stopped, but log file was not found. Ensure logging is working correctly.\033[0m")

    def playback_log(self, times):
        try:
            with open(self.log_file, "r") as file:
                logs = file.readlines()
            for _ in range(times):
                for log in logs:
                    if "CLICK" in log:
                        self.simulate_click(log)
                    elif "KEYPRESS" in log:
                        self.simulate_keypress(log)
                    time.sleep(1)
        except Exception as e:
            print(f"\033[91mError reading log file: {e}\033[0m")

    def simulate_click(self, log):
        try:
            details = json.loads(log.split(" CLICK: ")[1])
            element = self.driver.find_element(By.CSS_SELECTOR, f"#{details['id']}, .{details['class']}, {details['tag']}")
            self.actions.move_to_element(element).click().perform()
        except Exception as e:
            print(f"\033[91mError simulating click: {e}\033[0m")

    def simulate_keypress(self, log):
        try:
            details = json.loads(log.split(" KEYPRESS: ")[1])
            element = self.driver.switch_to.active_element
            if element:
                element.send_keys(details['key'])
        except Exception as e:
            print(f"\033[91mError simulating keypress: {e}\033[0m")

def animate_title(base_title):
    while True:
        for i in range(len(base_title) + 1):
            os.system(f'title {base_title[:i]}')
            time.sleep(0.1)
        time.sleep(0.5)
        for i in range(len(base_title) + 1):
            os.system(f'title {base_title[:len(base_title) - i]}')
            time.sleep(0.1)
        time.sleep(0.5)

def display_menu():
    print("\033[96mAccount Generator Options\033[0m")
    print("\033[91m1. Playback Log\033[0m")
    print("\033[91m2. Exit\033[0m")

    try:
        option = int(input("\033[92mEnter your choice: \033[0m"))
    except ValueError:
        print("\033[91mInvalid input. Please enter a number.\033[0m")
        return None
    return option

def prompt_user():
    print("\033[96mWelcome to the Account Generator Setup\033[0m")
    site_name = input("\033[93mEnter the site name (without http://): \033[92m")
    return site_name

def main():
    base_title = "Account Gen Maker By Marcelo"
    threading.Thread(target=animate_title, args=(base_title,)).start()

    site_name = prompt_user()
    tracker = UserActivityTracker(site_name)
    threading.Thread(target=tracker.start_tracking).start()

    def on_f1_press(event):
        print("\033[93mF1 key pressed. Stopping tracking...\033[0m")
        tracker.stop_tracking()

    keyboard.on_press_key('F1', on_f1_press)

    while True:
        option = display_menu()
        if option is None:
            continue

        if option == 1:
            try:
                times = int(input("\033[93mEnter the number of times to playback the log: \033[92m"))
                tracker.playback_log(times)
            except ValueError:
                print("\033[91mInvalid number. Please enter a valid integer.\033[0m")
        elif option == 2:
            tracker.stop_tracking()
            break
        else:
            print("\033[91mInvalid choice. Please try again.\033[0m")

if __name__ == "__main__":
    main()
