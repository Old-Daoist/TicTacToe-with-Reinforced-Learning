import os
import sys
import random
import glob
import zipfile
import pickle
import io
import struct
import collections

# Support PyInstaller standalone bundle path as well as standard directory
if hasattr(sys, "_MEIPASS"):
    project_root = sys._MEIPASS
else:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Check for numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Auto-detect .venv site-packages if PyTorch is available
TORCH_AVAILABLE = False
try:
    import torch
    from network import TicTacToeNetwork
    TORCH_AVAILABLE = True
except ImportError:
    venv_pkgs = glob.glob(os.path.join(project_root, ".venv/lib/python*/site-packages"))
    if venv_pkgs and venv_pkgs[0] not in sys.path:
        sys.path.insert(0, venv_pkgs[0])
    try:
        import torch
        from network import TicTacToeNetwork
        TORCH_AVAILABLE = True
    except ImportError:
        TORCH_AVAILABLE = False


class _StubUnpickler(pickle.Unpickler):
    """Safely extracts PyTorch state_dict metadata without requiring the PyTorch package."""
    def persistent_load(self, pid):
        return pid

    def find_class(self, module, name):
        if module == "torch._utils" and name == "_rebuild_tensor_v2":
            return lambda storage, offset, size, stride, requires_grad, hooks: {
                "storage": storage, "offset": offset, "size": size, "stride": stride
            }
        if module in ("collections", "builtins", "_codecs"):
            return super().find_class(module, name)
        return lambda *args: (module, name, args)


class AIAgent:
    """Pure Reinforcement Learning agent powered by trained Deep Q-Network."""

    def __init__(self, model_filename="tictactoe_model.pth"):
        self.model_filename = model_filename
        self.model_path = os.path.join(project_root, model_filename)
        self.torch_network = None
        self.native_weights = None
        self._load_model()

    def _load_model(self):
        candidate_paths = [
            self.model_path,
            os.path.join(os.path.dirname(sys.executable), self.model_filename),
            os.path.join(os.getcwd(), self.model_filename)
        ]
        resolved_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not resolved_path:
            return

        # 1. First try fast native loader (no torch dependency needed, instant load)
        try:
            weights = self._load_native_pth(resolved_path)
            if weights is not None:
                self.native_weights = weights
                return
        except Exception:
            pass

        # 2. Fallback to PyTorch if available
        if TORCH_AVAILABLE:
            try:
                self.torch_network = TicTacToeNetwork()
                self.torch_network.load_state_dict(torch.load(resolved_path, map_location="cpu", weights_only=True))
                self.torch_network.eval()
            except Exception:
                self.torch_network = None

    def _load_native_pth(self, pth_path):
        """Extracts MLP weights directly from .pth zip archive without importing torch."""
        with zipfile.ZipFile(pth_path, "r") as z:
            data_pkl_name = next((n for n in z.namelist() if n.endswith("data.pkl")), None)
            if not data_pkl_name:
                return None
            prefix = data_pkl_name[:-len("data.pkl")]
            entries = _StubUnpickler(io.BytesIO(z.read(data_pkl_name))).load()

            raw_dict = {}
            for k, meta in entries.items():
                storage_id = meta["storage"][2]
                raw = z.read(f"{prefix}data/{storage_id}")
                floats = list(struct.unpack(f"{len(raw)//4}f", raw))
                raw_dict[k] = (floats, meta["size"])

            if NUMPY_AVAILABLE:
                return {
                    "w0": np.array(raw_dict["network.0.weight"][0], dtype=np.float32).reshape(raw_dict["network.0.weight"][1]),
                    "b0": np.array(raw_dict["network.0.bias"][0], dtype=np.float32),
                    "w2": np.array(raw_dict["network.2.weight"][0], dtype=np.float32).reshape(raw_dict["network.2.weight"][1]),
                    "b2": np.array(raw_dict["network.2.bias"][0], dtype=np.float32),
                    "w4": np.array(raw_dict["network.4.weight"][0], dtype=np.float32).reshape(raw_dict["network.4.weight"][1]),
                    "b4": np.array(raw_dict["network.4.bias"][0], dtype=np.float32),
                    "type": "numpy"
                }
            else:
                return {
                    "w0": raw_dict["network.0.weight"][0],
                    "b0": raw_dict["network.0.bias"][0],
                    "w2": raw_dict["network.2.weight"][0],
                    "b2": raw_dict["network.2.bias"][0],
                    "w4": raw_dict["network.4.weight"][0],
                    "b4": raw_dict["network.4.bias"][0],
                    "type": "pure_python"
                }

    def _forward_native(self, obs):
        w = self.native_weights
        if w["type"] == "numpy":
            x = np.array(obs, dtype=np.float32)
            x = np.maximum(0, x @ w["w0"].T + w["b0"])
            x = np.maximum(0, x @ w["w2"].T + w["b2"])
            return (x @ w["w4"].T + w["b4"]).tolist()
        else:
            # Pure Python matrix multiply
            # Layer 1: 9 -> 256 + ReLU
            h1 = []
            for i in range(256):
                val = w["b0"][i]
                off = i * 9
                for j in range(9):
                    val += w["w0"][off + j] * obs[j]
                h1.append(val if val > 0 else 0.0)
            # Layer 2: 256 -> 256 + ReLU
            h2 = []
            for i in range(256):
                val = w["b2"][i]
                off = i * 256
                for j in range(256):
                    val += w["w2"][off + j] * h1[j]
                h2.append(val if val > 0 else 0.0)
            # Layer 3: 256 -> 9
            out = []
            for i in range(9):
                val = w["b4"][i]
                off = i * 256
                for j in range(256):
                    val += w["w4"][off + j] * h2[j]
                out.append(val)
            return out

    def get_move(self, board, ai_piece):
        """Chooses the best legal move purely using the trained RL network's Q-values."""
        empty = [i for i in range(9) if board[i] == 0]
        if not empty:
            return None

        # RL Observation: +1 for AI piece, -1 for opponent piece, 0 for empty
        obs = [1 if x == ai_piece else -1 if x != 0 else 0 for x in board]

        # 1. Native inference (fastest, 0 torch overhead)
        if self.native_weights is not None:
            try:
                q = self._forward_native(obs)
                best_val = max(q[i] for i in empty)
                return next(i for i in empty if q[i] == best_val)
            except Exception:
                pass

        # 2. PyTorch inference (if available)
        if self.torch_network is not None and TORCH_AVAILABLE:
            try:
                with torch.no_grad():
                    q = self.torch_network(torch.tensor(obs, dtype=torch.float32))
                return empty[torch.argmax(q[empty]).item()]
            except Exception:
                pass

        # Fallback to random move only if model couldn't be loaded at all
        return random.choice(empty)
