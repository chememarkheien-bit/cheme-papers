#!/usr/bin/env python3
"""
ChemE 498 – Problem Set #8
DFN Model Analysis of Mohtat2020 Graphite/LiPF6/NMC Pouch Cell
"""
import pybamm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT_DIR = "/home/claude/ps8_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

C_RATES = [0.5, 1, 2, 4, 8]
COLORS = {0.5: 'blue', 1: 'green', 2: 'orange', 4: 'red', 8: 'purple'}

def run_simulation(parameter_mods=None, c_rates=C_RATES, label="default", var_pts=None):
    """Run DFN simulations at multiple C-rates. Returns dict of solutions keyed by C-rate."""
    if var_pts is None:
        var_pts = {
            "x_n": 30, "x_s": 10, "x_p": 30,
            "r_n": 10, "r_p": 10,
        }
    
    solutions = {}
    for c_rate in c_rates:
        print(f"  Running {label} at {c_rate}C...")
        # Mohtat2020 cell starts discharged. Charge first, then discharge at target C-rate.
        experiment = pybamm.Experiment([
            (
                "Charge at 1C until 4.2 V",
                "Hold at 4.2 V until 10 mA",
                f"Discharge at {c_rate}C until 3.3 V",
            )
        ])
        
        parameter_values = pybamm.ParameterValues("Mohtat2020")
        if parameter_mods:
            for key, val in parameter_mods.items():
                parameter_values[key] = val
        
        model = pybamm.lithium_ion.DFN()
        sim = pybamm.Simulation(
            model, experiment=experiment,
            parameter_values=parameter_values, var_pts=var_pts
        )
        try:
            sol = sim.solve()
            solutions[c_rate] = sol
        except Exception as e:
            print(f"    WARNING: {c_rate}C failed: {e}")
            solutions[c_rate] = None
    
    return solutions

def get_discharge_time_slice(sol):
    """Get time array for discharge portion of simulation."""
    t_all = sol.t
    voltage = sol["Voltage [V]"](t_all)
    capacity = sol["Discharge capacity [A.h]"](t_all)
    
    # Find where voltage is near peak (~4.2V) — end of charge
    high_v_idx = np.where(voltage > 4.1)[0]
    if len(high_v_idx) == 0:
        return t_all, capacity, voltage
    
    start_idx = high_v_idx[-1]
    t_dis = t_all[start_idx:]
    v_dis = voltage[start_idx:]
    q_dis = capacity[start_idx:] - capacity[start_idx]
    return t_dis, q_dis, v_dis


def extract_discharge(sol):
    """Extract voltage and capacity for discharge portion only."""
    t_dis, q_dis, v_dis = get_discharge_time_slice(sol)
    return q_dis, v_dis


