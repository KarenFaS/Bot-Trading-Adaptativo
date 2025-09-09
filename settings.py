from pathlib import Path
import os, random, numpy as np
from dotenv import load_dotenv
import time 

# 1) Cargar .env
load_dotenv()

# 1.1) Zona horaria coherente
tz = os.getenv("TZ", "Europe/Madrid")
os.environ["TZ"] = tz
try:
    time.tzset()  # puede no existir
except AttributeError:
    pass


# 2) Semillas y determinismo básico
SEED = int(os.getenv("SEED", "42"))
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
np.random.seed(SEED)

try:
    import torch
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
except Exception:
    pass

# 3) Rutas
ROOT = Path(__file__).resolve().parent
DATA_DIR  = (ROOT / os.getenv("DATA_DIR", "data")).resolve()
MODELS_DIR = (ROOT / os.getenv("MODELS_DIR", "models")).resolve()
LOGS_DIR   = (ROOT / os.getenv("LOGS_DIR", "logs")).resolve()
for d in (DATA_DIR, MODELS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

