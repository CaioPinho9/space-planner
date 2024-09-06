import tkinter as tk
from tkinter import ttk
import requests
import json
from requests.exceptions import ConnectionError, Timeout, RequestException

host = "http://127.0.0.1:5000"


class SpacePlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Planner")
        self.geometry("800x600")

        # Table columns
        self.columns = ["Time", "Income per Second", "Thing", "Cost", "Quantity"]

        # Create Table
        self.table = ttk.Treeview(self, columns=self.columns, show="headings")

        # Adjusted column width settings
        self.table.heading("Time", text="Time")
        self.table.column("Time", width=120)

        self.table.heading("Income per Second", text="Income per Second")
        self.table.column("Income per Second", width=150)

        self.table.heading("Thing", text="Thing")
        self.table.column("Thing", width=150)

        self.table.heading("Cost", text="Cost")
        self.table.column("Cost", width=120)

        self.table.heading("Quantity", text="Quantity")
        self.table.column("Quantity", width=120)

        self.table.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Labels for best_index, best_income, simulation_index, and average_income
        self.label_vars = {
            "Best Index": tk.StringVar(),
            "Best Income": tk.StringVar(),
            "Simulation Index": tk.StringVar(),
            "Average Income": tk.StringVar(),
            "Elapsed Time": tk.StringVar(),
            "Simulations per Second": tk.StringVar()
        }

        for i, (label, var) in enumerate(self.label_vars.items(), start=1):
            tk.Label(self, text=f"{label}:").grid(row=i, column=0, sticky="w")
            tk.Label(self, textvariable=var).grid(row=i, column=1, sticky="w")

        # Buyable things list
        self.buyable_list = tk.Listbox(self, height=10)
        self.buyable_list.grid(row=0, column=2, rowspan=4, sticky="nsew")
        self.buyable_list.bind("<<ListboxSelect>>", self.buy_item)

        # Start income input
        tk.Label(self, text="Start Income:").grid(row=4, column=0, sticky="w")
        self.start_income_entry = tk.Entry(self)
        self.start_income_entry.grid(row=4, column=1, sticky="ew")

        # Start, End, and Save buttons
        self.start_button = tk.Button(self, text="Start Simulation", command=self.start_simulation)
        self.start_button.grid(row=5, column=0, columnspan=2, sticky="ew")

        self.end_button = tk.Button(self, text="End Simulation", command=self.end_simulation)
        self.end_button.grid(row=6, column=0, columnspan=2, sticky="ew")

        self.save_button = tk.Button(self, text="Save Simulation", command=self.save_simulation)
        self.save_button.grid(row=7, column=0, columnspan=2, sticky="ew")

        # Start the update loop
        self.update_simulation_results()
        self.update_buyable_list()

    def update_simulation_results(self):
        try:
            response = requests.get(host + '/simulation/results')
            response.raise_for_status()  # Raise exception for 4XX/5XX errors

            if response.status_code == 200:
                data = response.json()
                best_log = data["best_log"]

                # Update the table
                self.table.delete(*self.table.get_children())
                for i, row in enumerate(best_log[:10]):  # Paginate by 10 rows
                    self.table.insert("", "end", values=(
                        row["Time"], row["Income per Second"], row["Thing"], row["Cost"], row["Quantity"]
                    ))

                # Update labels
                self.label_vars["Best Index"].set(data["best_index"])
                self.label_vars["Best Income"].set(data["best_income"])
                self.label_vars["Simulation Index"].set(data["simulation_index"])
                self.label_vars["Average Income"].set(data["average_income"])
                self.label_vars["Elapsed Time"].set(data["time_elapsed"])
                self.label_vars["Simulations per Second"].set(data["simulations_per_second"])

        except (ConnectionError, Timeout) as e:
            print(f"Error: {e}. Could not connect to the server.")
        except RequestException as e:
            print(f"Request failed: {e}")

        # Repeat every second
        self.after(1000, self.update_simulation_results)

    def update_buyable_list(self):
        try:
            response = requests.get(host + '/thing_maker/buyable')
            response.raise_for_status()  # Raise exception for 4XX/5XX errors

            if response.status_code == 200:
                buyable_things = response.json()

                if not buyable_things:
                    self.after(1000, self.update_buyable_list)
                    return

                # Clear the list
                self.buyable_list.delete(0, tk.END)

                # Add buyable things to the list
                for thing in buyable_things:
                    self.buyable_list.insert(tk.END, f'{thing["name"]}: {thing["quantity"]}')

        except (ConnectionError, Timeout) as e:
            print(f"Error: {e}. Could not connect to the server.")
            self.after(1000, self.update_buyable_list)
        except RequestException as e:
            print(f"Request failed: {e}")

    def buy_item(self, event):
        selection = self.buyable_list.curselection()
        if selection:
            selected_item = self.buyable_list.get(selection[0])
            thing_name = selected_item.split(":")[0]  # Extract thing name

            try:
                response = requests.post(f'{host}/thing_maker/buy/{thing_name}')
                response.raise_for_status()  # Raise exception for 4XX/5XX errors

                if response.status_code == 200:
                    print(f"Bought {thing_name} successfully!")
                    self.update_buyable_list()

            except (ConnectionError, Timeout) as e:
                print(f"Error: {e}. Could not connect to the server.")
            except RequestException as e:
                print(f"Request failed: {e}")

    def start_simulation(self):
        start_income = self.start_income_entry.get()
        if start_income:
            try:
                start_income_value = float(start_income)
                payload = {"start_income": start_income_value}

                try:
                    response = requests.post(host + '/simulation/start', json=payload)
                    response.raise_for_status()  # Raise exception for 4XX/5XX errors

                    if response.status_code == 200:
                        print("Simulation started successfully!")
                    else:
                        print("Failed to start simulation.")

                except (ConnectionError, Timeout) as e:
                    print(f"Error: {e}. Could not connect to the server.")
                except RequestException as e:
                    print(f"Request failed: {e}")

            except ValueError:
                print("Invalid start income. Please enter a valid number.")
        else:
            print("Start income is required.")

    @staticmethod
    def end_simulation():
        try:
            response = requests.post(host + '/simulation/end')
            response.raise_for_status()  # Raise exception for 4XX/5XX errors

            if response.status_code == 200:
                print("Simulation ended successfully!")
            else:
                print("Failed to end simulation.")

        except (ConnectionError, Timeout) as e:
            print(f"Error: {e}. Could not connect to the server.")
        except RequestException as e:
            print(f"Request failed: {e}")

    @staticmethod
    def save_simulation():
        try:
            response = requests.post(host + '/simulation/save')
            response.raise_for_status()  # Raise exception for 4XX/5XX errors

            if response.status_code == 200:
                print("Simulation saved successfully!")
            else:
                print("Failed to save simulation.")

        except (ConnectionError, Timeout) as e:
            print(f"Error: {e}. Could not connect to the server.")
        except RequestException as e:
            print(f"Request failed: {e}")


# Run the app
if __name__ == "__main__":
    app = SpacePlanner()
    app.mainloop()
