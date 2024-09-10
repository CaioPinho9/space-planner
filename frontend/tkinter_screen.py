import tkinter as tk
from tkinter import ttk, simpledialog
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

host = "http://127.0.0.1:5000"


class SpacePlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.running_simulation = False

        self.title("Space Planner")
        self.geometry("675x500")

        # Table columns
        self.columns = ["Time", "Income", "Thing", "Cost", "Quantity"]

        # Create Table
        self.table = ttk.Treeview(self, columns=self.columns, show="headings")

        # Adjusted column width settings
        self.table.heading("Time", text="Time")
        self.table.column("Time", width=100)

        self.table.heading("Income", text="Income")
        self.table.column("Income", width=100)

        self.table.heading("Thing", text="Thing")
        self.table.column("Thing", width=150)

        self.table.heading("Cost", text="Cost")
        self.table.column("Cost", width=100)

        self.table.heading("Quantity", text="Quantity")
        self.table.column("Quantity", width=75)

        self.table.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Labels for best_index, best_income, simulation_index, and average_income
        self.label_vars = {
            "Best Index": tk.StringVar(),
            "Best Income": tk.StringVar(),
            "Simulation Index": tk.StringVar(),
            "Average Income": tk.StringVar(),
            "Current Income": tk.StringVar(),
            "Elapsed Time": tk.StringVar(),
            "Simulations per Second": tk.StringVar(),
            "Simulation Time": tk.StringVar()
        }

        for i, (label, var) in enumerate(self.label_vars.items(), start=1):
            tk.Label(self, text=f"{label}:").grid(row=i, column=0, sticky="w")
            tk.Label(self, textvariable=var).grid(row=i, column=1, sticky="w")

        # Buyable things list
        self.buyable_list = tk.Listbox(self, height=10)
        self.buyable_list.grid(row=0, column=2, rowspan=4, sticky="nsew")
        self.buyable_list.bind("<<ListboxSelect>>", self.buy_item)

        # Start income input
        tk.Label(self, text="Start Income:").grid(row=9, column=0, sticky="w")
        self.start_income_entry = tk.Entry(self)
        self.start_income_entry.grid(row=9, column=1, sticky="ew")

        # Start, End, and Save buttons
        self.start_button = tk.Button(self, text="Start Simulation", command=self.start_simulation)
        self.start_button.grid(row=10, column=0, columnspan=2, sticky="ew")

        self.end_button = tk.Button(self, text="End Simulation", command=self.end_simulation)
        self.end_button.grid(row=11, column=0, columnspan=2, sticky="ew")

        self.save_button = tk.Button(self, text="Save Simulation", command=self.save_simulation)
        self.save_button.grid(row=12, column=0, columnspan=2, sticky="ew")

        self.view_prices_button = tk.Button(self, text="View Prices", command=self.show_price_modal)
        self.view_prices_button.grid(row=13, column=0, columnspan=2, sticky="ew")

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
                        row["Time"], f"{row['Income']:.2f}", row["Thing"], row["Cost"], row["Quantity"]
                    ))

                # Update labels
                self.label_vars["Best Index"].set(data["best_index"])
                self.label_vars["Best Income"].set(f"{data['best_income']:.2f}W ")
                self.label_vars["Simulation Index"].set(data["simulation_index"])
                self.label_vars["Average Income"].set(f"{data['average_income']:.2f}W")
                self.label_vars["Current Income"].set(f"{data['current_income']:.2f}W")
                # Convert seconds to datetime like hh:mm:ss
                elapsed_time = int(data["time_elapsed"])
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.label_vars["Elapsed Time"].set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                self.label_vars["Simulations per Second"].set(f"{data['simulations_per_second']:.2f}")
                # Convert seconds to ms
                simulation_time = data["simulation_time"] * 1000
                self.label_vars["Simulation Time"].set(f"{simulation_time:.2f} ms")


        except (ConnectionError, Timeout) as e:
            print(f"Error: {e}. Could not connect to the server.")
        except RequestException as e:
            print(f"Request failed: {e}")

        # Repeat every second
        if self.running_simulation:
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
        except RequestException as e:
            print(f"Request failed: {e}")

    def buy_item(self, event):
        selection = self.buyable_list.curselection()
        if selection:
            selected_item = self.buyable_list.get(selection[0])
            thing_name = selected_item.split(":")[0]  # Extract thing name

            try:
                response = requests.get(f'{host}/thing_maker/buy/{thing_name}')
                response.raise_for_status()  # Raise exception for 4XX/5XX errors

                if response.status_code == 200:
                    print(f"Bought {thing_name} successfully!")
                    self.update_buyable_list()

            except (ConnectionError, Timeout) as e:
                print(f"Error: {e}. Could not connect to the server.")
            except RequestException as e:
                print(f"Request failed: {e}")

    def start_simulation(self):
        self.running_simulation = True
        start_income = self.start_income_entry.get()
        try:
            payload = {}
            if start_income:
                start_income_value = float(start_income)
                payload = {"start_income": start_income_value}

            try:
                response = requests.post(host + '/simulation/start', json=payload)
                response.raise_for_status()  # Raise exception for 4XX/5XX errors

                if response.status_code == 200:
                    print("Simulation started successfully!")
                    self.update_simulation_results()
                    self.update_buyable_list()
                else:
                    print("Failed to start simulation.")

            except (ConnectionError, Timeout) as e:
                print(f"Error: {e}. Could not connect to the server.")
            except RequestException as e:
                print(f"Request failed: {e}")

        except ValueError:
            print("Invalid start income. Please enter a valid number.")

    def end_simulation(self):
        try:
            response = requests.post(host + '/simulation/end')
            response.raise_for_status()  # Raise exception for 4XX/5XX errors

            if response.status_code == 200:
                print("Simulation ended successfully!")
                self.running_simulation = False
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

    def show_price_modal(self):
        # Modal window setup
        modal = tk.Toplevel(self)
        modal.title("Price Table")
        modal.geometry("600x400")

        # Sample data
        price_data = {
            "SolarPanel": [17, 20, 23, 26, 30, 34, 39, 45, 52, 60, 69, 79, 91, 105, 121, 139, 160, 184],
            "Potato": [120, 138, 159, 183, 210, 241, 277, 319, 367, 422, 485],
            "Probetato": [680, 782, 899, 1034, 1189, 1367, 1572, 1808, 2079, 2391, 2750],
            "Spudnik": [13700, 15755, 18118, 20836, 23961, 27555, 31688, 36441, 41907, 48193, 55422],
            "PotatoPlant": [284000]
        }

        # Treeview for the modal table
        columns = list(price_data.keys())
        tree = ttk.Treeview(modal, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Insert the data into the table
        max_length = max(len(lst) for lst in price_data.values())
        for i in range(max_length):
            values = [price_data[col][i] if i < len(price_data[col]) else "" for col in columns]
            tree.insert("", "end", values=values)

        tree.pack(fill=tk.BOTH, expand=True)

        # Add new value button
        add_button = tk.Button(modal, text="Add New Value", command=lambda: self.add_new_price(modal, tree, price_data))
        add_button.pack()

    def add_new_price(self, modal, tree, price_data):
        # Prompt for thing and new price
        thing_name = simpledialog.askstring("Input", "Enter thing name (e.g., SolarPanel):", parent=modal)
        new_price = simpledialog.askfloat("Input", f"Enter new price for {thing_name}:", parent=modal)

        if thing_name and new_price is not None:
            # Update the price_data with new value
            if thing_name in price_data:
                price_data[thing_name].append(new_price)

                # Send the new value to the server
                try:
                    response = requests.get(f'{host}/predictor/thing_price/{thing_name}/{int(new_price)}')
                    response.raise_for_status()

                    if response.status_code == 200:
                        print(f"New price {new_price} added to {thing_name} successfully!")
                    else:
                        print(f"Failed to add new price to {thing_name}.")

                except (ConnectionError, Timeout) as e:
                    print(f"Error: {e}. Could not connect to the server.")
                except RequestException as e:
                    print(f"Request failed: {e}")

                # Refresh the treeview
                self.refresh_price_table(tree, price_data)

    @staticmethod
    def refresh_price_table(tree, price_data):
        # Clear the current table
        tree.delete(*tree.get_children())

        # Reinsert updated data
        max_length = max(len(lst) for lst in price_data.values())
        for i in range(max_length):
            values = [price_data[col][i] if i < len(price_data[col]) else "" for col in price_data.keys()]
            tree.insert("", "end", values=values)


def run_tkinter():
    space_planner = SpacePlanner()
    space_planner.mainloop()
