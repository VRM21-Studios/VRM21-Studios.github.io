import sys

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


# ======================================================================
# RIGID N-PENDULUM KINEMATICS (LAGRANGIAN + RK4)
# ======================================================================
class RealNPendulum:
    def __init__(self, m, L, theta, omega, dt, G):
        self.n = len(m)
        self.m = np.array(m, dtype=float)
        self.L = np.array(L, dtype=float)
        self.theta = np.array(theta, dtype=float)
        self.omega = np.array(omega, dtype=float)
        self.dt = dt
        self.G = G  # Gravitational acceleration is configurable from the GUI.

    def derivatives(self, state):
        theta = state[:self.n]
        omega = state[self.n:]

        M = np.zeros((self.n, self.n))
        C = np.zeros(self.n)

        # Construct the mass matrix (M) and force vector (C).
        for i in range(self.n):
            for j in range(self.n):
                mass_sum = np.sum(self.m[max(i, j):])
                M[i, j] = (
                    mass_sum
                    * self.L[i]
                    * self.L[j]
                    * np.cos(theta[i] - theta[j])
                )

            c_val = 0
            for j in range(self.n):
                mass_sum = np.sum(self.m[max(i, j):])
                c_val -= (
                    mass_sum
                    * self.L[i]
                    * self.L[j]
                    * (omega[j] ** 2)
                    * np.sin(theta[i] - theta[j])
                )

            mass_sum_i = np.sum(self.m[i:])
            c_val -= (
                mass_sum_i
                * self.G
                * self.L[i]
                * np.sin(theta[i])
            )
            C[i] = c_val

            # Add a small diagonal regularization term to reduce
            # the risk of a singular dynamic mass matrix.
            M += np.eye(self.n) * 1e-6

        try:
            # Use a standard linear solver for the dynamic system.
            alpha = scipy.linalg.solve(M, C)
        except scipy.linalg.LinAlgError:
            # Fallback if the system becomes singular.
            alpha = np.zeros(self.n)

        return np.concatenate((omega, alpha))

    def step_rk4(self):
        state = np.concatenate((self.theta, self.omega))

        k1 = self.dt * self.derivatives(state)
        k2 = self.dt * self.derivatives(state + 0.5 * k1)
        k3 = self.dt * self.derivatives(state + 0.5 * k2)
        k4 = self.dt * self.derivatives(state + k3)

        state_next = state + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0

        self.theta = state_next[:self.n]
        self.omega = state_next[self.n:]

    def positions(self):
        x = np.zeros(self.n + 1)
        y = np.zeros(self.n + 1)

        for i in range(self.n):
            x[i + 1] = x[i] + self.L[i] * np.sin(self.theta[i])
            y[i + 1] = y[i] - self.L[i] * np.cos(self.theta[i])

        return x, y


