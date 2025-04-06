import argparse
import numpy as np
from matplotlib import pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(description="Plot losses from log")
    parser.add_argument("--log-file", help="Path to log file", required=True)
    parser.add_argument("--fake-weight", help="Weight for fake loss", default=1.4, type=float)
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        with open(args.log_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {args.log_file} does not exist.")
        return

    # Extract real and fake losses
    real_losses = np.array([float(line.split(" ")[-1]) for line in lines if line.startswith("real_loss")])
    fake_losses = np.array([float(line.split(" ")[-1]) for line in lines if line.startswith("fake_loss")])

    # Calculate weighted loss
    loss = (fake_losses * args.fake_weight + real_losses) / 2

    plt.title(f"Weighted loss ({args.fake_weight}*fake_loss + real_loss)/2)")
    best_loss_idx = np.argsort(loss)[:5]
    # Ignore early epochs; loss is noisy and there could be spikes
    best_loss_idx = best_loss_idx[best_loss_idx > 16]
    
    plt.scatter(best_loss_idx, loss[best_loss_idx], c="red")
    for idx in best_loss_idx:
        plt.annotate(str(idx), (idx, loss[idx]))
    
    plt.plot(loss, label='Weighted Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    main()
