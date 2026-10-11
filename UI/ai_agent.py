import os
import sys
import random
import glob

# Ensure workspace root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Auto-detect .venv site-packages if PyTorch is not in the active Python environment
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


class AIAgent:
    """Pure Reinforcement Learning agent powered by trained Deep Q-Network."""

    def __init__(self, model_filename="tictactoe_model.pth"):
        self.network = None
        self.model_path = os.path.join(project_root, model_filename)
        self._load_model()

    def _load_model(self):
        if not TORCH_AVAILABLE:
            return
        if os.path.exists(self.model_path):
            try:
                self.network = TicTacToeNetwork()
                self.network.load_state_dict(torch.load(self.model_path, map_location="cpu", weights_only=True))
                self.network.eval()
            except Exception:
                self.network = None

    def get_move(self, board, ai_piece):
        """Chooses the best legal move purely using the trained RL network's Q-values."""
        empty = [i for i in range(9) if board[i] == 0]
        if not empty:
            return None

        if self.network is not None and TORCH_AVAILABLE:
            try:
                # RL Observation: +1 for AI piece, -1 for opponent piece, 0 for empty
                obs = [1 if x == ai_piece else -1 if x != 0 else 0 for x in board]
                with torch.no_grad():
                    q = self.network(torch.tensor(obs, dtype=torch.float32))
                return empty[torch.argmax(q[empty]).item()]
            except Exception:
                pass

        # Fallback to random move if model could not be loaded
        return random.choice(empty)
