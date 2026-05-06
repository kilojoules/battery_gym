#!/bin/bash
#BSUB -J battery_phase2_ppo
#BSUB -q hpc
#BSUB -n 8
#BSUB -R "rusage[mem=4GB]"
#BSUB -R "span[hosts=1]"
#BSUB -W 4:00
#BSUB -o phase2_ppo_%J.out
#BSUB -e phase2_ppo_%J.err

# GBAR submission for phase 2 PPO training. CPU-only; PPO on small env is fast.
#
# Usage:
#   # On gbar:  cd ~/battery_gym && bsub < gbar_phase2_ppo.sh
#
# Requires:
#   pixi env (auto-built from pixi.toml on first run)
#   stable-baselines3, gymnasium, torch  (added via pip install in run)

set -e
echo "[gbar] starting phase2 PPO at $(date)"
echo "[gbar] hostname: $(hostname)"
echo "[gbar] cwd:      $(pwd)"
echo "[gbar] cores:    $LSB_DJOB_NUMPROC"

# Pixi env -- assumes pixi installed in user's home
export PATH="$HOME/.pixi/bin:$PATH"

# Build / use pixi env. cvxpy + sb3 needed; install via pip into pixi env.
pixi install
pixi run python -m pip install --quiet stable-baselines3 gymnasium

# Run with multi-env vectorization (n_envs=4 -> 4 parallel CPU envs)
pixi run python phase2_ppo.py \
    --total_timesteps 1000000 \
    --n_envs 4 \
    --T 168 \
    --lookahead 72 \
    --noise_train 8.0 \
    --alpha 0.005 \
    --b_E 2.0 \
    --b_P 2.0 \
    --seed 42 \
    --save ppo_policy.zip \
    --log_dir ppo_logs \
    --n_eval 50

echo "[gbar] phase2 PPO done at $(date)"