def plot_vcell_vs_q(solutions, title, filename):
    """Plot Vcell vs Q for all C-rates on same axes."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    for c_rate in C_RATES:
        sol = solutions.get(c_rate)
        if sol is None:
            continue
        q, v = extract_discharge(sol)
        ax.plot(q, v, color=COLORS[c_rate], linewidth=2, label=f'{c_rate}C')
    
    ax.set_xlabel("Discharge Capacity [A.h]", fontsize=13)
    ax.set_ylabel("Cell Voltage [V]", fontsize=13)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim([2.8, 4.3])
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {filename}")


def plot_loss_breakdown(solutions, title, filename, c_rates_to_plot=None):
    """Plot V-Veq contributions for given solutions."""
    if c_rates_to_plot is None:
        c_rates_to_plot = [1, 4, 8]
    
    n_plots = len(c_rates_to_plot)
    fig, axes = plt.subplots(1, n_plots, figsize=(6*n_plots, 5), sharey=True)
    if n_plots == 1:
        axes = [axes]
    
    for idx, c_rate in enumerate(c_rates_to_plot):
        ax = axes[idx]
        sol = solutions.get(c_rate)
        if sol is None:
            ax.set_title(f"{c_rate}C - FAILED")
            continue
        
        t_dis, q_dis, v_dis = get_discharge_time_slice(sol)
        
        positrode = sol["X-averaged positive electrode reaction overpotential [V]"](t_dis)
        negitrode = sol["X-averaged negative electrode reaction overpotential [V]"](t_dis)
        electrolyte = sol["X-averaged electrolyte ohmic losses [V]"](t_dis)
        posiconc = sol["Positive particle concentration overpotential [V]"](t_dis)
        negiconc = sol["Negative particle concentration overpotential [V]"](t_dis)
        
        ax.plot(q_dis, positrode, color='red', linewidth=1.5, label='η+ (kinetics)')
        ax.plot(q_dis, negitrode, color='green', linewidth=1.5, label='η- (kinetics)')
        ax.plot(q_dis, electrolyte, color='black', linestyle='--', linewidth=1.5, label='Electrolyte ohmic')
        ax.plot(q_dis, posiconc, color='magenta', linewidth=1.5, label='COP+ (diffusion)')
        ax.plot(q_dis, negiconc, color='cyan', linewidth=1.5, label='COP- (diffusion)')
        
        ax.set_xlabel("Discharge Capacity [A.h]", fontsize=11)
        if idx == 0:
            ax.set_ylabel("Overpotential [V]", fontsize=11)
        ax.set_title(f"{c_rate}C", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='best')
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {filename}")


# ==========================================
# PART (a): Default parameters, multiple C-rates
# ==========================================
print("=" * 60)
print("PART (a): Default Mohtat2020 Parameters")
print("=" * 60)
sols_a = run_simulation(label="Part(a) default")
plot_vcell_vs_q(sols_a, "Part (a): Default Cell – V vs Q at Various C-rates", "part_a_vcell_vs_q.png")
plot_loss_breakdown(sols_a, "Part (a): Default Cell – Loss Breakdown", "part_a_losses.png", c_rates_to_plot=[0.5, 1, 2, 4, 8])


# ==========================================
# PART (b): 2x electrode thickness, 0.5x width
# ==========================================
print("\n" + "=" * 60)
print("PART (b): 2x Electrode Thickness, 0.5x Width")
print("=" * 60)
# Default values: pos=6.7e-5, neg=6.2e-5, width=0.205
mods_b = {
    "Positive electrode thickness [m]": 6.7e-05 * 2,
    "Negative electrode thickness [m]": 6.2e-05 * 2,
    "Electrode width [m]": 0.205 / 2,
}
sols_b = run_simulation(parameter_mods=mods_b, label="Part(b) 2x thick")
plot_vcell_vs_q(sols_b, "Part (b): 2× Thickness, 0.5× Width – V vs Q", "part_b_vcell_vs_q.png")
plot_loss_breakdown(sols_b, "Part (b): 2× Thickness – Loss Breakdown", "part_b_losses.png", c_rates_to_plot=[0.5, 1, 2, 4, 8])


# ==========================================
# PART (c): 0.5x particle radius
# ==========================================
print("\n" + "=" * 60)
print("PART (c): 0.5x Particle Radius")
print("=" * 60)
mods_c = {
    "Positive particle radius [m]": 3.5e-06 / 2,
    "Negative particle radius [m]": 2.5e-06 / 2,
}
sols_c = run_simulation(parameter_mods=mods_c, label="Part(c) 0.5x radius")
plot_vcell_vs_q(sols_c, "Part (c): 0.5× Particle Radius – V vs Q", "part_c_vcell_vs_q.png")
plot_loss_breakdown(sols_c, "Part (c): 0.5× Particle Radius – Loss Breakdown", "part_c_losses.png", c_rates_to_plot=[0.5, 1, 2, 4, 8])


# ==========================================
# PART (d): Drone Battery Optimization at 25C
# ==========================================
print("\n" + "=" * 60)
print("PART (d): 25C Drone Battery Optimization")
print("=" * 60)

# First, try the default cell at 25C
print("\n--- Default cell at 25C ---")
sols_d_default = run_simulation(c_rates=[25], label="Part(d) default@25C")

# Now optimize: reduce particle size by 10x, and find optimal electrode thickness
# With thinner electrodes, we need more area (larger width) to keep 5 Ah capacity
# Try 10x smaller particles, various electrode thickness reductions

# Strategy: thinner electrodes reduce diffusion path in electrolyte,
# smaller particles reduce solid-state diffusion limitation

# Let's systematically try different configurations
print("\n--- Optimizing for 25C: 10x smaller particles ---")

# Try different thickness scale factors
thickness_factors = [1.0, 0.5, 0.25, 0.1]
# Width must scale inversely with thickness to keep capacity constant
# Capacity ~ (electrode thickness) * (electrode area) = (thickness) * (width * height)

sols_d_opt = {}
for tf in thickness_factors:
    width_factor = 1.0 / tf  # inverse to keep capacity
    mods = {
        "Positive particle radius [m]": 3.5e-06 / 10,  # 10x smaller
        "Negative particle radius [m]": 2.5e-06 / 10,
        "Positive electrode thickness [m]": 6.7e-05 * tf,
        "Negative electrode thickness [m]": 6.2e-05 * tf,
        "Electrode width [m]": 0.205 * width_factor,
    }
    label = f"10x_small_particles_{tf}x_thick"
    print(f"\n  Config: {tf}x thickness, {width_factor}x width, 10x smaller particles")
    print(f"    Pos thickness: {6.7e-05*tf*1e6:.1f} μm, Neg thickness: {6.2e-05*tf*1e6:.1f} μm")
    print(f"    Width: {0.205*width_factor:.3f} m, Total area: {0.205*width_factor*1.0:.3f} m²")
    
    try:
        sol_dict = run_simulation(parameter_mods=mods, c_rates=[1, 4, 8, 25], label=label)
        sols_d_opt[tf] = sol_dict
    except Exception as e:
        print(f"    FAILED: {e}")

# Plot the 25C results for different thickness configs
fig, ax = plt.subplots(figsize=(10, 7))
colors_tf = {1.0: 'blue', 0.5: 'green', 0.25: 'orange', 0.1: 'red'}

for tf in thickness_factors:
    if tf not in sols_d_opt:
        continue
    sol = sols_d_opt[tf].get(25)
    if sol is None:
        continue
    q, v = extract_discharge(sol)
    width_factor = 1.0 / tf
    total_area = 0.205 * width_factor * 1.0
    ax.plot(q, v, color=colors_tf[tf], linewidth=2, 
            label=f'{tf}x thick, {total_area:.2f} m² area')

ax.set_xlabel("Discharge Capacity [A.h]", fontsize=13)
ax.set_ylabel("Cell Voltage [V]", fontsize=13)
ax.set_title("Part (d): 25C Discharge – 10× Smaller Particles, Various Thicknesses", 
             fontsize=13, fontweight='bold')
ax.set_ylim([2.5, 4.3])
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "part_d_25C_optimization.png"), dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved part_d_25C_optimization.png")

# Also plot the best config at multiple C-rates
# Find the best thickness factor (one that delivers most capacity at 25C)
best_tf = None
best_cap = 0
for tf in thickness_factors:
    if tf in sols_d_opt and sols_d_opt[tf].get(25) is not None:
        q, v = extract_discharge(sols_d_opt[tf][25])
        delivered = q[-1] if len(q) > 0 else 0
        print(f"  {tf}x thick @ 25C delivers {delivered:.2f} Ah")
        if delivered > best_cap:
            best_cap = delivered
            best_tf = tf

if best_tf is not None:
    print(f"\n  Best config: {best_tf}x thickness, delivers {best_cap:.2f} Ah at 25C")
    width_opt = 0.205 / best_tf
    area_opt = width_opt * 1.0
    print(f"  Optimal width: {width_opt:.3f} m")
    print(f"  Total cell area: {area_opt:.3f} m²")
    
    # Plot the best config across all C-rates
    fig, ax = plt.subplots(figsize=(10, 7))
    all_rates = [1, 4, 8, 25]
    rate_colors = {1: 'blue', 4: 'green', 8: 'orange', 25: 'red'}
    for cr in all_rates:
        sol = sols_d_opt[best_tf].get(cr)
        if sol is None:
            continue
        q, v = extract_discharge(sol)
        ax.plot(q, v, color=rate_colors[cr], linewidth=2, label=f'{cr}C')
    
    ax.set_xlabel("Discharge Capacity [A.h]", fontsize=13)
    ax.set_ylabel("Cell Voltage [V]", fontsize=13)
    ax.set_title(f"Part (d): Optimized Drone Cell ({best_tf}x thick, 10x smaller particles)", 
                 fontsize=13, fontweight='bold')
    ax.set_ylim([2.5, 4.3])
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "part_d_best_config.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("  Saved part_d_best_config.png")
    
    # Loss breakdown for best config
    plot_loss_breakdown(sols_d_opt[best_tf], 
                       f"Part (d): Optimized Cell – Loss Breakdown",
                       "part_d_best_losses.png", 
                       c_rates_to_plot=[1, 8, 25])

print("\n" + "=" * 60)
print("ALL SIMULATIONS COMPLETE")
print("=" * 60)
