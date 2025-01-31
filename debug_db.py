import sqlite3

def print_tables():
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    print("=== Table sessions ===")
    c.execute("SELECT * FROM sessions")
    sessions = c.fetchall()
    for session in sessions:
        print(f"ID: {session[0]}, Date: {session[1]}, Type: {session[2]}")
        
    print("\n=== Table exercises ===")
    c.execute("SELECT * FROM exercises")
    exercises = c.fetchall()
    for exercise in exercises:
        print(f"ID: {exercise[0]}, Session: {exercise[1]}, Exercise: {exercise[2]}, Set: {exercise[3]}, Reps: {exercise[4]}, Weight: {exercise[5]}")
    
    conn.close()

if __name__ == "__main__":
    print_tables()
