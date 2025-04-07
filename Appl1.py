import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta

class TrainScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расписание поездов")
        self.root.geometry("1000x600")
        self.conn = sqlite3.connect('trains.db')
        self.create_tables()
        self.current_route_id = None
        self.current_station_id = None
        self.setup_ui()
        self.load_routes()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY,
                route_id INTEGER NOT NULL,
                order_index INTEGER NOT NULL,
                city TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                travel_time INTEGER,
                FOREIGN KEY (route_id) REFERENCES routes(id)
            )
        ''')
        self.conn.commit()

    def setup_ui(self):
        # Левая панель: Список маршрутов
        self.left_frame = tk.Frame(self.root, width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.route_list = tk.Listbox(self.left_frame)
        self.route_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.route_list.bind('<<ListboxSelect>>', self.on_route_select)
        self.new_route_btn = tk.Button(self.left_frame, text="Новый маршрут", command=self.create_route)
        self.new_route_btn.pack(fill=tk.X, padx=5, pady=2)
        self.del_route_btn = tk.Button(self.left_frame, text="Удалить маршрут", command=self.delete_route)
        self.del_route_btn.pack(fill=tk.X, padx=5, pady=2)

        # Средняя панель: Список станций
        self.middle_frame = tk.Frame(self.root)
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.station_list = tk.Listbox(self.middle_frame)
        self.station_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.station_list.bind('<<ListboxSelect>>', self.on_station_select)
        self.add_station_btn = tk.Button(self.middle_frame, text="Добавить станцию", command=self.add_station)
        self.add_station_btn.pack(fill=tk.X, padx=5, pady=2)
        self.del_station_btn = tk.Button(self.middle_frame, text="Удалить станцию", command=self.delete_station)
        self.del_station_btn.pack(fill=tk.X, padx=5, pady=2)

        # Правая панель: Редактирование станции
        self.right_frame = tk.Frame(self.root, width=300)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.right_frame, text="Город:").pack(anchor=tk.W)
        self.city_entry = tk.Entry(self.right_frame)
        self.city_entry.pack(fill=tk.X)
        
        tk.Label(self.right_frame, text="Время отправления (ЧЧ:ММ):").pack(anchor=tk.W)
        self.departure_entry = tk.Entry(self.right_frame)
        self.departure_entry.pack(fill=tk.X)
        
        tk.Label(self.right_frame, text="Время в пути до следующей (мин):").pack(anchor=tk.W)
        self.travel_entry = tk.Entry(self.right_frame)
        self.travel_entry.pack(fill=tk.X)
        
        tk.Label(self.right_frame, text="Время прибытия:").pack(anchor=tk.W)
        self.arrival_label = tk.Label(self.right_frame, text="")
        self.arrival_label.pack(anchor=tk.W)
        
        tk.Label(self.right_frame, text="Время стоянки:").pack(anchor=tk.W)
        self.dwell_label = tk.Label(self.right_frame, text="")
        self.dwell_label.pack(anchor=tk.W)
        
        self.save_btn = tk.Button(self.right_frame, text="Сохранить", command=self.save_station)
        self.save_btn.pack(fill=tk.X, pady=5)

    def load_routes(self):
        self.route_list.delete(0, tk.END)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM routes")
        for route in cursor.fetchall():
            self.route_list.insert(tk.END, route[1])

    def create_route(self):
        name = simpledialog.askstring("Создать маршрут", "Введите название маршрута:")
        if name:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO routes (name) VALUES (?)", (name,))
            self.conn.commit()
            self.load_routes()

    def delete_route(self):
        selected = self.route_list.curselection()
        if not selected:
            return
        route_name = self.route_list.get(selected[0])
        route_id = self.get_route_id(route_name)
        if messagebox.askyesno("Удалить маршрут", f"Удалить маршрут '{route_name}'?"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM routes WHERE name=?", (route_name,))
            cursor.execute("DELETE FROM stations WHERE route_id=?", (route_id,))
            self.conn.commit()
            self.load_routes()
            self.station_list.delete(0, tk.END)

    def get_route_id(self, route_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM routes WHERE name=?", (route_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def on_route_select(self, event):
        selected = self.route_list.curselection()
        if not selected:
            return
        route_name = self.route_list.get(selected[0])
        route_id = self.get_route_id(route_name)
        if route_id is None:
            messagebox.showerror("Ошибка", "Маршрут не найден!")
            self.station_list.delete(0, tk.END)
            return
        self.current_route_id = route_id
        self.load_stations()

    def load_stations(self):
        self.station_list.delete(0, tk.END)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, city, departure_time, travel_time 
            FROM stations 
            WHERE route_id=? 
            ORDER BY order_index
        """, (self.current_route_id,))
        stations = cursor.fetchall()
        for station in stations:
            self.station_list.insert(tk.END, f"{station[1]} ({station[2]})")
        if stations:
            self.station_list.selection_set(0)
            self.on_station_select(None)

    def add_station(self):
        if not self.current_route_id:
            messagebox.showwarning("Ошибка", "Сначала выберите маршрут!")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(order_index) FROM stations WHERE route_id=?", (self.current_route_id,))
        max_order = cursor.fetchone()[0] or 0

        city = simpledialog.askstring("Новая станция", "Введите название станции:")
        if not city:
            return

        if max_order == 0:
            # Первая станция
            departure_time = simpledialog.askstring("Время отправления", "Введите время отправления (ЧЧ:ММ):")
            if not self.validate_time(departure_time):
                messagebox.showerror("Ошибка", "Неверный формат времени!")
                return
            travel_time = 0
        else:
            # Получаем данные предыдущей станции
            cursor.execute("""
                SELECT departure_time, travel_time 
                FROM stations 
                WHERE route_id=? AND order_index=?
            """, (self.current_route_id, max_order))
            prev_departure, prev_travel = cursor.fetchone()
            
            # Запрашиваем время в пути
            travel_time = simpledialog.askinteger("Время в пути", "Введите время в пути до следующей станции (минуты):")
            if not travel_time or travel_time < 0:
                messagebox.showerror("Ошибка", "Неверное время в пути!")
                return

            # Рассчитываем время прибытия и отправления
            arrival = self.calculate_arrival(prev_departure, prev_travel)
            departure_time = arrival

        cursor.execute("""
            INSERT INTO stations (route_id, order_index, city, departure_time, travel_time)
            VALUES (?, ?, ?, ?, ?)
        """, (self.current_route_id, max_order + 1, city, departure_time, travel_time))
        self.conn.commit()
        
        # Пересчитываем время для последующих станций
        self.recalculate_times(max_order + 1)
        self.load_stations()

    def delete_station(self):
        selected = self.station_list.curselection()
        if not selected:
            return
        station_index = selected[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, order_index FROM stations WHERE route_id=? ORDER BY order_index", (self.current_route_id,))
        stations = cursor.fetchall()
        if not stations:
            return
        deleted_order = stations[station_index][1]
        cursor.execute("DELETE FROM stations WHERE id=?", (stations[station_index][0],))
        self.conn.commit()
        # Пересчитываем время отправления для последующих станций
        if deleted_order < len(stations):
            self.recalculate_times(deleted_order)
        self.load_stations()

    def recalculate_times(self, start_order):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, departure_time, travel_time 
            FROM stations 
            WHERE route_id=? AND order_index >= ?
            ORDER BY order_index
        """, (self.current_route_id, start_order))
        stations = cursor.fetchall()
        if not stations:
            return

        # Начинаем с предыдущей станции
        if start_order > 1:
            cursor.execute("""
                SELECT departure_time, travel_time 
                FROM stations 
                WHERE route_id=? AND order_index=?
            """, (self.current_route_id, start_order-1))
            prev_data = cursor.fetchone()
            if prev_data:
                current_time = datetime.strptime(prev_data[0], "%H:%M") + timedelta(minutes=prev_data[1])
            else:
                current_time = datetime.strptime("00:00", "%H:%M")
        else:
            current_time = datetime.strptime(stations[0][1], "%H:%M")

        for station in stations:
            new_departure = current_time.strftime("%H:%M")
            cursor.execute("UPDATE stations SET departure_time=? WHERE id=?", (new_departure, station[0]))
            current_time = datetime.strptime(new_departure, "%H:%M") + timedelta(minutes=station[2] or 0)
        
        self.conn.commit()

    def on_station_select(self, event):
        selected = self.station_list.curselection()
        if not selected:
            return
        station_index = selected[0]
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, city, departure_time, travel_time, order_index 
            FROM stations 
            WHERE route_id=? 
            ORDER BY order_index
        """, (self.current_route_id,))
        stations = cursor.fetchall()
        if not stations:
            return
        station = stations[station_index]
        self.current_station_id = station[0]
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, station[1])

        # Обновляем интерфейс в зависимости от позиции станции
        if station_index == 0:
            self.departure_entry.config(state=tk.NORMAL)
            self.departure_entry.delete(0, tk.END)
            self.departure_entry.insert(0, station[2])
        else:
            self.departure_entry.config(state=tk.DISABLED)
            self.departure_entry.delete(0, tk.END)
            self.departure_entry.insert(0, station[2])

        if station_index == len(stations) - 1:
            self.travel_entry.config(state=tk.DISABLED)
            self.travel_entry.delete(0, tk.END)
            self.travel_entry.insert(0, "0")
        else:
            self.travel_entry.config(state=tk.NORMAL)
            self.travel_entry.delete(0, tk.END)
            self.travel_entry.insert(0, str(station[3]))

        # Рассчитываем время прибытия и стоянки
        if station_index == 0:
            arrival_time = station[2]
            dwell_time = 0
        else:
            prev_station = stations[station_index - 1]
            arrival_time = self.calculate_arrival(prev_station[2], prev_station[3])
            dwell_time = self.calculate_dwell(arrival_time, station[2])

        self.arrival_label.config(text=arrival_time)
        self.dwell_label.config(text=f"{dwell_time} мин")

    def calculate_arrival(self, departure, travel):
        try:
            dep_time = datetime.strptime(departure, "%H:%M")
            arrival = dep_time + timedelta(minutes=int(travel))
            return arrival.strftime("%H:%M")
        except:
            return "Ошибка"

    def calculate_dwell(self, arrival, departure):
        try:
            arr = datetime.strptime(arrival, "%H:%M")
            dep = datetime.strptime(departure, "%H:%M")
            dwell = (dep - arr).seconds // 60
            return max(dwell, 0)
        except:
            return 0

    def save_station(self):
        city = self.city_entry.get()
        departure = self.departure_entry.get()
        travel_time = self.travel_entry.get()

        if not self.validate_time(departure):
            messagebox.showerror("Ошибка", "Неверный формат времени отправления!")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT order_index FROM stations WHERE id=?", (self.current_station_id,))
        order_index = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(order_index) FROM stations WHERE route_id=?", (self.current_route_id,))
        max_order = cursor.fetchone()[0]

        # Получаем текущую станцию
        cursor.execute("""
            SELECT city, departure_time, travel_time 
            FROM stations 
            WHERE id=?
        """, (self.current_station_id,))
        current_data = cursor.fetchone()

        # Обновляем данные станции
        new_travel = int(travel_time) if travel_time else 0
        if order_index == max_order:
            new_travel = 0

        cursor.execute("""
            UPDATE stations 
            SET city=?, departure_time=?, travel_time=?
            WHERE id=?
        """, (city, departure, new_travel, self.current_station_id))

        # Пересчитываем время для последующих станций
        if order_index < max_order:
            self.recalculate_times(order_index)

        self.conn.commit()
        self.load_stations()
        self.station_list.selection_clear(0, tk.END)
        self.station_list.selection_set(order_index)
        self.on_station_select(None)

    def validate_time(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = TrainScheduleApp(root)
    root.mainloop()