import torch
import torch.nn as nn
import torch.nn.functional as F


class TemporalAttention(nn.Module):
    """Learns which lag step (t, t-1, t-2, t-3) matters most for prediction."""
    def __init__(self, hidden_size):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, lstm_out):
        # score each time step, softmax across T, then weighted sum
        scores = self.attn(lstm_out).squeeze(-1)           # (B, T)
        weights = F.softmax(scores, dim=1)                 # (B, T)
        return torch.bmm(weights.unsqueeze(1), lstm_out).squeeze(1)  # (B, H)


class CNNBlock(nn.Module):
    """
    1D conv applied per time step across the feature dimension.
    Captures interactions like NO2 * wind_speed without mixing time steps.
    """
    def __init__(self, n_features, out_channels, kernel_size=3):
        super().__init__()
        p = kernel_size // 2
        self.conv1 = nn.Conv1d(1, out_channels, kernel_size, padding=p)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, padding=p)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.bn2 = nn.BatchNorm1d(out_channels)
        # project back to original feature size so LSTM input stays consistent
        self.proj = nn.Linear(n_features * out_channels, n_features)

    def forward(self, x):
        B, T, n_f = x.shape
        h = x.reshape(B * T, 1, n_f)           # treat each timestep independently
        h = F.relu(self.bn1(self.conv1(h)))
        h = F.relu(self.bn2(self.conv2(h)))
        h = self.proj(h.reshape(B * T, -1))
        return h.reshape(B, T, n_f)


class AQIModel(nn.Module):
    """
    CNN → LSTM → Attention → Dense regressor for surface AQI estimation.
    Input: (batch, seq_len=4, n_features=18), Output: (batch,) continuous AQI
    """
    def __init__(self, n_features=18, seq_len=4, cnn_channels=32,
                 lstm_hidden=128, lstm_layers=2, dropout=0.3):
        super().__init__()
        self.cnn = CNNBlock(n_features, cnn_channels)
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0  # dropout only between layers
        )
        self.attention = TemporalAttention(lstm_hidden)
        self.head = nn.Sequential(
            nn.Linear(lstm_hidden, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        x = self.cnn(x)                    # feature interaction
        lstm_out, _ = self.lstm(x)         # temporal persistence
        ctx = self.attention(lstm_out)     # focus on most relevant lag
        return self.head(ctx).squeeze(-1)


def build_model(n_features=18, **kwargs):
    return AQIModel(n_features=n_features, **kwargs)


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    model = build_model()
    print(f"Parameters: {count_parameters(model):,}")
    x = torch.randn(32, 4, 18)
    out = model(x)
    print(f"Input: {x.shape} -> Output: {out.shape}")
