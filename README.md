# 🚘 ParkFlow - Smart Parking Management System

**ParkFlow** is a data-driven Python web application built to manage parking spots, entry/exit operations, waiting lists, and real-time occupancy[cite: 34]. 

This project was developed as a graduation project applying core algorithms, data structures, object-oriented programming (OOP), data analytics, and a modern Streamlit interface[cite: 34]. 

---

## ✨ Features & User Roles

The system implements Role-Based Access Control (RBAC) with tailored interfaces for three main users[cite: 34]:

1. **Admin (Control Panel)**[cite: 34]:
   * Views a real-time 2D colored map of the parking lot[cite: 34].
   * Accesses a live metrics dashboard (Available, Occupied, Reserved, Waiting)[cite: 34].
   * Analyzes historical data using Pandas (Entries per hour/day, usage by floor, total revenue) and interactive charts[cite: 28, 34].
   * Manages employee (Gate Operator) accounts.

2. **Employee / Gate Operator (Operations Tab)**[cite: 28, 34]:
   * Manages vehicle check-ins (walk-ins and pre-reserved) and check-outs.
   * Views the active sessions and waiting list queue[cite: 28].
   * Has the ability to "Undo" the last parking/queue action safely[cite: 28].

3. **Customer / Driver (Driver Portal)**[cite: 28, 34]:
   * Views live available spaces[cite: 28].
   * Reserves a parking space in advance (restricted to returning customers)[cite: 28].
   * Registers new vehicles to their account.
   * Searches for parked vehicles using exact or partial plate matching[cite: 28].

---

## 🧠 Technical Architecture

The project strictly follows a Clean Architecture pattern, separating the Business Logic from the User Interface ("No business rules in the UI")[cite: 28].

* **`core/`**: Contains all business logic, models, validators, and custom data structures[cite: 1, 28].
* **`ui/`**: Contains all Streamlit presentation logic and role-based routing[cite: 1, 28].
* **`data/`**: Stores persistent application state in CSV files (`sessions.csv`, `users.csv`, `parked.csv`, `waiting.csv`)[cite: 1, 28, 58].
* **`tests/`**: Contains automated tests (`pytest`) and the manual UI testing checklist[cite: 1, 28].

### Algorithms & Data Structures Used
* **Hash Tables**: For fast O(1) lookups of users and active parking sessions[cite: 28, 34].
* **Queues (FIFO)**: To manage the waiting list when the lot is full[cite: 28, 34].
* **Stacks (LIFO)**: To maintain an action history for the "Undo" feature[cite: 28, 34].
* **Sorting**: Merge Sort (O(n log n)) and Insertion Sort implemented manually to sort session history[cite: 28, 34].
* **Searching**: Binary Search (requires sorting first) and Sequential Search for plate lookups[cite: 28, 34].
* **Greedy Algorithm**: Allocating the closest available space to the entrance (distance formula)[cite: 28].

---

## 🚀 Installation & Setup

Follow these steps to run the application on your local machine.

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system. 

### 2. Required Libraries
The application depends on the following libraries. You should have a `requirements.txt` file[cite: 28] containing:
```text
streamlit
pandas
pytest