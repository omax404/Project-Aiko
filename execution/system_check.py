import psutil
import json

def get_system_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # Get top CPU consuming processes
    procs = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] is not None:
                procs.append({
                    "name": info['name'],
                    "cpu": info['cpu_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort processes by CPU usage descending
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    top_procs = procs[:3] if procs else [{"name": "None", "cpu": 0}]
    
    return {
        "cpu": cpu,
        "ram": ram,
        "top_procs": top_procs
    }

if __name__ == "__main__":
    try:
        stats = get_system_stats()
        print(json.dumps(stats))
    except Exception as e:
        print(json.dumps({"cpu": 0, "ram": 0, "top_procs": [{"name": f"Error: {e}", "cpu": 0}]}))
