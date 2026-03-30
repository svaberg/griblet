"""BATSRUS-style example graph with placeholder NumPy field data."""

import numpy as np

from griblet import Graph
from griblet.loader import BlockLoader

_fallback_gamma = 5/3
_mu_0 = 4e-7 * np.pi
_proton_mass = 1.67262192369e-27
_boltzmann = 1.380649e-23


class WindLoader(BlockLoader):
    """
    Placeholder BATSRUS block loader with in-memory NumPy field data.

    This stands in for a real BATSRUS file reader. The values are synthetic,
    but the block-loading behavior is real: the first field request loads the
    whole block, after which cached paths become available for every source
    field in the block.
    """

    DEFAULT_COST = 10.0
    DEFAULT_CACHED_COST = 0.05

    def __init__(self, n=10):
        rng = np.random.default_rng(0)

        X_R = rng.normal(size=n)
        Y_R = rng.normal(size=n)
        Z_R = rng.normal(size=n)

        Bx = rng.normal(size=n)
        By = rng.normal(size=n)
        Bz = rng.normal(size=n)

        Ux = rng.normal(size=n)
        Uy = rng.normal(size=n)
        Uz = rng.normal(size=n)

        P   = np.abs(rng.normal(size=n)) + 1.0
        rho = np.abs(rng.normal(size=n)) + 1.0

        super().__init__({
            "X (R)": X_R,
            "Y (R)": Y_R,
            "Z (R)": Z_R,
            "B_x (T)": Bx,
            "B_y (T)": By,
            "B_z (T)": Bz,
            "U_x (m/s)": Ux,
            "U_y (m/s)": Uy,
            "U_z (m/s)": Uz,
            "P (Pa)": P,
            "Rho (kg/m^3)": rho,
            "Star_radius_m": 1.0,   # scalar
            "GAMMA": 1.4,           # scalar
        })

    def _metadata(self, field):
        """Mark BATSRUS source fields as disk-backed."""
        if field not in self._fields:
            raise ValueError(f"Field '{field}' not found.")
        return {"kind": "disk"}


def make_wind_graph():
    """Build the derived BATSRUS-style graph without source fields attached."""
    graph = Graph()

    # In this example, each formula costs one unit per dependency it needs.

    # Star radius coordinates
    def X_m(X_R, Star_radius_m): return Star_radius_m * X_R
    graph.add("X (m)", X_m, needs=("X (R)", "Star_radius_m"), cost=2.0)

    def Y_m(Y_R, Star_radius_m): return Star_radius_m * Y_R
    graph.add("Y (m)", Y_m, needs=("Y (R)", "Star_radius_m"), cost=2.0)

    def Z_m(Z_R, Star_radius_m): return Star_radius_m * Z_R
    graph.add("Z (m)", Z_m, needs=("Z (R)", "Star_radius_m"), cost=2.0)

    def R_R(X_R, Y_R, Z_R): return np.sqrt(X_R**2 + Y_R**2 + Z_R**2)
    graph.add("R (R)", R_R, needs=("X (R)", "Y (R)", "Z (R)"), cost=3.0)

    def H_R(R_R): return R_R - 1.0
    graph.add("H (R)", H_R, needs=("R (R)",), cost=1.0)

    def R_m(X_m, Y_m, Z_m): return np.sqrt(X_m**2 + Y_m**2 + Z_m**2)
    graph.add("R (m)", R_m, needs=("X (m)", "Y (m)", "Z (m)"), cost=3.0)

    # Vector absolute values
    def U(Ux, Uy, Uz): return np.sqrt(Ux**2 + Uy**2 + Uz**2)
    graph.add("U (m/s)", U, needs=("U_x (m/s)", "U_y (m/s)", "U_z (m/s)"), cost=3.0)

    def B(Bx, By, Bz): return np.sqrt(Bx**2 + By**2 + Bz**2)
    graph.add("B (T)", B, needs=("B_x (T)", "B_y (T)", "B_z (T)"), cost=3.0)

    # Radial values
    def B_r(Bx, By, Bz, X_R, Y_R, Z_R, R_R):
        denom = np.where(R_R == 0, np.nan, R_R)
        return (Bx*X_R + By*Y_R + Bz*Z_R) / denom
    graph.add(
        "B_r (T)", B_r,
        needs=("B_x (T)", "B_y (T)", "B_z (T)", "X (R)", "Y (R)", "Z (R)", "R (R)"),
        cost=7.0
    )

    def U_r(Ux, Uy, Uz, X_R, Y_R, Z_R, R_R):
        denom = np.where(R_R == 0, np.nan, R_R)
        return (Ux*X_R + Uy*Y_R + Uz*Z_R) / denom
    graph.add(
        "U_r (m/s)", U_r,
        needs=("U_x (m/s)", "U_y (m/s)", "U_z (m/s)", "X (R)", "Y (R)", "Z (R)", "R (R)"),
        cost=7.0
    )

    # Other stuff
    def c_s_fallback(P, rho): return np.sqrt(_fallback_gamma * P / rho)
    graph.add("c_s (m/s)", c_s_fallback, needs=("P (Pa)", "Rho (kg/m^3)"), cost=2.0)

    def c_s_gamma(P, rho, GAMMA): return np.sqrt(GAMMA * P / rho)
    graph.add("c_s (m/s)", c_s_gamma, needs=("P (Pa)", "Rho (kg/m^3)", "GAMMA"), cost=3.0)

    def c_A(B, rho): return B / np.sqrt(_mu_0 * rho)
    graph.add("c_A (m/s)", c_A, needs=("B (T)", "Rho (kg/m^3)"), cost=2.0)

    def c_A_r(B_r, rho): return np.abs(B_r) / np.sqrt(_mu_0 * rho)
    graph.add("c_A_r (m/s)", c_A_r, needs=("B_r (T)", "Rho (kg/m^3)"), cost=2.0)

    def P_b(B): return B**2 / (2.0 * _mu_0)
    graph.add("P_b (Pa)", P_b, needs=("B (T)",), cost=1.0)

    def Ma(U, c_s): return U / c_s
    graph.add("Ma (U/c_s)", Ma, needs=("U (m/s)", "c_s (m/s)"), cost=2.0)

    def MA(U, c_A): return U / c_A
    graph.add("MA (U/c_A)", MA, needs=("U (m/s)", "c_A (m/s)"), cost=2.0)

    def MA_r(U_r, c_A_r): return np.abs(U_r) / c_A_r
    graph.add("MA (U_r/c_A_r)", MA_r, needs=("U_r (m/s)", "c_A_r (m/s)"), cost=2.0)

    def beta(P, P_b): return P / P_b
    graph.add("beta (P/P_b)", beta, needs=("P (Pa)", "P_b (Pa)"), cost=2.0)

    def R2rho(R_m, rho): return (R_m**2) * rho
    graph.add("R^2 Rho (kg/m)", R2rho, needs=("R (m)", "Rho (kg/m^3)"), cost=2.0)

    def Ne(rho): return rho / _proton_mass
    graph.add("Ne (1/m^3)", Ne, needs=("Rho (kg/m^3)",), cost=1.0)

    def T_ideal(P, Ne): return P / (2.0 * Ne * _boltzmann)
    graph.add("T ideal (K)", T_ideal, needs=("P (Pa)", "Ne (1/m^3)"), cost=2.0)

    return graph