# ======================================================================
# APPLICATION GUI
# ======================================================================
class PendulumApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lagrangian N-Pendulum Dynamics (RK4 Engine)")
        self.resize(1300, 750)

        # Matplotlib canvas.
        plt.style.use("dark_background")
        self.canvas = FigureCanvas(Figure(figsize=(6, 6)))
        self.ax = self.canvas.figure.add_subplot(111)
        self.ax.set_aspect("equal")
        self.canvas.figure.tight_layout()

        self.lines, = self.ax.plot(
            [],
            [],
            "o-",
            color="#00ffcc",
            lw=2,
            markersize=6,
        )

        self.traces = []
        self.trace_data_x = []
        self.trace_data_y = []

        # ==================================================================
        # GLOBAL PARAMETERS
        # ==================================================================
        left_layout = QVBoxLayout()

        global_group = QGroupBox("Global Parameters")
        global_layout = QFormLayout()

        self.g_input = QDoubleSpinBox()
        self.g_input.setRange(-50.0, 50.0)
        self.g_input.setValue(9.81)
        self.g_input.setSingleStep(1.0)

        self.dt_input = QDoubleSpinBox()
        self.dt_input.setRange(0.001, 0.1)
        self.dt_input.setDecimals(4)
        self.dt_input.setValue(0.0160)
        self.dt_input.setSingleStep(0.001)

        self.substep_input = QSpinBox()
        self.substep_input.setRange(1, 20)
        self.substep_input.setValue(2)

        self.trace_input = QSpinBox()
        self.trace_input.setRange(10, 5000)
        self.trace_input.setValue(200)
        self.trace_input.setSingleStep(50)

        global_layout.addRow("Gravity (G):", self.g_input)
        global_layout.addRow("Time Step (dt):", self.dt_input)
        global_layout.addRow("RK4 Sub-steps:", self.substep_input)
        global_layout.addRow("Trace Length:", self.trace_input)

        global_group.setLayout(global_layout)
        left_layout.addWidget(global_group)

        # ==================================================================
        # N-PENDULUM CONFIGURATION
        # ==================================================================
        top_ctrl_layout = QHBoxLayout()

        top_ctrl_layout.addWidget(QLabel("Number of Joints (N):"))

        self.n_input = QSpinBox()
        self.n_input.setRange(1, 8)
        self.n_input.setValue(4)
        self.n_input.valueChanged.connect(self.build_table)

        top_ctrl_layout.addWidget(self.n_input)
        left_layout.addLayout(top_ctrl_layout)

        # ==================================================================
        # INDEPENDENT PENDULUM PARAMETERS
        # ==================================================================
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "Mass (kg)",
                "Length (m)",
                "Theta (rad)",
                "Omega (rad/s)",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        left_layout.addWidget(self.table)

        # ==================================================================
        # CONTROL BUTTONS
        # ==================================================================
        btn_layout = QHBoxLayout()

        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Apply Parameters & Reset")

        self.play_btn.clicked.connect(self.play)
        self.pause_btn.clicked.connect(self.pause)
        self.reset_btn.clicked.connect(self.reset_sim)

        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.reset_btn)

        left_layout.addLayout(btn_layout)

        # ==================================================================
        # MAIN LAYOUT
        # ==================================================================
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(self.canvas, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # ==================================================================
        # SIMULATION STATE
        # ==================================================================
        self.running = False
        self.sim = None
        self.trace_length = 200
        self.sub_steps = 2

        self.build_table()
        self.reset_sim()

        # Update loop: approximately 60 FPS.
        self.ani = FuncAnimation(
            self.canvas.figure,
            self.update_frame,
            interval=16,
            blit=False,
        )

    def build_table(self):
        n = self.n_input.value()
        current_rows = self.table.rowCount()

        self.table.setRowCount(n)

        for i in range(n):
            if i >= current_rows:
                self.table.setItem(
                    i,
                    0,
                    QTableWidgetItem("1.0"),
                )
                self.table.setItem(
                    i,
                    1,
                    QTableWidgetItem("1.0"),
                )
                self.table.setItem(
                    i,
                    2,
                    QTableWidgetItem(
                        str(round(np.pi / 2 + (i * 0.1), 3))
                    ),
                )
                self.table.setItem(
                    i,
                    3,
                    QTableWidgetItem("0.0"),
                )

    def read_parameters(self):
        n = self.n_input.value()

        masses = []
        lengths = []
        theta = []
        omega = []

        for i in range(n):
            try:
                masses.append(float(self.table.item(i, 0).text()))
                lengths.append(float(self.table.item(i, 1).text()))
                theta.append(float(self.table.item(i, 2).text()))
                omega.append(float(self.table.item(i, 3).text()))
            except (ValueError, AttributeError):
                masses.append(1.0)
                lengths.append(1.0)
                theta.append(np.pi / 2)
                omega.append(0.0)

        return masses, lengths, theta, omega

    def reset_sim(self):
        self.running = False

        # Read simulation parameters from the GUI.
        masses, lengths, theta, omega = self.read_parameters()
        dt = self.dt_input.value()
        gravity = self.g_input.value()

        self.trace_length = self.trace_input.value()
        self.sub_steps = self.substep_input.value()

        # Initialize the physics engine.
        self.sim = RealNPendulum(
            masses,
            lengths,
            theta,
            omega,
            dt,
            gravity,
        )

        # Clear existing trace data.
        for trace in self.traces:
            trace.remove()

        self.traces = []
        self.trace_data_x = [[] for _ in range(self.sim.n)]
        self.trace_data_y = [[] for _ in range(self.sim.n)]

        # Create a trace line for each joint.
        colors = plt.cm.jet(
            np.linspace(0.3, 1, self.sim.n)
        )

        for i in range(self.sim.n):
            trace, = self.ax.plot(
                [],
                [],
                "-",
                color=colors[i],
                lw=1,
                alpha=0.6,
            )
            self.traces.append(trace)

        # Calculate dynamic plot boundaries.
        max_reach = sum(lengths) * 1.1
        self.ax.set_xlim(-max_reach, max_reach)
        self.ax.set_ylim(-max_reach, max_reach)

        self.draw_initial()

    def draw_initial(self):
        x, y = self.sim.positions()

        self.lines.set_data(x, y)
        self.canvas.draw()

    def play(self):
        self.running = True

    def pause(self):
        self.running = False

    def update_frame(self, frame):
        if not self.running or self.sim is None:
            return self.lines, *self.traces

        # Apply the configured number of RK4 sub-steps.
        for _ in range(self.sub_steps):
            self.sim.step_rk4()

        x, y = self.sim.positions()
        self.lines.set_data(x, y)

        for i in range(self.sim.n):
            self.trace_data_x[i].append(x[i + 1])
            self.trace_data_y[i].append(y[i + 1])

            if len(self.trace_data_x[i]) > self.trace_length:
                self.trace_data_x[i].pop(0)
                self.trace_data_y[i].pop(0)

            self.traces[i].set_data(
                self.trace_data_x[i],
                self.trace_data_y[i],
            )

        return self.lines, *self.traces


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PendulumApp()
    window.show()
    sys.exit(app.exec())
