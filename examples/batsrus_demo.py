import numpy as np
import pytest
import scipy.constants

from griblet import ComputationGraph
from griblet import BaseLoader

_fallback_gamma = 5/3


class WindLoader(BaseLoader):
    """
    Test loader, like the RoomLoader demo: primitives only, plain numpy.
    Values here are placeholders just to make the graph runnable.
    """
    def __init__(self, n=10):
        super().__init__()
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

        self._fields = {
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
        }


def make_wind_recipes_graph():
    cg = ComputationGraph()

    # Star radius coordinates
    def X_m(X_R, Star_radius_m): return Star_radius_m * X_R
    cg.add_recipe("X (m)", X_m, deps=["X (R)", "Star_radius_m"], cost=1.0)

    def Y_m(Y_R, Star_radius_m): return Star_radius_m * Y_R
    cg.add_recipe("Y (m)", Y_m, deps=["Y (R)", "Star_radius_m"], cost=1.0)

    def Z_m(Z_R, Star_radius_m): return Star_radius_m * Z_R
    cg.add_recipe("Z (m)", Z_m, deps=["Z (R)", "Star_radius_m"], cost=1.0)

    def R_R(X_R, Y_R, Z_R): return np.sqrt(X_R**2 + Y_R**2 + Z_R**2)
    cg.add_recipe("R (R)", R_R, deps=["X (R)", "Y (R)", "Z (R)"], cost=1.0)

    def H_R(R_R): return R_R - 1.0
    cg.add_recipe("H (R)", H_R, deps=["R (R)"], cost=0.2)

    def R_m(X_m, Y_m, Z_m): return np.sqrt(X_m**2 + Y_m**2 + Z_m**2)
    cg.add_recipe("R (m)", R_m, deps=["X (m)", "Y (m)", "Z (m)"], cost=1.0)

    # Vector absolute values
    def U(Ux, Uy, Uz): return np.sqrt(Ux**2 + Uy**2 + Uz**2)
    cg.add_recipe("U (m/s)", U, deps=["U_x (m/s)", "U_y (m/s)", "U_z (m/s)"], cost=1.0)

    def B(Bx, By, Bz): return np.sqrt(Bx**2 + By**2 + Bz**2)
    cg.add_recipe("B (T)", B, deps=["B_x (T)", "B_y (T)", "B_z (T)"], cost=1.0)

    # Radial values
    def B_r(Bx, By, Bz, X_R, Y_R, Z_R, R_R):
        denom = np.where(R_R == 0, np.nan, R_R)
        return (Bx*X_R + By*Y_R + Bz*Z_R) / denom
    cg.add_recipe(
        "B_r (T)", B_r,
        deps=["B_x (T)", "B_y (T)", "B_z (T)", "X (R)", "Y (R)", "Z (R)", "R (R)"],
        cost=2.0
    )

    def U_r(Ux, Uy, Uz, X_R, Y_R, Z_R, R_R):
        denom = np.where(R_R == 0, np.nan, R_R)
        return (Ux*X_R + Uy*Y_R + Uz*Z_R) / denom
    cg.add_recipe(
        "U_r (m/s)", U_r,
        deps=["U_x (m/s)", "U_y (m/s)", "U_z (m/s)", "X (R)", "Y (R)", "Z (R)", "R (R)"],
        cost=2.0
    )

    # Other stuff
    def c_s_fallback(P, rho): return np.sqrt(_fallback_gamma * P / rho)
    cg.add_recipe("c_s (m/s)", c_s_fallback, deps=["P (Pa)", "Rho (kg/m^3)"], cost=1.0)

    def c_s_gamma(P, rho, GAMMA): return np.sqrt(GAMMA * P / rho)
    cg.add_recipe("c_s (m/s)", c_s_gamma, deps=["P (Pa)", "Rho (kg/m^3)", "GAMMA"], cost=1.0)

    def c_A(B, rho): return B / np.sqrt(scipy.constants.mu_0 * rho)
    cg.add_recipe("c_A (m/s)", c_A, deps=["B (T)", "Rho (kg/m^3)"], cost=1.0)

    def c_A_r(B_r, rho): return np.abs(B_r) / np.sqrt(scipy.constants.mu_0 * rho)
    cg.add_recipe("c_A_r (m/s)", c_A_r, deps=["B_r (T)", "Rho (kg/m^3)"], cost=1.0)

    def P_b(B): return B**2 / (2.0 * scipy.constants.mu_0)
    cg.add_recipe("P_b (Pa)", P_b, deps=["B (T)"], cost=0.5)

    def Ma(U, c_s): return U / c_s
    cg.add_recipe("Ma (U/c_s)", Ma, deps=["U (m/s)", "c_s (m/s)"], cost=0.3)

    def MA(U, c_A): return U / c_A
    cg.add_recipe("MA (U/c_A)", MA, deps=["U (m/s)", "c_A (m/s)"], cost=0.3)

    def MA_r(U_r, c_A_r): return np.abs(U_r) / c_A_r
    cg.add_recipe("MA (U_r/c_A_r)", MA_r, deps=["U_r (m/s)", "c_A_r (m/s)"], cost=0.3)

    def beta(P, P_b): return P / P_b
    cg.add_recipe("beta (P/P_b)", beta, deps=["P (Pa)", "P_b (Pa)"], cost=0.3)

    def R2rho(R_m, rho): return (R_m**2) * rho
    cg.add_recipe("R^2 Rho (kg/m)", R2rho, deps=["R (m)", "Rho (kg/m^3)"], cost=0.5)

    def Ne(rho): return rho / scipy.constants.proton_mass
    cg.add_recipe("Ne (1/m^3)", Ne, deps=["Rho (kg/m^3)"], cost=0.3)

    def T_ideal(P, Ne): return P / (2.0 * Ne * scipy.constants.Boltzmann)
    cg.add_recipe("T ideal (K)", T_ideal, deps=["P (Pa)", "Ne (1/m^3)"], cost=0.7)

    return cg


def test_batsrus_example_flow_resolves_and_evaluates():
    graph = ComputationGraph(WindLoader().as_graph())
    graph.merge(make_wind_recipes_graph())

    cost, _tree = graph.plan("T ideal (K)")
    value = graph.compute("T ideal (K)")

    assert cost > 0
    assert value.shape == (10,)
    assert np.all(np.isfinite(value))
