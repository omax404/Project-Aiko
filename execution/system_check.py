import psutil
import json

def get_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    procs = []
    for p in sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda x: x.info['cpu_percent'], reverse=True)[:5]:
        procs.append(p.info)
        
    return {
        "cpu": cpu,
        "ram": ram,
        "top_procs": procs
    }

if __name__ == "__main__":
    print(json.dumps(get_stats()))