def build_wind_graph():
    """
    Build the full BATSRUS-style example on the loader's live graph.

    A BlockLoader owns a cache-backed graph that changes as fields are loaded,
    so the derived paths are merged onto that live graph rather than onto a
    separate copy.
    """
    graph = WindLoader().as_graph()
    graph.merge(make_wind_graph())
    return graph


if __name__ == "__main__":
    loader = WindLoader()
    print("\n=== Loader ===\n")
    print(loader)

    loader_graph = loader.as_graph()
    print("\n=== Loader Graph ===\n")
    print(loader_graph)

    derived_graph = make_wind_graph()
    print("\n=== Derived Graph ===\n")
    print(derived_graph)

    graph = loader_graph
    graph.merge(derived_graph)

    cold_path = graph.path("Ma (U/c_s)")
    print("\n=== Cold Best Path to Ma (U/c_s) ===\n")
    print(cold_path)

    temperature = graph.compute("T ideal (K)")
    mach = graph.compute("Ma (U/c_s)")
    warm_path = graph.path("Ma (U/c_s)")

    print("\n=== After One Block Load ===\n")
    print(f"cost before: {round(cold_path.cost, 12)}")
    print(f"cost after: {round(warm_path.cost, 12)}\n")
    print(warm_path)

    print("\n=== Computed Values ===\n")
    print("T ideal (K) shape:", temperature.shape)
    print("T ideal (K) first three values:")
    print(np.array2string(temperature[:3], precision=4, floatmode="maxprec_equal"))
    print("\nMa (U/c_s) first three values:")
    print(np.array2string(mach[:3], precision=4, floatmode="maxprec_equal"))

    path_before = warm_path
    # Demo trick: the cheaper two-input c_s path was added first in
    # make_wind_graph(), so popping the first entry forces a reroute through
    # the three-input GAMMA formula.
    graph.paths["c_s (m/s)"].pop(0)
    rerouted_path = graph.path("Ma (U/c_s)")
    rerouted_mach = graph.compute("Ma (U/c_s)")

    print("\n=== After Removing the Cheaper c_s Path ===\n")
    print(f"cost before: {round(path_before.cost, 12)}")
    print(f"cost after: {round(rerouted_path.cost, 12)}\n")
    print(rerouted_path)
    print("\nrerouted Ma (U/c_s) first three values:")
    print(np.array2string(rerouted_mach[:3], precision=4, floatmode="maxprec_equal"))
