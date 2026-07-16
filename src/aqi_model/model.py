"""
model.py — CNN-LSTM + Self-Attention Architecture for Surface AQI Estimation

Architecture:
    Input (Batch, SeqLen=4, Features=18)
        → 1D CNN Block    (feature interaction within each time step)
        → LSTM Block      (temporal persistence across lag window)
        → Self-Attention  (dynamically weight which lag day matters most)
        → Dense Regressor (predict continuous CPCB_AQI 0-500)

Design rationale:
  - 1D CNN: captures high-order feature interactions (e.g. NO2 × wind_speed)
    within a single time step without temporal mixing
  - LSTM: models day-to-day AQI persistence (r=0.914 in Delhi)
  - Attention: learns which lag step is most predictive under varying
    atmospheric conditions (yesterday vs 3-days-ago matters differently
    in stable vs unstable weather)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class TemporalAttention(nn.Module):
    """
    Scaled dot-product self-attention over LSTM hidden states.
    Learns which time steps (lags) are most predictive.
    """
    def __init__(self, hidden_size: int):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, lstm_out: torch.Tensor) -> torch.Tensor:
        """
        Args:
            lstm_out: (Batch, SeqLen, HiddenSize)
        Returns:
            context:  (Batch, HiddenSize)  — attention-weighted sum
        """
        # (Batch, SeqLen, 1) → (Batch, SeqLen)
        scores = self.attn(lstm_out).squeeze(-1)
        weights = F.softmax(scores, dim=1)              # (Batch, SeqLen)
        context = torch.bmm(weights.unsqueeze(1), lstm_out).squeeze(1)  # (Batch, H)
        return context


class CNNBlock(nn.Module):
    """
    1D CNN applied along the feature dimension (NOT the time dimension).
    Captures interactions between meteorological + satellite features.
    """
    def __init__(self, n_features: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        padding = kernel_size // 2
        self.conv1 = nn.Conv1d(1, out_channels, kernel_size, padding=padding)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, padding=padding)
        self.bn1   = nn.BatchNorm1d(out_channels)
        self.bn2   = nn.BatchNorm1d(out_channels)
        self.proj  = nn.Linear(n_features * out_channels, n_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (Batch, SeqLen, n_features)
        Returns:
            out: (Batch, SeqLen, n_features)  — same shape
        """
        B, T, n_f = x.shape
        # Apply CNN on each time step independently
        x_flat = x.reshape(B * T, 1, n_f)                    # (B*T, 1, n_f)
        h = F.relu(self.bn1(self.conv1(x_flat)))              # (B*T, C, n_f)
        h = F.relu(self.bn2(self.conv2(h)))                   # (B*T, C, n_f)
        h = h.reshape(B * T, -1)                              # (B*T, C*n_f)
        out = self.proj(h).reshape(B, T, n_f)                 # (B, T, n_f)
        return out


class AQIModel(nn.Module):
    """
    Full CNN-LSTM + Attention regressor for surface AQI estimation.

    Args:
        n_features   : number of input features per time step (default 18)
        seq_len      : temporal window length (default 4)
        cnn_channels : number of CNN filters (default 32)
        lstm_hidden  : LSTM hidden state size (default 128)
        lstm_layers  : number of stacked LSTM layers (default 2)
        dropout      : dropout rate (default 0.3)
    """

    def __init__(
        self,
        n_features:   int = 18,
        seq_len:      int = 4,
        cnn_channels: int = 32,
        lstm_hidden:  int = 128,
        lstm_layers:  int = 2,
        dropout:      float = 0.3,
    ):
        super().__init__()
        self.n_features  = n_features
        self.seq_len     = seq_len
        self.lstm_hidden = lstm_hidden

        # 1. CNN Block — feature interaction
        self.cnn = CNNBlock(n_features, cnn_channels)

        # 2. LSTM Block — temporal persistence
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0,
            bidirectional=False,
        )

        # 3. Self-Attention — lag weighting
        self.attention = TemporalAttention(lstm_hidden)

        # 4. Dense Regressor
        self.regressor = nn.Sequential(
            nn.Linear(lstm_hidden, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),          # scalar AQI prediction
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (Batch, SeqLen, n_features)
        Returns:
            aqi_pred: (Batch,)  — continuous AQI estimate
        """
        # 1. CNN feature extraction
        x = self.cnn(x)                        # (B, T, F)

        # 2. LSTM temporal modelling
        lstm_out, _ = self.lstm(x)             # (B, T, H)

        # 3. Attention pooling
        context = self.attention(lstm_out)     # (B, H)

        # 4. Regression
        out = self.regressor(context)          # (B, 1)
        return out.squeeze(-1)                 # (B,)


def build_model(n_features: int = 18, **kwargs) -> AQIModel:
    """Factory function — build model with project defaults."""
    return AQIModel(n_features=n_features, **kwargs)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Smoke test
    model = build_model(n_features=18)
    print(f"AQIModel architecture:\n{model}")
    print(f"\nTotal trainable parameters: {count_parameters(model):,}")

    # Forward pass test
    dummy = torch.randn(32, 4, 18)   # batch=32, seq=4, features=18
    out   = model(dummy)
    print(f"\nInput  shape: {dummy.shape}")
    print(f"Output shape: {out.shape}    (should be [32])")
    print(f"Output range: [{out.min():.2f}, {out.max():.2f}]")
